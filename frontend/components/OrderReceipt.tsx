"use client";

import { useEffect, useState } from 'react';
import { useRoomContext } from '@livekit/components-react';

interface Order {
  drinkType: string | null;
  size: string | null;
  milk: string | null;
  extras: string[];
  name: string | null;
}

export default function OrderReceipt() {
  const [order, setOrder] = useState<Order>({
    drinkType: null,
    size: null,
    milk: null,
    extras: [],
    name: null,
  });

  const room = useRoomContext();

  useEffect(() => {
    if (!room) return;

    // Listen for data messages from backend
    const handleData = (
      payload: Uint8Array,
      participant?: any,
      kind?: any
    ) => {
      try {
        const text = new TextDecoder().decode(payload);
        const data = JSON.parse(text);
        
        if (data.type === 'order_update') {
          console.log('Received order update:', data.order);
          setOrder(data.order);
        }
      } catch (error) {
        console.error('Error parsing order update:', error);
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
    <div className="fixed top-4 right-4 bg-white rounded-lg shadow-2xl p-6 w-80 border-2 border-green-600 z-50">
      {/* Starbucks Header */}
      <div className="text-center mb-4">
        <div className="text-2xl font-bold text-green-700">STARBUCKS</div>
        <div className="text-xs text-gray-500">ORDER IN PROGRESS</div>
      </div>

      {/* Order Details */}
      <div className="space-y-3 border-t border-b border-dashed border-gray-300 py-4">
        <OrderField label="Drink" value={order.drinkType} />
        <OrderField label="Size" value={order.size} />
        <OrderField label="Milk" value={order.milk} />
        <OrderField 
          label="Extras" 
          value={order.extras.length > 0 ? order.extras.join(', ') : null} 
        />
        <OrderField label="Name" value={order.name} />
      </div>

      {/* Footer */}
      <div className="mt-4 text-center text-xs text-gray-400">
        Your order is being prepared...
      </div>
    </div>
  );
}

function OrderField({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm font-medium text-gray-700">{label}:</span>
      <span className="text-sm text-gray-900 font-semibold">
        {value || (
          <span className="text-gray-400 italic">waiting...</span>
        )}
      </span>
    </div>
  );
}