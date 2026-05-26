import json
import logging
import sys
from datetime import datetime, timezone

# configure python's logger to output raw JSON lines
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(message)s'  # just the message, no extra formatting
)
logger = logging.getLogger("tenantiq")

def log_agent_step(
    request_id: str,
    agent: str,
    latency_seconds: float,
    input_tokens: int = 0,
    output_tokens: int = 0,
    extra: dict = None
):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "agent": agent,
        "latency_seconds": round(latency_seconds, 3),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
    if extra:
        record.update(extra)
    
    logger.info(json.dumps(record))

def log_request_complete(
    request_id: str,
    total_latency: float,
    total_tokens: int,
    cost_usd: float,
    category: str
):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "event": "request_complete",
        "total_latency_seconds": round(total_latency, 3),
        "total_tokens": total_tokens,
        "cost_usd": round(cost_usd, 6),
        "category": category
    }
    logger.info(json.dumps(record))