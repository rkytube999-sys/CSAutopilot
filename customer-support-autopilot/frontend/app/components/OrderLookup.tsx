'use client';

import { useState } from 'react';

interface OrderInfo {
  order_id: number;
  order_number: number;
  status: string;
  fulfillment_status: string;
  total: string;
  items: Array<{ name: string; quantity: number; price: string }>;
}

interface OrderLookupProps {
  backendUrl?: string;
}

export default function OrderLookup({ backendUrl = 'http://localhost:8000' }: OrderLookupProps) {
  const [orderId, setOrderId] = useState('');
  const [order, setOrder] = useState<OrderInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setOrder(null);

    try {
      // This would call the backend API with Shopify integration
      const response = await fetch(`${backendUrl}/api/tools/order/${orderId}`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error('Order not found');
      }

      const data = await response.json();
      setOrder(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to lookup order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Order Lookup</h3>
      
      <form onSubmit={handleLookup} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="Enter order ID"
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
          />
          <button
            type="submit"
            disabled={loading || !orderId}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? '...' : 'Lookup'}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-3 bg-red-100 dark:bg-red-900/20 text-red-600 rounded">
          {error}
        </div>
      )}

      {order && (
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Order #:</span>
            <span className="font-medium">{order.order_number}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Status:</span>
            <span className={`px-2 py-1 rounded text-sm ${
              order.status === 'paid' 
                ? 'bg-green-100 text-green-700' 
                : 'bg-yellow-100 text-yellow-700'
            }`}>
              {order.status}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Fulfillment:</span>
            <span>{order.fulfillment_status || 'Pending'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Total:</span>
            <span className="font-medium">${order.total}</span>
          </div>
          
          {order.items && order.items.length > 0 && (
            <div className="pt-3 border-t dark:border-gray-700">
              <h4 className="font-medium mb-2">Items:</h4>
              <ul className="space-y-1">
                {order.items.map((item, idx) => (
                  <li key={idx} className="text-sm">
                    {item.name} x {item.quantity} - ${item.price}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
