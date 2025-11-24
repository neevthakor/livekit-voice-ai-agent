# AI Voice Agents Challenge – 10 Days, 10 Agents

This repository contains my implementation for the **Murf AI Voice Agents Challenge 2025**. Each day, a unique AI voice agent is built using **LiveKit**, **Next.js**, and **Python backend agents** powered by **Murf Falcon TTS**.

---

## 🎯 Day 1 — Base Agent Setup

**Completed:**

- ✅ Set up backend agent runner using LiveKit Agents SDK
- ✅ Connected frontend (Next.js) with backend
- ✅ Implemented STT → LLM → TTS pipeline
- ✅ Solved connection issues, session routing, and credential problems
- ✅ Successfully ran the starter voice agent end-to-end

**Outcome:**  
A working baseline voice agent capable of joining, listening, and responding in real-time.

---

## ☕ Day 2 — Starbucks Barista Voice Agent

**Theme:** Starbucks-style barista assistant with fast, conversational voice responses.

**What I Built:**

- ✅ Created a **Barista AI Agent** that takes orders like a Starbucks employee
- ✅ Customized backend `agent.py` with barista prompt logic
- ✅ Added barista-style personality and conversational flow
- ✅ Implemented order-taking flow (drink type, size, milk, extras, name)
- ✅ Created `OrderReceipt.tsx` React component for live order display
- ✅ Real-time order state broadcasting from backend to frontend
- ✅ JSON order persistence to `orders/` directory
- ✅ Updated UI to match Starbucks theme with green branding

**Features:**

- 🎙️ Voice-first ordering experience
- 📝 Live order visualization
- 💾 Order history saved to JSON files
- ⚡ Ultra-fast TTS responses using Murf Falcon

**Agent Name:** `myagent`

---

## 💙 Day 3 — Health & Wellness Voice Companion

**Theme:** Empathetic wellness companion for daily check-ins and goal setting.

**What I Built:**

- ✅ Created **Wellness Companion Agent** for daily mental health check-ins
- ✅ Built `wellness_agent.py` with empathetic conversation flow
- ✅ Implemented mood and energy level tracking
- ✅ Daily intentions/objectives collection (1-3 goals)
- ✅ Personalized advice based on user's mood, energy, and goals
- ✅ Created `WellnessCheckIn.tsx` component for live check-in display
- ✅ JSON persistence to `wellness_log.json` with full history
- ✅ Historical context awareness (references previous check-ins)
- ✅ Comprehensive recap and motivational closing

**Features:**

- 🧠 Natural language understanding (accepts conversational responses)
- 💬 Empathetic, supportive conversation style
- 📊 Tracks mood, energy, and daily objectives
- 💡 Personalized, actionable wellness advice
- 📝 Persistent check-in history across sessions
- 🎨 Blue-themed UI for wellness/healthcare feel

**Agent Name:** `wellness-companion`

**Check-in Flow:**

1. Greeting & mood assessment
2. Energy level evaluation
3. Daily goal/intention setting
4. Personalized advice & suggestions
5. Comprehensive recap
6. Motivational closing & data save

---

## 🛠️ Tech Stack

**Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS  
**Backend:** Python 3.10+, LiveKit Agents SDK  
**Voice Tech:** Deepgram STT, Google Gemini 2.5 Flash LLM, Deepgram TTS (Aura Asteria)  
**Real-time:** WebRTC, WebSockets, LiveKit Cloud  
**Data Storage:** JSON file-based persistence

---

## 🚀 How to Run

### Prerequisites

- Python 3.10+
- Node.js 18+
- LiveKit Cloud account (or self-hosted LiveKit server)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 2. Environment Variables

Create `backend/.env.local`:

```env
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_API_KEY=your_google_key
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
```

Create `frontend/.env.local`:

```env
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
NEXT_PUBLIC_AGENT_NAME=wellness-companion
```

### 3. Run Backend Agent

**For Day 2 (Starbucks Barista):**

```bash
cd backend
python src/agent.py dev
```

**For Day 3 (Wellness Companion):**

```bash
cd backend
python src/wellness_agent.py start
```

### 4. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Open in Browser

Navigate to `http://localhost:3000`

---

## 📁 Project Structure

```
ten-days-of-voice-agents-2025/
├── backend/
│   ├── src/
│   │   ├── agent.py              # Day 2: Starbucks Barista
│   │   └── wellness_agent.py     # Day 3: Wellness Companion
│   ├── orders/                   # Saved coffee orders (Day 2)
│   ├── wellness_log.json         # Check-in history (Day 3)
│   ├── requirements.txt
│   └── .env.local
│
├── frontend/
│   ├── app/
│   │   └── (app)/
│   │       └── page.tsx
│   ├── components/
│   │   ├── app/
│   │   │   ├── app.tsx
│   │   │   ├── session-provider.tsx
│   │   │   ├── session-view.tsx
│   │   │   ├── view-controller.tsx
│   │   │   └── welcome-view.tsx
│   │   ├── OrderReceipt.tsx      # Day 2 UI
│   │   └── WellnessCheckIn.tsx   # Day 3 UI
│   ├── lib/
│   │   └── utils.ts
│   ├── app-config.ts
│   └── .env.local
│
├── README.md
└── .gitignore
```

---

## 🎨 Agent Switching

To switch between agents, update `frontend/app-config.ts`:

**For Starbucks Barista (Day 2):**

```typescript
agentName: 'myagent',
```

**For Wellness Companion (Day 3):**

```typescript
agentName: 'wellness-companion',
```

Or use the environment variable in `frontend/.env.local`:

```env
NEXT_PUBLIC_AGENT_NAME=wellness-companion
```

---

## 📊 Data Persistence

**Day 2 (Starbucks):**  
Orders saved to `backend/orders/order_[name]_[timestamp].json`

**Day 3 (Wellness):**  
All check-ins appended to `backend/wellness_log.json`

Example wellness log entry:

```json
{
  "date": "2024-11-24",
  "timestamp": "2024-11-24T10:30:00.123456",
  "mood": "stressed",
  "energy": "low",
  "objectives": ["finish project report", "go for a walk"],
  "summary": "User feeling stressed with low energy, focusing on project completion and self-care"
}
```

---

## 🎯 Key Features by Day

### Day 1

- Basic voice agent foundation
- LiveKit integration
- STT/LLM/TTS pipeline

### Day 2

- Conversational order taking
- Real-time UI updates
- Order persistence
- Custom barista personality

### Day 3

- Empathetic conversation AI
- Natural language understanding
- Personalized wellness advice
- Historical context awareness
- Comprehensive check-in flow

---

## 🔥 Upcoming Days

- Day 4-10: More specialized agents coming soon!

---

## 🤝 Contributing

This is a personal challenge project, but feel free to fork and create your own version!

---

## 📝 Notes

- `venv/` is excluded from GitHub
- Each day's agent runs independently
- Frontend UI switches based on `agentName` config
- All agents use the same LiveKit infrastructure

---

## 🏆 Challenge Info

Part of the **#MurfAIVoiceAgentsChallenge** and **#10DaysofAIVoiceAgents**  
Building with the fastest TTS API - **Murf Falcon**

---

**Built with ❤️ using LiveKit, Next.js, and Python**
