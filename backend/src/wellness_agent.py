# backend/src/wellness_agent.py
import logging
from dotenv import load_dotenv
import os
import json
import asyncio
from datetime import datetime

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    metrics,
    MetricsCollectedEvent,
    function_tool,
)
from livekit.plugins import silero, google, deepgram

logger = logging.getLogger("wellness-agent")
logging.basicConfig(level=logging.INFO)

# ---------------------------------------
# LOAD ENV
# ---------------------------------------
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE, ".env.local")
load_dotenv(ENV_PATH)

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Path for wellness log
WELLNESS_LOG_FILE = "wellness_log.json"

# Global room reference for broadcasting
current_room = None

# ---------------------------------------
# WELLNESS LOG HELPER FUNCTIONS
# ---------------------------------------
def load_wellness_history():
    """Load previous check-ins from JSON file."""
    if os.path.exists(WELLNESS_LOG_FILE):
        try:
            with open(WELLNESS_LOG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("wellness_log.json is corrupted, starting fresh")
            return []
    return []


def get_last_checkin():
    """Get the most recent check-in."""
    history = load_wellness_history()
    return history[-1] if history else None


def format_history_context():
    """Format history for system prompt context."""
    history = load_wellness_history()
    if not history:
        return "This is the user's first check-in."
    
    last_entry = history[-1]
    context = f"\nPrevious check-in ({last_entry['date']}):\n"
    context += f"- Mood: {last_entry['mood']}\n"
    context += f"- Energy: {last_entry.get('energy', 'N/A')}\n"
    context += f"- Objectives: {', '.join(last_entry['objectives'])}\n"
    
    if len(history) >= 2:
        context += f"\nTotal check-ins so far: {len(history)}"
    
    return context


# ---------------------------------------
# BROADCAST CHECKIN STATE
# ---------------------------------------
async def broadcast_checkin_state(checkin: dict):
    """Send check-in state to frontend via data channel."""
    if current_room:
        payload = json.dumps({"type": "checkin_update", "checkin": checkin})
        await current_room.local_participant.publish_data(
            payload.encode('utf-8'),
            reliable=True
        )
        logger.info(f"Broadcasted check-in state: {checkin}")


# ---------------------------------------
# SAVE CHECK-IN TOOL
# ---------------------------------------
@function_tool()
async def save_checkin(
    mood: str,
    energy: str,
    objectives: list,
    summary: str
) -> str:
    """
    Save the daily wellness check-in data to wellness_log.json.
    
    Args:
        mood: User's self-reported mood (e.g., "good", "stressed", "tired")
        energy: User's energy level (e.g., "high", "medium", "low")
        objectives: List of 1-3 goals or intentions for the day
        summary: Brief summary of the conversation
    """
    try:
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "mood": mood,
            "energy": energy,
            "objectives": objectives,
            "summary": summary
        }
        
        # Load existing history
        history = load_wellness_history()
        history.append(entry)
        
        # Save to file
        with open(WELLNESS_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved check-in: {entry}")
        
        # Broadcast to frontend
        await broadcast_checkin_state(entry)
        
        return f"Check-in saved successfully! Recorded mood: {mood}, energy: {energy}, with {len(objectives)} objectives."
    
    except Exception as e:
        logger.error(f"Error saving check-in: {e}")
        return f"Error saving check-in: {str(e)}"


# ---------------------------------------
# UPDATE CHECKIN FIELD TOOL
# ---------------------------------------
@function_tool()
async def update_checkin_field(field: str, value: str) -> str:
    """Update a single field in the current check-in session."""
    try:
        return f"Updated {field} to {value}"
    except Exception as e:
        return f"Error updating field: {str(e)}"


# ---------------------------------------
# WELLNESS COMPANION AGENT
# ---------------------------------------
class WellnessCompanion(Agent):
    def __init__(self):
        # Get history context for system prompt
        history_context = format_history_context()
        
        super().__init__(
            # Replace the entire instructions section in WellnessCompanion class with this:

instructions=f"""You are a warm, supportive Health & Wellness Voice Companion. Your role is to conduct brief daily check-ins to help users reflect on their wellbeing and set intentions.

{history_context}

CHECK-IN STATE TO TRACK:
{{
  "mood": null,
  "energy": null,
  "objectives": [],
  "summary": null
}}

CRITICAL UNDERSTANDING RULES:
- Accept natural, conversational responses - not just perfect answers
- Understand the MEANING behind what people say, not just keywords
- If unclear, acknowledge and gently ask for clarification once
- Don't get stuck - if you can't understand after 2 tries, make your best guess and move on
- Be flexible with how people express themselves

MOOD/FEELING EXAMPLES (accept ANY of these and similar):
✓ "I'm okay" → neutral mood
✓ "Not great" → low/stressed mood  
✓ "Pretty good" → positive mood
✓ "Exhausted" → tired/low mood
✓ "Meh" → neutral/slightly low mood
✓ "Fantastic!" → very positive mood
✓ "Could be better" → somewhat negative mood
✓ "Stressed out" → anxious/stressed mood

ENERGY EXAMPLES (accept ANY of these):
✓ "High", "Good", "Energetic", "Full of energy" → high energy
✓ "Medium", "Okay", "Decent", "Alright" → medium energy
✓ "Low", "Tired", "Drained", "Exhausted", "Sleepy" → low energy

OBJECTIVES EXAMPLES (accept ANY phrasing):
✓ "Finish the report" 
✓ "Get some work done"
✓ "Exercise maybe"
✓ "Nothing much, just relax"
✓ "Call my friend"
✓ "Clean up a bit"

CONVERSATION FLOW (FOLLOW THIS ORDER):

1. GREETING & MOOD CHECK (1-2 minutes)
   - Start warmly: "Hi! Good to see you. How are you feeling today?"
   - LISTEN ACTIVELY: Accept any description of feelings
   - Show empathy: "I hear you" or "That makes sense"
   - If they mentioned something last time, reference it: "Last time you were feeling [X]. How's today compared to that?"
   - If response is unclear: "Can you tell me a bit more about that?"

2. ENERGY LEVEL (30 seconds)
   - Ask naturally: "How's your energy level today? High, medium, or low?"
   - Accept variations: tired = low, good = medium/high, energetic = high
   - Respond with understanding:
     * High: "That's great! Good energy to get things done."
     * Medium: "Okay, a decent level to work with."
     * Low: "I understand. We all have those days."

3. DAILY INTENTIONS (1-2 minutes)
   - Ask: "What are 2 or 3 things you'd like to accomplish today?"
   - Encourage self-care: "Anything you want to do for yourself? Like rest, exercise, or a hobby?"
   - Accept any goals - work, personal, self-care, or "nothing much"
   - If too many: "That's quite a list! Can we focus on the top 2-3 priorities?"
   - If vague: Clarify gently: "Can you be a bit more specific? Like what kind of work?"

4. GIVE THOUGHTFUL, PERSONALIZED ADVICE (2-3 minutes - IMPORTANT!)
   Based on their mood + energy + goals, offer 2-3 SPECIFIC suggestions:
   
   IF STRESSED/ANXIOUS:
   - "Try the Pomodoro technique: work 25 minutes, break 5 minutes"
   - "Start with the task that's stressing you most - getting it done will lift a weight"
   - "Write everything down first, then tackle one thing at a time"
   - "Take 3 deep breaths before starting each task"
   
   IF LOW ENERGY/TIRED:
   - "Start with the easiest task to build momentum"
   - "Take a 10-minute walk - movement really helps energy"
   - "Stay hydrated and have a healthy snack"
   - "Consider a 20-minute power nap if you can"
   - "Do important work early, save easy stuff for later"
   
   IF OVERWHELMED:
   - "Break that big project into 3 tiny steps for today"
   - "It's totally okay to move some things to tomorrow"
   - "Focus on progress, not perfection"
   - "Just do what you can - that's enough"
   
   IF GOOD ENERGY/MOTIVATED:
   - "Great! This is perfect timing for your challenging tasks"
   - "Batch similar tasks together for efficiency"
   - "Don't forget to schedule breaks to keep this momentum"
   - "Ride this energy wave - you've got this!"
   
   IF NEUTRAL/OKAY:
   - "Since you're feeling steady, tackle the most important thing first"
   - "Break your day into chunks - morning, afternoon, evening"
   - "Remember small wins add up!"

5. COMPREHENSIVE RECAP (1 minute)
   - Summarize EVERYTHING clearly:
     "Okay, let me recap what we discussed today:
     - You're feeling [mood] with [energy] energy
     - Your main goals are: [list each objective]
     - My suggestions: [repeat 2-3 key advice points from step 4]"
   
   - Ask for confirmation: "Does this all sound right? Anything you'd like to change?"
   - If they want changes, update and confirm again

6. SAVE & MOTIVATIONAL CLOSE (30 seconds)
   - When confirmed, call save_checkin(mood, energy, objectives, summary)
   - Give personalized closing based on their situation:
     * Stressed: "Remember, one step at a time. You've got this! 💪"
     * Tired: "Be kind to yourself today. Do what you can, and that's enough. 🌟"
     * Motivated: "Amazing energy! Use it wisely. Have a fantastic day! 🚀"
     * Overwhelmed: "Just breathe. Focus on one thing. You can do this. 💙"
     * Neutral: "You've got a solid plan. Go make it happen! ✨"
   
   - Always end warmly: "I'll check in with you next time. Take care of yourself!"

IMPORTANT RULES:
- Be conversational and natural - like talking to a supportive friend
- Total check-in: 5-7 minutes maximum
- Give SPECIFIC advice (not vague like "just do your best")
- Tailor everything to their exact mood/energy/goals
- ONE question at a time - don't rush
- If they seem to be struggling, be extra gentle and patient
- NEVER diagnose medical conditions or give medical advice
- Accept imperfect answers - understand the intent
- If stuck, make a reasonable assumption and move forward
- You're a caring companion, NOT a therapist or doctor

TONE: Warm, empathetic, practical, understanding, and genuinely motivating - like a close friend who really listens and offers real, helpful advice.
""",
            tools=[save_checkin, update_checkin_field]
        )


# ---------------------------------------
# PREWARM
# ---------------------------------------
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


# ---------------------------------------
# ENTRYPOINT
# ---------------------------------------
async def entrypoint(ctx: JobContext):
    global current_room
    
    try:
        ctx.log_context_fields = {"room": ctx.room.name}
        logger.info("Wellness agent started for room: %s", ctx.room.name)

        if not DEEPGRAM_API_KEY:
            raise RuntimeError(
                "DEEPGRAM_API_KEY is not set in backend/.env.local. "
                "Add DEEPGRAM_API_KEY=<your_key>."
            )

        # Store room reference for broadcasting
        current_room = ctx.room

        # PLUGINS - Same as your barista setup
        stt_plugin = deepgram.STT(api_key=DEEPGRAM_API_KEY, model="nova-3")
        llm_plugin = google.LLM(
            model="gemini-2.5-flash",
            temperature=0.8,  # Slightly higher for more natural conversation
        )
        tts_plugin = deepgram.TTS(
            model="aura-asteria-en",  # Warm, friendly voice
        )

        # Create AgentSession
        session = AgentSession(
            stt=stt_plugin,
            llm=llm_plugin,
            tts=tts_plugin,
            vad=ctx.proc.userdata.get("vad"),
            preemptive_generation=True,
            min_endpointing_delay=0.5,
            allow_interruptions=True,
        )

        # Initialize userdata with check-in state
        try:
            _ = session.userdata
        except ValueError:
            session.userdata = {}

        session.userdata["checkin"] = {
            "mood": None,
            "energy": None,
            "objectives": [],
            "summary": None,
        }

        # Metrics
        usage = metrics.UsageCollector()

        @session.on("metrics_collected")
        def collect(ev: MetricsCollectedEvent):
            metrics.log_metrics(ev.metrics)
            usage.collect(ev.metrics)

        async def log_usage():
            logger.info(f"Usage summary: {usage.get_summary()}")

        ctx.add_shutdown_callback(log_usage)

        # Broadcast state after agent speaks
        @session.on("agent_speech_committed")
        def on_agent_speech(text: str):
            asyncio.create_task(_handle_agent_speech(session.userdata["checkin"]))

        async def _handle_agent_speech(checkin: dict):
            """Handle agent speech event asynchronously."""
            await broadcast_checkin_state(checkin)

        logger.info("Starting wellness session for room: %s", ctx.room.name)
        
        # Connect to room FIRST
        await ctx.connect()
        logger.info("Connected to room")
        
        # Start session
        await session.start(
            agent=WellnessCompanion(),
            room=ctx.room,
        )
        logger.info("Session started")
        
        # Broadcast initial empty state
        await broadcast_checkin_state(session.userdata["checkin"])
        
        # Initial greeting
        last_entry = get_last_checkin()
        if last_entry:
            await session.say(
                f"Hi! Good to see you again. Ready for today's check-in?",
                add_to_chat_ctx=True
            )
        else:
            await session.say(
                "Hi there! I'm your wellness companion. Ready for your first check-in?",
                add_to_chat_ctx=True
            )

    except Exception as exc:
        logger.exception("Unhandled error in wellness agent: %s", exc)
        raise


# ---------------------------------------
# RUN WORKER
# ---------------------------------------
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="wellness-companion",
        )
    )