import { NextResponse } from "next/server";
import { AccessToken } from "livekit-server-sdk";
import { RoomConfiguration } from "@livekit/protocol";

export const revalidate = 0;

// Server-side env vars
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;

export async function POST(req: Request) {
  try {
    if (!LIVEKIT_URL) throw new Error("LIVEKIT_URL is not defined");
    if (!API_KEY) throw new Error("LIVEKIT_API_KEY is not defined");
    if (!API_SECRET) throw new Error("LIVEKIT_API_SECRET is not defined");

    const body = await req.json();

    // Which agent to use
    const agentName =
      body?.room_config?.agents?.[0]?.agent_name || "myagent";

    // Create unique room + identity
    const roomName = `voice_room_${Math.floor(Math.random() * 100000)}`;
    const identity = `user_${Math.floor(Math.random() * 100000)}`;

    // Build LiveKit token
    const token = new AccessToken(API_KEY, API_SECRET, {
      identity,
      name: identity,
      ttl: "15m",
    });

    token.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canPublishData: true,
      canSubscribe: true,
    });

    // Attach agent
    token.roomConfig = new RoomConfiguration({
      agents: [{ agentName }],
    });

    const jwt = await token.toJwt();

    return NextResponse.json(
      {
        serverUrl: LIVEKIT_URL,
        roomName,
        participantName: identity,
        participantToken: jwt,
      },
      { headers: { "Cache-Control": "no-store" } }
    );
  } catch (error: any) {
    console.error("ERROR IN /api/connection-details:", error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}