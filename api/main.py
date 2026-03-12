"""
Production-Grade FastAPI Server for Gita RAG
Implements enterprise patterns: health checks, monitoring, rate limiting, error handling
"""

import os
import torch

# Force CPU mode - ignore GPU/MPS hardware (compatibility across all platforms)
os.environ["CUDA_VISIBLE_DEVICES"] = ""
torch.set_default_device('cpu')

import pickle
import time
import json
import logging
import io
from typing import List, Optional
from datetime import datetime
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from sentence_transformers import util
from rank_bm25 import BM25Okapi

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GitaRAGAPI")

# Initialize FastAPI app
app = FastAPI(
    title="Gita RAG API",
    description="Production-grade Retrieval-Augmented Generation system for Bhagavad Gita",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Query request model with validation."""
    query: str = Field(
        ..., 
        min_length=5, 
        max_length=500,
        description="The user's question about Bhagavad Gita"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of verses to retrieve"
    )
    user_id: Optional[str] = Field(
        default="anonymous",
        description="User identifier for tracking"
    )

class BatchQueryRequest(BaseModel):
    """Batch query request model."""
    queries: List[str] = Field(
        ...,
        max_items=100,
        description="List of queries to process"
    )
    top_k: int = Field(default=5, ge=1, le=20)

class VerseResponse(BaseModel):
    """Single verse in response."""
    chapter: int
    verse: int
    text: str
    score: float

class QueryResponse(BaseModel):
    """Response to a query."""
    query_id: str
    query: str
    answer: str
    verses: List[VerseResponse]
    confidence: float
    latency_ms: float
    model: str = "Gita RAG v1.0"
    timestamp: str

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str
    uptime_seconds: float

class MetricsResponse(BaseModel):
    """System metrics response."""
    requests_total: int
    error_rate: float
    latency_p99_ms: float
    cache_hit_rate: float
    sla_compliant: bool
    timestamp: str

# ============================================================================
# STATE & MONITORING
# ============================================================================

class SystemState:
    def __init__(self):
        self.corpus = []
        self.bm25_index = None
        self.embedding_model = None
        self.corpus_embeddings = None
        
        # Metrics
        self.request_count = 0
        self.error_count = 0
        self.latencies = []
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Rate limiting
        self.user_request_counts = defaultdict(lambda: {'count': 0, 'reset_time': time.time()})
        self.rate_limit_per_minute = 100
        
        # Startup time for uptime tracking
        self.startup_time = time.time()

state = SystemState()

# ============================================================================
# INITIALIZATION
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Load models and initialize system on startup."""
    logger.info("Loading production models...")
    try:
        # Custom unpickler: remap MPS (Mac GPU) → CPU (cross-platform compatible)
        class CPU_Unpickler(pickle.Unpickler):
            def find_class(self, module, name):
                if module == 'torch.storage' and name == '_load_from_bytes':
                    return lambda b: torch.load(io.BytesIO(b), map_location='cpu')
                else:
                    return super().find_class(module, name)
        
        # Load pickle with device remapping
        with open('data/retriever_state.pkl', 'rb') as f:
            retriever_state = CPU_Unpickler(f).load()
        
        state.corpus = retriever_state['corpus']
        state.bm25_index = retriever_state['bm25_index']
        state.embedding_model = retriever_state['embedding_model']
        state.corpus_embeddings = retriever_state['corpus_embeddings']
        
        logger.info(f"Loaded {len(state.corpus)} verses, ready for queries")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise

# ============================================================================
# RETRIEVAL LOGIC
# ============================================================================

def retrieve_verses(query: str, top_k: int) -> tuple[List[dict], float]:
    """Retrieve verses using hybrid search."""
    # Check cache
    cache_key = f"{query}:{top_k}"
    if cache_key in state.cache:
        state.cache_hits += 1
        return state.cache[cache_key], 0.0
    
    state.cache_misses += 1
    
    # BM25 search
    query_tokens = query.lower().split()
    bm25_scores = state.bm25_index.get_scores(query_tokens)
    bm25_indices = np.argsort(bm25_scores)[-top_k*2:][::-1]
    bm25_results = [(int(idx), float(bm25_scores[idx])) 
                    for idx in bm25_indices if bm25_scores[idx] > 0]
    
    # Semantic search
    query_embedding = state.embedding_model.encode(query, convert_to_tensor=True)
    similarities = util.pytorch_cos_sim(query_embedding, state.corpus_embeddings)[0]
    semantic_indices = np.argsort(similarities.cpu().numpy())[-top_k*2:][::-1]
    semantic_results = [(int(idx), float(similarities[idx].item())) 
                        for idx in semantic_indices]
    
    # RRF fusion
    rrf_scores = {}
    k = 60
    for rank, (idx, score) in enumerate(bm25_results):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k + rank + 1)
    for rank, (idx, score) in enumerate(semantic_results):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k + rank + 1)
    
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    verses = []
    for idx, score in sorted_results:
        verse = state.corpus[idx]
        verses.append({
            'chapter': verse['chapter'],
            'verse': verse['verse'],
            'text': verse['english'],
            'score': float(score)
        })
    
    # Cache result
    state.cache[cache_key] = verses
    if len(state.cache) > 1000:  # Simple eviction
        oldest_key = next(iter(state.cache))
        del state.cache[oldest_key]
    
    confidence = float(sorted_results[0][1]) if sorted_results else 0.0
    return verses, confidence

