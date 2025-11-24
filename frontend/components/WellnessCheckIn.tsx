"use client";
import { useEffect, useState } from 'react';
import { useRoomContext } from '@livekit/components-react';

interface CheckIn {
  mood: string | null;
  energy: string | null;
  objectives: string[];
  summary: string | null;
}

export default function WellnessCheckIn() {
  const [checkin, setCheckIn] = useState<CheckIn>({
    mood: null,
    energy: null,
    objectives: [],
    summary: null,
  });

  const room = useRoomContext();

  useEffect(() => {
    if (!room) return;

    // Listen for data messages from wellness backend
    const handleData = (
      payload: Uint8Array,
      participant?: any,
      kind?: any
    ) => {
      try {
        const text = new TextDecoder().decode(payload);
        const data = JSON.parse(text);
        
        if (data.type === 'checkin_update') {
          console.log('Received check-in update:', data.checkin);
          setCheckIn(data.checkin);
        }
      } catch (error) {
        console.error('Error parsing check-in update:', error);
      }
    };

    // Subscribe to data received events
    room.on('dataReceived', handleData);

    // Cleanup
    return () => {
      room.off('dataReceived', handleData);
    };
  }, [room]);

  return (
    <div className="fixed top-4 right-4 bg-white rounded-lg shadow-2xl p-6 w-80 border-2 border-blue-500 z-50">
      {/* Wellness Header */}
      <div className="text-center mb-4">
        <div className="text-2xl font-bold text-blue-600">WELLNESS CHECK-IN</div>
        <div className="text-xs text-gray-500">DAILY REFLECTION</div>
      </div>

      {/* Check-in Details */}
      <div className="space-y-3 border-t border-b border-dashed border-gray-300 py-4">
        <CheckInField label="Mood" value={checkin.mood} />
        <CheckInField label="Energy" value={checkin.energy} />
        <CheckInField 
          label="Objectives" 
          value={checkin.objectives.length > 0 ? checkin.objectives.join(', ') : null} 
          multiline={true}
        />
      </div>

      {/* Footer */}
      <div className="mt-4 text-center text-xs text-gray-400">
        Take care of yourself today 💙
      </div>
    </div>
  );
}

function CheckInField({ 
  label, 
  value, 
  multiline = false 
}: { 
  label: string; 
  value: string | null;
  multiline?: boolean;
}) {
  return (
    <div className={multiline ? "space-y-1" : "flex justify-between items-center"}>
      <span className="text-sm font-medium text-gray-700">{label}:</span>
      <span className={`text-sm text-gray-900 font-semibold ${multiline ? 'block mt-1' : ''}`}>
        {value || (
          <span className="text-gray-400 italic">waiting...</span>
        )}
      </span>
    </div>
  );
}