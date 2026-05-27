# GAP ANALYSIS & FIX PLAN

## Mission Statement

Transform this project into a REAL production-ready SaaS that ACTUALLY matches every claim in README.md.

**Success Criterion:** README claims == real implementation

---

## Gap #1: Fake Analytics Endpoint

### Current State
```python
# backend/app/main.py:75-87
@app.get("/api/stats", tags=["stats"])
async def get_stats(api_key: str):
    """Get analytics stats for dashboard."""
    if api_key != settings.admin_api_key:
        return {"error": "Unauthorized"}, 401
    
    # Return mock stats for now - will be implemented with actual data
    return {
        "total_conversations": 0,
        "auto_resolution_rate": 0.0,
        "cost_per_resolution": 0.0,
        "recent_escalations": [],
    }
```

### Required State
- Real metrics from database
- Token usage aggregation
- Resolution rate calculation
- Recent escalations from SQLite

### Fix Plan

**File:** `backend/app/main.py`

**Changes:**
1. Import `get_analytics` and `get_recent_escalations` from `app.core.fallback`
2. Replace mock return with actual function calls
3. Add proper error handling

**Code:**
```python
from app.core.fallback import get_analytics, get_recent_escalations

@app.get("/api/stats", tags=["stats"])
async def get_stats(api_key: str):
    """Get analytics stats for dashboard."""
    if api_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Get real analytics from database
        analytics = await get_analytics()
        
        # Get recent escalations
        escalations = await get_recent_escalations(limit=10)
        
        # Format escalations (remove sensitive data)
        formatted_escalations = [
            {
                "ticket_id": e["id"],
                "session_id": e["session_id"],
                "intent": e["intent"],
                "sentiment": e["sentiment"],
                "created_at": e["created_at"],
                "status": e["status"],
            }
            for e in escalations
        ]
        
        return {
            "total_conversations": analytics["total_conversations"],
            "auto_resolution_rate": analytics["auto_resolution_rate"],
            "cost_per_resolution": analytics["cost_per_resolution"],
            "total_tokens_used": analytics["total_tokens_used"],
            "estimated_cost": analytics["estimated_cost"],
            "recent_escalations": formatted_escalations,
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")
```

**Priority:** 🔴 CRITICAL  
**Estimated Effort:** 1 hour  
**Dependencies:** fallback.py already has get_analytics() implemented

---

## Gap #2: Hash-Based Pseudo-Embeddings

### Current State
```python
# backend/app/integrations/groq_client.py:148-170
async def embed_text(text: str) -> List[float]:
    """Generate embedding for text using hash-based approach."""
    import hashlib
    # Create deterministic but meaningless vectors
    hash_bytes = hashlib.sha256(text.encode()).digest()
    embedding = []
    for i in range(384):
        seed = hash_bytes[i % len(hash_bytes)] + i
        value = (hashlib.md5(bytes([seed])).digest()[0] - 128) / 128.0
        embedding.append(float(value))
    return embedding
```

### Problem
- Hash-based vectors have NO semantic meaning
- Similar texts produce completely different embeddings
- RAG retrieval will return RANDOM results
- System cannot find relevant knowledge base articles

### Required State
- Real sentence embeddings using ML model
- Semantic similarity matching
- Fallback to local model when API unavailable

### Fix Plan

**Option A: Use Sentence Transformers (Recommended for Development)**

**File:** `backend/app/integrations/embeddings.py` (NEW)

**Requirements:** Add to `requirements.txt`:
```
sentence-transformers==2.3.0
```

**Code:**
```python
"""
Real text embeddings using sentence-transformers.
"""
import logging
from typing import List, Optional
from functools import lru_cache

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Global model instance (lazy loading)
_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """Get or load the sentence transformer model."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformer model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded successfully")
    return _model


async def embed_text(text: str) -> List[float]:
    """
    Generate real semantic embeddings for text.
    
    Args:
        text: Text to embed
        
    Returns:
        384-dimensional embedding vector
    """
    try:
        model = get_model()
        embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        # Fallback to simple average of word vectors (better than hash)
        return _fallback_embedding(text)


def _fallback_embedding(text: str) -> List[float]:
    """Simple fallback using word frequency (384 dimensions)."""
    # Initialize zero vector
    embedding = [0.0] * 384
    
    # Simple tokenization
    words = text.lower().split()
    
    if not words:
        return embedding
    
    # Hash each word to multiple dimensions
    for i, word in enumerate(words):
        for j, char in enumerate(word[:20]):  # Limit to first 20 chars
            dim = (hash(char) + i * 7 + j * 13) % 384
            embedding[dim] += 1.0 / len(words)
    
    # Normalize
    magnitude = sum(x * x for x in embedding) ** 0.5
    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]
    
    return embedding
```

