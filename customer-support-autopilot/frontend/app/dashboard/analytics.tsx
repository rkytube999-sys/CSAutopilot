interface Stats {
  total_conversations: number;
  auto_resolution_rate: number;
  cost_per_resolution: number;
}

interface DashboardAnalyticsProps {
  stats: Stats;
}

export default function DashboardAnalytics({ stats }: DashboardAnalyticsProps) {
  return (
    <div className="grid md:grid-cols-3 gap-6 mb-8">
      {/* Total Conversations */}
      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
          Total Conversations
        </h3>
        <p className="text-3xl font-bold">{stats.total_conversations}</p>
        <p className="text-sm text-green-600 mt-2">All time</p>
      </div>

      {/* Auto-Resolution Rate */}
      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
          Auto-Resolution Rate
        </h3>
        <p className="text-3xl font-bold">{stats.auto_resolution_rate}%</p>
        <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div 
            className="bg-green-500 h-2 rounded-full transition-all"
            style={{ width: `${Math.min(stats.auto_resolution_rate, 100)}%` }}
          />
        </div>
        <p className="text-sm text-gray-500 mt-2">Target: 70%</p>
      </div>

      {/* Cost per Resolution */}
      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
          Cost per Resolution
        </h3>
        <p className="text-3xl font-bold">${stats.cost_per_resolution.toFixed(4)}</p>
        <p className="text-sm text-gray-500 mt-2">Based on Groq token usage</p>
      </div>
    </div>
  );
}
