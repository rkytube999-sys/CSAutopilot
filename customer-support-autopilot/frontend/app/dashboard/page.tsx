'use client';

import { useState, useEffect } from 'react';
import DashboardAnalytics from './analytics';

interface Stats {
  total_conversations: number;
  auto_resolution_rate: number;
  cost_per_resolution: number;
  recent_escalations: any[];
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [apiKey, setApiKey] = useState('');

  const fetchStats = async () => {
    if (!apiKey) {
      setError('Please enter admin API key');
      return;
    }

    try {
      const response = await fetch(`/api/stats?api_key=${apiKey}`);
      if (!response.ok) {
        throw new Error('Invalid API key');
      }
      const data = await response.json();
      setStats(data);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Monitor your Customer Support Autopilot performance
          </p>
        </header>

        {/* API Key Input */}
        <div className="mb-8 p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
          <label className="block text-sm font-medium mb-2">Admin API Key</label>
          <div className="flex gap-2">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your admin API key"
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
            />
            <button
              onClick={fetchStats}
              disabled={loading}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Load Stats'}
            </button>
          </div>
          {error && (
            <p className="mt-2 text-red-600 text-sm">{error}</p>
          )}
        </div>

        {/* Stats Display */}
        {stats && (
          <>
            <DashboardAnalytics stats={stats} />
            
            {/* Recent Escalations */}
            <div className="mt-8 p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Recent Escalations</h2>
              {stats.recent_escalations && stats.recent_escalations.length > 0 ? (
                <table className="w-full">
                  <thead>
                    <tr className="border-b dark:border-gray-700">
                      <th className="text-left py-2">Ticket ID</th>
                      <th className="text-left py-2">Intent</th>
                      <th className="text-left py-2">Created</th>
                      <th className="text-left py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.recent_escalations.map((esc: any) => (
                      <tr key={esc.id} className="border-b dark:border-gray-700">
                        <td className="py-2 font-mono text-sm">{esc.id}</td>
                        <td className="py-2">{esc.intent}</td>
                        <td className="py-2 text-gray-600 dark:text-gray-400">
                          {new Date(esc.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-2">
                          <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-sm">
                            {esc.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-500">No recent escalations</p>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