**Update:** `backend/app/integrations/groq_client.py`
- Remove `embed_text()` function
- Import from new embeddings module: `from app.integrations.embeddings import embed_text`

**Priority:** 🔴 CRITICAL  
**Estimated Effort:** 2 hours  
**Impact:** RAG will actually work correctly

---

## Gap #3: Simulated Streaming (Not Real Token Streaming)

### Current State
```python
# backend/app/api/chat.py:163-169
# Stream the response character by character (simulated)
response_text = result.get("response", "")
for char in response_text:
    yield {
        "type": "token",
        "token": char,
    }
```

### Problem
- Waits for FULL response before streaming
- Character-by-character is fake streaming
- Doesn't use Groq's streaming API
- First token latency is HIGH (waits for complete generation)

### Required State
- True token-by-token streaming from Groq
- Sub-second first token time
- Real-time SSE events

### Fix Plan

**File:** `backend/app/integrations/groq_client.py`

**Add new function:**
```python
async def stream_response(
    message: str,
    intent: str,
    context: Optional[List[dict]] = None,
    tool_result: Optional[dict] = None,
    conversation_history: Optional[List[dict]] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream response tokens from Groq in real-time.
    
    Yields:
        Dictionary with token and metadata
    """
    # Build prompt (same as generate_response)
    system_prompt = f"""You are a helpful customer support assistant..."""
    messages = [{"role": "system", "content": system_prompt}]
    
    if conversation_history:
        for turn in conversation_history[-5:]:
            messages.append(turn)
    
    messages.append({"role": "user", "content": message})
    
    if not groq_client:
        yield {"token": _fallback_response(message), "done": True}
        return
    
    try:
        # Use Groq's streaming API
        stream = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=0.7,
            max_tokens=512,
            stream=True,  # Enable streaming
        )
        
        total_tokens = 0
        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                yield {"token": token, "done": False}
                total_tokens += 1
        
        yield {"token": "", "done": True, "tokens_used": total_tokens}
        
    except Exception as e:
        logger.error(f"Error streaming response: {e}")
        yield {"token": "Error generating response", "done": True, "error": str(e)}
```

**File:** `backend/app/api/chat.py`

**Update `process_message_stream`:**
```python
async def process_message_stream(...) -> AsyncGenerator[Dict[str, Any], None]:
    """Process message and stream REAL tokens from Groq."""
    from app.integrations.groq_client import stream_response
    
    yield {"type": "status", "message": "Processing..."}
    
    # Classify intent first (non-streaming)
    intent_result = await classify_intent(message, conversation_history)
    yield {"type": "intent", "intent": intent_result["intent"]}
    
    # Retrieve knowledge (non-streaming)
    chunks = await retrieve_knowledge(message, top_k=3)
    
    # Stream response from Groq
    async for event in stream_response(
        message=message,
        intent=intent_result["intent"],
        context=chunks,
        conversation_history=conversation_history,
    ):
        if event.get("done"):
            yield {
                "type": "complete",
                "response": message,  # Full response accumulated client-side
                "tokens_used": event.get("tokens_used", 0),
            }
        else:
            yield {"type": "token", "token": event["token"]}
```

**Priority:** 🔴 CRITICAL  
**Estimated Effort:** 3 hours  
**Impact:** True sub-second first token latency

---

## Gap #4: Missing Email Implementation

### Current State
```python
# backend/app/tools/email_tools.py
"""Email tools placeholder."""
# Almost empty - no actual implementation
```

### Required State
- Send emails via SMTP/SendGrid
- Parse inbound emails
- Attach responses to tickets

### Fix Plan

**File:** `backend/app/tools/email_tools.py`

