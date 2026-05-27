# Customer Support Autopilot (CSA)

## Project Overview

CSA automatically resolves customer support tickets (refunds, order status, FAQs) using a Groq LLM, a knowledge base (RAG), and real‑time e‑commerce data (Shopify, Stripe). It provides a chat widget and email handler. The goal is 70% auto‑resolution with sub‑second latency.

## Tech Stack

- **Backend**: FastAPI (async), Python 3.11+, LangGraph (agent orchestration), Groq SDK, Qdrant (vector DB), Redis (rate limiting & session store), SQLite (logs).
- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, Vercel AI SDK (streaming chat).
- **Infrastructure**: Docker Compose for development, environment variables via `.env`.
- **Integrations**: Shopify Admin API (REST), Stripe API, email parsing (SendGrid or simple IMAP).

## Features

1. **Chat Widget** – embeddable `<script>` that loads a React chat bubble. Uses Server‑Sent Events (SSE) for streaming responses.
2. **Email Auto‑responder** – POST endpoint `/api/email` that accepts email JSON, processes similarly to chat, and replies via email.
3. **Intent Classifier** – classify user message into: `refund_request`, `order_status`, `faq`, `human_escalation`.
4. **RAG over Knowledge Base** – load FAQs from markdown files, chunk, embed, store in Qdrant, and retrieve top‑k chunks.
5. **Order Lookup Tool** – call Shopify API to return shipping status, items, total.
6. **Refund Tool** – call Stripe refund endpoint after verifying order ID and amount.
7. **Fallback to Human** – for unknown intents or negative sentiment, create a ticket (logged to local "escalations" table).
8. **Merchant Dashboard** – simple Next.js page showing analytics and recent escalations.

## Quick Start

### With Docker (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd customer-support-autopilot

# Copy environment variables
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start all services
docker compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Dashboard: http://localhost:3000/dashboard
```

### Without Docker

See [BUILD.md](BUILD.md) for manual setup instructions.

## Embedding the Chat Widget

Add this single line to any HTML page:

```html
<script src="http://localhost:3000/widget.js"></script>
<script>
  window.CSA.init({
    backendUrl: 'http://localhost:8000',
    sessionId: 'unique-session-id' // optional, generated if not provided
  });
</script>
```

## API Reference

See [docs/api_reference.md](docs/api_reference.md) for complete API documentation.

## Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

- `GROQ_API_KEY`: Your Groq API key (get free key at https://console.groq.com)
- `SHOPIFY_STORE_URL`: Your Shopify store URL
- `SHOPIFY_ACCESS_TOKEN`: Shopify Admin API access token
- `STRIPE_SECRET_KEY`: Stripe secret key
- `QDRANT_URL`: Qdrant vector DB URL (default: http://qdrant:6333)
- `REDIS_URL`: Redis connection URL (default: redis://redis:6379)
- `ADMIN_API_KEY`: Admin API key for dashboard access

## License

MIT
