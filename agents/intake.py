import time
import anthropic
import json
import re
from dotenv import load_dotenv
from metrics import agent_latency, tokens_used, query_category
from logger import log_agent_step

load_dotenv()
import os
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

VAGUE_INDICATORS = [
    "it", "this", "that", "they", "again", "more", "else",
    "what about", "and if", "what should i do", "how about",
    "do it", "can they", "will they", "if so", "about it"
]

LEGAL_CATEGORIES = [
    "security_deposit",
    "eviction_and_notice", 
    "habitability_and_repairs",
    "landlord_entry",
    "lease_terms",
    "tenant_retaliation",
    "rent_payment",
    "general_rights"
]

INTAKE_PROMPT = """You are a legal intake classifier for a tenant rights system.

Your job is to classify the user's question into exactly ONE of these legal categories:
- security_deposit: questions about deposits, withholding, return timelines, deductions
- eviction_and_notice: eviction process, notice to quit, writ of possession, timelines
- habitability_and_repairs: heat, hot water, mold, repairs, uninhabitable conditions
- landlord_entry: unauthorized entry, notice requirements, privacy rights
- lease_terms: lease agreements, subletting, pet policies, lease violations
- tenant_retaliation: landlord retaliation for complaints or organizing
- rent_payment: rent amount, late fees, rent increases
- general_rights: anything else not fitting the above

Respond ONLY with a valid JSON object in this exact format, no other text:
{
  "category": "<one of the categories above>",
  "confidence": "<high|medium|low>",
  "key_facts": "<one sentence summarizing what the tenant is actually asking>"
}"""

def is_vague_question(question: str) -> bool:
    question_lower = question.lower()
    return any(
        re.search(r'\b' + re.escape(indicator) + r'\b', question_lower)
        for indicator in VAGUE_INDICATORS
    )

def intake_agent(state: dict) -> dict:
    question = state["user_question"]
    request_id = state.get("request_id", "unknown")
    existing_category = state.get("legal_category", "")
    
    # if question is vague and we have a prior category, keep it
    if is_vague_question(question) and existing_category and existing_category != "general_rights":
        print(f"  [Intake] Vague follow-up — keeping category: {existing_category}")
        return {
            "legal_category": existing_category,
            "category_confidence": "high"
        }
    
    start = time.time()
    
    # otherwise classify fresh
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=INTAKE_PROMPT,
        messages=[{"role": "user", "content": question}]
    )

    latency = time.time() - start

    # record metrics
    agent_latency.labels(agent="intake").observe(latency)
    tokens_used.labels(agent="intake", token_type="input").inc(
        response.usage.input_tokens
    )
    tokens_used.labels(agent="intake", token_type="output").inc(
        response.usage.output_tokens
    )
    
    raw = response.content[0].text.strip()
    
    try:
        clean = re.sub(r'```json|```', '', raw).strip()
        result = json.loads(clean)
        category = result.get("category", "general_rights")
        confidence = result.get("confidence", "low")
    except json.JSONDecodeError:
        category = "general_rights"
        confidence = "low"
    
    # record category distribution
    query_category.labels(category=category).inc()
    
    # structured log
    log_agent_step(
        request_id=request_id,
        agent="intake",
        latency_seconds=latency,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        extra={"category": category, "confidence": confidence}
    )
    
    print(f"  [Intake] Category: {category} (confidence: {confidence})")
    
    return {
        "legal_category": category,
        "category_confidence": confidence
    }