**Complete Implementation:**
```python
"""
Email sending and receiving tools.
"""
import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_email(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send an email via SMTP.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        html: Whether body is HTML
        cc: CC recipients
        bcc: BCC recipients
        
    Returns:
        Send result dictionary
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = "support@yourstore.com"  # Configure in env
        msg["To"] = to
        
        if cc:
            msg["Cc"] = ", ".join(cc)
        
        # Attach body
        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body, mime_type))
        
        # Send via SMTP
        await aiosmtplib.send(
            msg,
            hostname=settings.email_smtp_host,
            port=587,
            username=settings.email_smtp_user,
            password=settings.email_smtp_pass,
            start_tls=True,
        )
        
        logger.info(f"Email sent to {to}: {subject}")
        
        return {
            "success": True,
            "recipient": to,
            "subject": subject,
        }
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {
            "success": False,
            "error": str(e),
            "recipient": to,
        }


async def send_support_response(
    to: str,
    original_subject: str,
    response: str,
    ticket_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a support response to customer.
    
    Args:
        to: Customer email
        original_subject: Original email subject
        response: AI-generated response
        ticket_id: Escalation ticket ID if applicable
        
    Returns:
        Send result
    """
    # Prefix subject with Re: if not present
    if not original_subject.lower().startswith("re:"):
        subject = f"Re: {original_subject}"
    else:
        subject = original_subject
    
    # Add ticket ID if present
    if ticket_id:
        subject = f"[{ticket_id}] {subject}"
    
    # Format email body
    body = f"""
Hello,

Thank you for contacting customer support. {response}

Best regards,
Customer Support Team

---
Ticket ID: {ticket_id or 'N/A'}
"""
    
    return await send_email(to, subject, body)


async def parse_inbound_email(
    raw_email: bytes,
) -> Dict[str, Any]:
    """
    Parse inbound email from raw bytes.
    
    Args:
        raw_email: Raw email bytes
        
    Returns:
        Parsed email dictionary
    """
    from email import message_from_bytes
    
    try:
        msg = message_from_bytes(raw_email)
        
        # Extract headers
        subject = msg.get("Subject", "")
        from_addr = msg.get("From", "")
        to_addr = msg.get("To", "")
        date = msg.get("Date", "")
        
        # Extract body (prefer plain text)
        body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode()
                elif content_type == "text/html":
                    html_body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()
        
        return {
            "from": from_addr,
            "to": to_addr,
            "subject": subject,
            "date": date,
            "body": body,
            "html_body": html_body,
            "headers": dict(msg.items()),
        }
        
    except Exception as e:
        logger.error(f"Failed to parse email: {e}")
        return {
            "error": str(e),
            "raw_subject": subject if 'subject' in dir() else "Unknown",
        }
```

**File:** `backend/app/api/email.py`

**Update to use email_tools:**
```python
from app.tools.email_tools import send_support_response, parse_inbound_email

@router.post("/")
async def email_endpoint(request: EmailRequest) -> EmailResponse:
    """Process inbound email and send AI response."""
    # Process through orchestrator (same as chat)
    result = await process_message(
        message=request.body,
        session_id=f"email-{request.from_addr}-{datetime.now().date()}",
    )
    
    # Send email response
    send_result = await send_support_response(
        to=request.from_addr,
        original_subject=request.subject,
        response=result["response"],
        ticket_id=result.get("ticket_id"),
    )
    
    return EmailResponse(
        success=send_result.get("success", False),
        response=result["response"],
        ticket_id=result.get("ticket_id"),
    )
```

**Priority:** 🟡 HIGH  
**Estimated Effort:** 3 hours  
**Dependencies:** aiosmtplib already in requirements.txt

---

## Gap #5: No JWT Authentication

### Current State
- No authentication middleware
- Admin API key passed in query string (insecure)
- CORS allows all origins
- No RBAC

### Required State
- JWT-based authentication
- Refresh token rotation
- Role-based access control
- Secure cookie storage

### Fix Plan

**Create:** `backend/app/auth/jwt.py` (NEW FILE)

```python
"""
JWT authentication module.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Security scheme
security = HTTPBearer(auto_error=False)

# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class TokenPayload(BaseModel):
    """JWT payload schema."""
    sub: str  # User ID
    role: str = "user"
    exp: datetime
    type: str = "access"  # 'access' or 'refresh'


class UserToken(BaseModel):
    """Token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_access_token(user_id: str, role: str = "user") -> str:
    """Create JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = TokenPayload(
        sub=user_id,
        role=role,
        exp=expire,
        type="access",
    )
    return jwt.encode(payload.dict(), settings.admin_api_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = TokenPayload(
        sub=user_id,
        role="user",
        exp=expire,
        type="refresh",
    )
    return jwt.encode(payload.dict(), settings.admin_api_key, algorithm=ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> TokenPayload:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.admin_api_key, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Verify expiration
        if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
            raise HTTPException(status_code=401, detail="Token expired")
        
        return TokenPayload(**payload)
        
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenPayload:
    """Get current authenticated user from request."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return verify_token(credentials.credentials)


def require_role(required_role: str):
    """Decorator to require specific role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user')
            if not user or user.role != required_role:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Update:** `backend/app/main.py`

```python
from app.auth.jwt import get_current_user, TokenPayload

