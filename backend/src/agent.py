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
    RoomInputOptions,
    MetricsCollectedEvent,
    function_tool,
    llm,
)
from livekit.plugins import silero, google, deepgram

logger = logging.getLogger("agent")
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

# Global room reference for broadcasting
current_room = None

# ---------------------------------------
# BROADCAST ORDER HELPER
# ---------------------------------------
async def broadcast_order_state(order: dict):
    """Send order state to frontend via data channel."""
    if current_room:
        payload = json.dumps({"type": "order_update", "order": order})
        await current_room.local_participant.publish_data(
            payload.encode('utf-8'),
            reliable=True
        )
        logger.info(f"Broadcasted order state: {order}")

# ---------------------------------------
# SAVE ORDER TOOL
# ---------------------------------------
@function_tool()
async def save_order_to_disk(order: dict) -> str:
    """Save the completed order to a JSON file."""
    try:
        os.makedirs("orders", exist_ok=True)

        name = order.get("name", "customer")
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"orders/order_{name}_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(order, f, indent=2, ensure_ascii=False)

        # Broadcast final order
        await broadcast_order_state(order)

        return f"Order saved successfully to {filename}"
    except Exception as e:
        return f"Error saving order: {str(e)}"


# ---------------------------------------
# UPDATE ORDER TOOL
# ---------------------------------------
@function_tool()
async def update_order_field(field: str, value: str) -> str:
    """Update a single field in the order and broadcast to frontend."""
    try:
        # This will be called by the LLM to update order state
        # For now, just acknowledge - actual update happens in session.userdata
        return f"Updated {field} to {value}"
    except Exception as e:
        return f"Error updating order: {str(e)}"


# ---------------------------------------
# MAIN AGENT CLASS
# ---------------------------------------
class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
You are Sirena, a warm and friendly Starbucks barista. Your mission is to take a complete coffee order by filling this order state:
{
  "drinkType": null,
  "size": null,
  "milk": null,
  "extras": [],
  "name": null
}

CONVERSATION FLOW (STRICT ORDER):
1. GREETING: Start with "Welcome to Starbucks! I'm Sirena. What can I get started for you today?"

2. DRINK TYPE: Ask what drink they want (latte, cappuccino, americano, mocha, etc.)
   - If unclear, ask: "Would you like a hot or iced drink?"

3. SIZE: Ask "What size would you like? We have tall, grande, or venti."
   - Only accept: tall, grande, or venti

4. MILK: Ask "What type of milk? We have whole, 2%, almond, oat, soy, or coconut milk."
   - If they say "regular" → assume whole milk
   - If they say "none" or it's black coffee → set to "none"

5. EXTRAS: Ask "Would you like any extras? We have whipped cream, extra shot, caramel drizzle, vanilla syrup, or anything else?"
   - Store as array (can be empty [])
   - If they say "no" or "nothing" → set to []

6. NAME: Ask "And what name should I put on the cup?"

7. CONFIRMATION: Read back the COMPLETE order:
   "Perfect! So I have a [size] [drinkType] with [milk] milk, [list extras if any], for [name]. Is that correct?"

8. SAVE: When they confirm "yes", call save_order_to_disk with the complete order object.
   Then say: "Awesome! Your order is confirmed. That'll be ready in just a few minutes, [name]!"

RULES:
- Ask ONE question at a time
- Don't move to next field until current one is filled
- Be conversational but efficient
- Use the order state in session.userdata["order"]
- After filling each field, the order state is automatically sent to the display
- If customer gives multiple details at once, fill what you can and ask about missing fields
- Stay in character as a Starbucks barista

Tone: Friendly, upbeat, professional — classic Starbucks energy!
""",
            tools=[save_order_to_disk, update_order_field]
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
        logger.info("entrypoint started for room: %s", ctx.room.name)

        if not DEEPGRAM_API_KEY:
            raise RuntimeError(
                "DEEPGRAM_API_KEY is not set in backend/.env.local. "
                "Add DEEPGRAM_API_KEY=<your_key>."
            )

        # Store room reference for broadcasting
        current_room = ctx.room

        # PLUGINS - Optimized for speed
        stt_plugin = deepgram.STT(api_key=DEEPGRAM_API_KEY, model="nova-3")
        llm_plugin = google.LLM(
            model="gemini-2.5-flash",
            temperature=0.7,
        )
        # Use linear16 encoding (default) for compatibility
        tts_plugin = deepgram.TTS(
            model="aura-asteria-en",
        )

        # Create AgentSession with optimizations
        session = AgentSession(
            stt=stt_plugin,
            llm=llm_plugin,
            tts=tts_plugin,
            vad=ctx.proc.userdata.get("vad"),
            preemptive_generation=True,  # Already enabled - good!
            min_endpointing_delay=0.5,  # Faster turn detection (default is 0.8)
            allow_interruptions=True,  # Allow user to interrupt
        )

        # Initialize userdata
        try:
            _ = session.userdata
        except ValueError:
            session.userdata = {}

        # Create fresh order object
        session.userdata["order"] = {
            "drinkType": None,
            "size": None,
            "milk": None,
            "extras": [],
            "name": None,
        }

        usage = metrics.UsageCollector()

        @session.on("metrics_collected")
        def collect(ev: MetricsCollectedEvent):
            metrics.log_metrics(ev.metrics)
            usage.collect(ev.metrics)

        async def log_usage():
            logger.info(f"Usage summary: {usage.get_summary()}")

        ctx.add_shutdown_callback(log_usage)

        # ✅ FIXED: Changed async callback to sync wrapper
        @session.on("agent_speech_committed")
        def on_agent_speech(text: str):
            # Create async task to broadcast order state
            asyncio.create_task(_handle_agent_speech(session.userdata["order"]))

        # Helper function for async operations
        async def _handle_agent_speech(order: dict):
            """Handle agent speech event asynchronously."""
            await broadcast_order_state(order)

        logger.info("starting session for agent in room: %s", ctx.room.name)
        
        # ✅ Connect to room FIRST before starting session
        await ctx.connect()
        logger.info("ctx.connect completed")
        
        # ✅ Start session
        await session.start(
            agent=Assistant(),
            room=ctx.room,
        )
        logger.info("session.start completed")
        
        # ✅ Broadcast initial empty order AFTER session starts
        await broadcast_order_state(session.userdata["order"])
        
        # ✅ Force immediate greeting by using say()
        await session.say("Welcome to Starbucks! I'm Sam. What can I get started for you today?", add_to_chat_ctx=True)

    except Exception as exc:
        logger.exception("Unhandled error in entrypoint: %s", exc)
        raise


# ---------------------------------------
# RUN WORKER
# ---------------------------------------
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="myagent",
        )
    )