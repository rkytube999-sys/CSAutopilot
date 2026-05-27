import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-bold mb-4">Customer Support Autopilot</h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            AI-powered customer support that resolves 70% of tickets automatically
          </p>
        </header>

        <section className="grid md:grid-cols-2 gap-8 mb-12">
          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <h2 className="text-2xl font-semibold mb-4">Features</h2>
            <ul className="space-y-2">
              <li>✓ Automatic intent classification</li>
              <li>✓ RAG-powered knowledge base</li>
              <li>✓ Order status lookup (Shopify)</li>
              <li>✓ Refund processing (Stripe)</li>
              <li>✓ Email auto-responder</li>
              <li>✓ Human escalation fallback</li>
            </ul>
          </div>

          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <h2 className="text-2xl font-semibold mb-4">Quick Links</h2>
            <div className="space-y-3">
              <Link 
                href="/dashboard" 
                className="block p-3 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
              >
                Dashboard →
              </Link>
              <a 
                href="/docs/api_reference.md" 
                className="block p-3 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition"
              >
                API Documentation
              </a>
            </div>
          </div>
        </section>

        <section className="p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <h2 className="text-2xl font-semibold mb-4">Embed the Chat Widget</h2>
          <p className="mb-4">Add this to any HTML page:</p>
          <pre className="bg-gray-900 text-green-400 p-4 rounded overflow-x-auto text-sm">
{`<script src="http://localhost:3000/widget.js"></script>
<script>
  window.CSA.init({
    backendUrl: 'http://localhost:8000'
  });
</script>`}
          </pre>
        </section>
      </div>
    </main>
  );
}
