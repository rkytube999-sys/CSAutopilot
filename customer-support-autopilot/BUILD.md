# Build Guide - Customer Support Autopilot

This guide explains how to set up and run the CSA project without Docker.

## Prerequisites

- Python 3.11 or higher
- Node.js 18+ and npm
- Redis server running locally
- Qdrant vector database (can run via Docker or binary)

## Step 1: Install Backend Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Install Frontend Dependencies

```bash
cd frontend

# Install Node packages
npm install
```

## Step 3: Set Up Environment Variables

```bash
# From project root
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Required environment variables:
- `GROQ_API_KEY`: Get from https://console.groq.com
- `REDIS_URL`: Default is `redis://localhost:6379`
- `QDRANT_URL`: Default is `http://localhost:6333`
- Other API keys for Shopify, Stripe, etc. (optional for testing)

## Step 4: Start Redis

### Option A: Using Docker
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Option B: Native Installation
- **macOS**: `brew install redis && brew services start redis`
- **Linux**: `sudo apt-get install redis-server && sudo systemctl start redis`
- **Windows**: Download from https://github.com/microsoftarchive/redis/releases

## Step 5: Start Qdrant

### Option A: Using Docker
```bash
docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### Option B: Binary Installation
Download from https://qdrant.tech/documentation/quick-start/

## Step 6: Seed the Knowledge Base

```bash
# Create a sample knowledge base if it doesn't exist
mkdir -p knowledge_base

# Run the seeding script
python scripts/seed_kb.py --kb knowledge_base/faqs.md
```

## Step 7: Run the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## Step 8: Run the Frontend

```bash
cd frontend
npm run dev
```

The application will be available at http://localhost:3000

## Testing the Application

1. Open http://localhost:3000 in your browser
2. Try the chat widget by sending a message
3. Visit http://localhost:3000/dashboard to see analytics (use admin API key from .env)

## Troubleshooting

### Redis Connection Error
Ensure Redis is running: `redis-cli ping` should return `PONG`

### Qdrant Connection Error
Check if Qdrant is accessible: `curl http://localhost:6333`

### Groq API Error
Verify your API key is correct and has available credits

### Port Already in Use
Change the port in the respective configuration files or stop the conflicting service

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## Production Deployment

For production deployment, consider:
1. Using a managed Redis service (Redis Cloud, AWS ElastiCache)
2. Using Qdrant Cloud or a managed vector database
3. Setting up proper SSL/TLS certificates
4. Configuring CORS properly for your domain
5. Using environment-specific .env files
6. Setting up monitoring and logging (e.g., Sentry, Datadog)
