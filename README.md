# AI Voice Agents Challenge – 10 Days, 10 Agents

This repository contains my implementation for the **Murf AI Voice Agents Challenge 2025**. Each day, a unique AI voice agent is built using **LiveKit**, **Next.js**, and **Python backend agents** powered by **Murf Falcon TTS**.

This is my personal project repo where each agent evolves day-by-day.

---

# Day-1 — Base Agent Setup

**Completed:**

- Set up backend agent runner using LiveKit Agents SDK
- Connected frontend (Next.js) with backend
- Implemented STT → LLM → TTS pipeline
- Solved connection issues, session routing, and credential problems
- Successfully ran the starter voice agent end-to-end

**Outcome:**  
A working baseline voice agent capable of joining, listening, and responding.

---

# Day-2 — Starbucks Barista Voice Agent

**Theme:** Starbucks-style barista assistant with fast, conversational voice responses.

**What I built today:**

- Created a **Barista AI Agent** that takes orders like a Starbucks employee
- Customized backend `agent.py` with new prompt logic
- Added barista-style personality rules
- Implemented name suggestions (Starbucks theme)
- Integrated order-taking flow (coffee, size, sugar, addons)
- Added new React components (`OrderReceipt.tsx`)
- Updated UI in `page.tsx` to match the Barista agent use case
- Updated `route.ts` to reliably pass connection details
- Integrated frontend HTML/TSX improvements for the agent UI
- Cleaned up old LiveKit example content
- Ensured frontend and backend are synchronized for real-time conversation

**Outcome:**  
A fully working Starbucks-style AI Barista that talks, listens, takes orders, and responds instantly using Murf Falcon.

---

## Tech Stack

**Frontend:** Next.js 14 (App Router), React, TypeScript  
**Backend:** Python, LiveKit Agents SDK, Murf Falcon  
**Protocols:** WebRTC, WebSockets  
**Features:**

- Real-time transcriptions
- Ultra-fast TTS replies
- Agent behaviors + custom prompts
- Frontend UI for order visualization

---

## How to Run

### 1. Backend

cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/agent.py start

### 2. Frontend

Open in browser →  
http://localhost:3000

---

## Folder Structure

root/
├── backend/
│ ├── src/
│ │ └── agent.py
│ ├── orders/
│ └── requirements.txt
│
├── frontend/
│ ├── app/
│ ├── components/
│ │ └── OrderReceipt.tsx
│ └── page.tsx
│
├── README.md
└── .gitignore

---

## Notes

- venv/ is excluded from GitHub
- Daily challenge updates will continue in this repo