@app.get("/api/stats", tags=["stats"])
async def get_stats(user: TokenPayload = Depends(get_current_user)):
    """Get analytics stats (requires authentication)."""
    # Check role
    if user.role not in ["admin", "merchant"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # ... rest of implementation
```

**Add Auth Endpoints:** `backend/app/api/auth.py` (NEW)

```python
@router.post("/login")
async def login(email: str, password: str):
    """Login and get tokens."""
    # Validate credentials (implement your user store)
    user = await authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return UserToken(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    payload = verify_token(refresh_token, token_type="refresh")
    
    return {
        "access_token": create_access_token(payload.sub, payload.role),
        "refresh_token": create_refresh_token(payload.sub),
    }
```

**Priority:** 🔴 CRITICAL  
**Estimated Effort:** 4 hours  
**Dependencies:** Add `python-jose[cryptography]` to requirements.txt

---

## Gap #6: No Testing Infrastructure

### Current State
- Only `test_orchestrator.py` exists
- No unit tests
- No integration tests
- No E2E tests
- No coverage reporting

### Required State
- Unit tests for all components
- Integration tests for APIs
- E2E tests with realistic scenarios
- >90% code coverage

### Fix Plan

**Create Test Structure:**
```
backend/tests/
├── __init__.py
├── conftest.py
├── test_api/
│   ├── __init__.py
│   ├── test_chat.py
│   ├── test_email.py
│   ├── test_webhooks.py
│   └── test_auth.py
├── test_core/
│   ├── __init__.py
│   ├── test_classifier.py
│   ├── test_rag_engine.py
│   ├── test_orchestrator.py
│   └── test_fallback.py
├── test_tools/
│   ├── __init__.py
│   ├── test_shopify.py
│   ├── test_stripe.py
│   └── test_email_tools.py
└── test_integrations/
    ├── __init__.py
    ├── test_groq_client.py
    ├── test_vector_db.py
    └── test_embeddings.py
```

**File:** `backend/tests/conftest.py` (NEW)

```python
"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_message():
    """Sample chat message."""
    return {
        "message": "Where is my order #12345?",
        "session_id": "test-session-123",
    }


@pytest.fixture
def auth_headers(client):
    """Get authenticated headers."""
    # Login and get token
    response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "testpass123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**File:** `backend/tests/test_core/test_classifier.py` (NEW)

```python
"""
Tests for intent classifier.
"""
import pytest
from app.core.classifier import classify_intent


@pytest.mark.asyncio
async def test_refund_classification():
    """Test refund intent classification."""
    result = await classify_intent("I want a refund for my order")
    
    assert result["intent"] == "refund_request"
    assert result["confidence"] > 0.5
    assert result["sentiment"] in ["positive", "neutral", "negative"]


@pytest.mark.asyncio
async def test_order_status_classification():
    """Test order status classification."""
    result = await classify_intent("Where is my order?")
    
    assert result["intent"] == "order_status"
    assert result["confidence"] > 0.5


@pytest.mark.asyncio
async def test_escalation_classification():
    """Test human escalation classification."""
    result = await classify_intent(
        "This is terrible! I want to speak to a human agent NOW!"
    )
    
    assert result["intent"] == "human_escalation"
    assert result["sentiment"] == "negative"
```

**Update:** `backend/requirements.txt`

```
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0
python-jose[cryptography]==3.3.4
```

**Add Makefile Target:**

```makefile
test:
	cd backend && pytest --cov=app --cov-report=html --cov-report=term-missing

test-e2e:
	cd backend && pytest tests/e2e/ -v
```

**Priority:** 🟡 HIGH  
**Estimated Effort:** 8 hours  
**Impact:** Prevents regressions, enables confident refactoring

---

## Summary of All Gaps

| # | Gap | Priority | Effort | Status |
|---|-----|----------|--------|--------|
| 1 | Fake Analytics | 🔴 CRITICAL | 1h | ⏳ Pending |
| 2 | Hash Embeddings | 🔴 CRITICAL | 2h | ⏳ Pending |
| 3 | Simulated Streaming | 🔴 CRITICAL | 3h | ⏳ Pending |
| 4 | Email Implementation | 🟡 HIGH | 3h | ⏳ Pending |
| 5 | JWT Authentication | 🔴 CRITICAL | 4h | ⏳ Pending |
| 6 | Testing Infrastructure | 🟡 HIGH | 8h | ⏳ Pending |
| 7 | Security Hardening | 🔴 CRITICAL | 6h | ⏳ Pending |
| 8 | Dashboard Connection | 🟡 HIGH | 2h | ⏳ Pending |
| 9 | Documentation | 🟢 MEDIUM | 4h | ⏳ Pending |
| 10 | Production Deploy Configs | 🟡 HIGH | 6h | ⏳ Pending |

**Total Estimated Effort:** 39 hours (~1 week of focused development)

---

## Execution Order

### Day 1: Core Functionality
1. Fix analytics endpoint (Gap #1)
2. Implement real embeddings (Gap #2)
3. Fix streaming (Gap #3)

### Day 2: Email & Auth
4. Complete email implementation (Gap #4)
5. Add JWT authentication (Gap #5)

### Day 3: Testing
6. Create test infrastructure (Gap #6)
7. Write unit tests for core modules

### Day 4: Security & Frontend
8. Security hardening (CORS, input validation)
9. Connect dashboard to real data (Gap #8)

### Day 5: Documentation & Deployment
10. Write API documentation
11. Create Kubernetes configs
12. Create Terraform configs
13. Final testing and validation

---

*End of Gap Analysis*
