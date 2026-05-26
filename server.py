import uuid
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import make_asgi_app
from dotenv import load_dotenv

from graph import tenantiq_graph
from metrics import cost_per_request, request_total, request_errors
from logger import log_request_complete

load_dotenv()

app = FastAPI(title="TenantIQ API")

metrics_app = make_asgi_app()
app.mount("/metrics/", metrics_app)

# claude pricing as of 2026 (per million tokens)
PRICING = {
    "claude-opus-4-5": {"input": 15.0, "output": 75.0},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25}
}

class QueryRequest(BaseModel):
    question: str
    conversation_history: list = []
    last_category: str = ""

class QueryResponse(BaseModel):
    answer: str
    request_id: str
    category: str

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    request_total.inc()
    
    try:
        initial_state = {
            "request_id": request_id,
            "user_question": request.question,
            "conversation_history": request.conversation_history,
            "legal_category": request.last_category,
            "category_confidence": "",
            "retrieved_chunks": [],
            "retrieved_sources": [],
            "formatted_context": "",
            "legal_reasoning": "",
            "counterarguments": "",
            "skeptic_verdict": "",
            "final_answer": ""
        }
        
        result = tenantiq_graph.invoke(initial_state)
        total_latency = time.time() - start
        
        # estimate cost — rough calculation from token counters
        # in production you'd track this per-request more precisely
        estimated_cost = 0.001  # placeholder — refine with actual token tracking
        cost_per_request.set(estimated_cost)
        
        log_request_complete(
            request_id=request_id,
            total_latency=total_latency,
            total_tokens=0,  # sum from agent logs
            cost_usd=estimated_cost,
            category=result.get("legal_category", "unknown")
        )
        
        return QueryResponse(
            answer=result["final_answer"],
            request_id=request_id,
            category=result.get("legal_category", "unknown")
        )
    
    except Exception as e:
        request_errors.inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}