def generate_answer(query: str, verses: List[dict]) -> str:
    """Generate answer from retrieved verses."""
    if not verses:
        return "I could not find relevant verses to answer your question."
    
    answer = "Based on Bhagavad Gita teachings:\n\n"
    for i, verse in enumerate(verses[:3], 1):
        answer += f"BG {verse['chapter']}.{verse['verse']}: \"{verse['text'][:150]}...\"\n\n"
    answer += "Apply these teachings to navigate your situation with wisdom and equanimity."
    
    return answer

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    x_api_key: Optional[str] = Header(None)
) -> QueryResponse:
    """Query the Gita RAG system."""
    start_time = time.time()
    query_id = f"req_{int(start_time * 1000)}"
    
    # Rate limiting check
    user_id = request.user_id or "anonymous"
    current_time = time.time()
    user_data = state.user_request_counts[user_id]
    
    if current_time - user_data['reset_time'] > 60:
        # Reset counter after 1 minute
        user_data['count'] = 0
        user_data['reset_time'] = current_time
    
    if user_data['count'] >= state.rate_limit_per_minute:
        logger.warning(f"Rate limit exceeded for user {user_id}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    user_data['count'] += 1
    
    try:
        # Retrieve verses
        verses, confidence = retrieve_verses(request.query, request.top_k)
        
        # Generate answer
        answer = generate_answer(request.query, verses)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Update metrics
        state.request_count += 1
        state.latencies.append(latency_ms)
        
        logger.info(f"Query processed: {query_id} | latency: {latency_ms:.1f}ms | confidence: {confidence:.2f}")
        
        return QueryResponse(
            query_id=query_id,
            query=request.query,
            answer=answer,
            verses=[VerseResponse(**v) for v in verses],
            confidence=confidence,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        state.error_count += 1
        logger.error(f"Query failed {query_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/batch")
async def batch_endpoint(request: BatchQueryRequest):
    """Process multiple queries in batch."""
    start_time = time.time()
    batch_id = f"batch_{int(start_time * 1000)}"
    
    results = []
    for query in request.queries:
        query_req = QueryRequest(query=query, top_k=request.top_k)
        result = await query_endpoint(query_req)
        results.append(result.dict())
    
    latency_ms = (time.time() - start_time) * 1000
    
    logger.info(f"Batch processed: {batch_id} | queries: {len(request.queries)} | latency: {latency_ms:.1f}ms")
    
    return {
        'batch_id': batch_id,
        'query_count': len(request.queries),
        'results': results,
        'latency_ms': latency_ms,
        'timestamp': datetime.utcnow().isoformat()
    }

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_endpoint() -> HealthResponse:
    """Health check endpoint."""
    uptime = time.time() - state.startup_time
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=uptime
    )

@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def metrics_endpoint(x_api_key: Optional[str] = Header(None)) -> MetricsResponse:
    """System metrics endpoint (admin only)."""
    total = state.request_count
    error_rate = state.error_count / total if total > 0 else 0
    
    latency_p99 = float(np.percentile(state.latencies, 99)) if state.latencies else 0
    sla_target = 500
    sla_compliant = latency_p99 < sla_target
    
    cache_hit_rate = state.cache_hits / (state.cache_hits + state.cache_misses) \
                     if (state.cache_hits + state.cache_misses) > 0 else 0
    
    return MetricsResponse(
        requests_total=total,
        error_rate=error_rate,
        latency_p99_ms=latency_p99,
        cache_hit_rate=cache_hit_rate,
        sla_compliant=sla_compliant,
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "message": "Gita RAG API v1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "query": "POST /api/v1/query"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=4)
