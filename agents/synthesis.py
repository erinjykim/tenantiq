import time
import anthropic
from dotenv import load_dotenv
from metrics import agent_latency, tokens_used
from logger import log_agent_step

load_dotenv()
import os
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYNTHESIS_PROMPT = """You are TenantIQ, a tenant rights advisor for Pennsylvania renters.

You will be given legal context, reasoning, and a skeptic review.

Write a clear, plain-language answer that:
- Directly answers the tenant's question in the first sentence
- Explains what the law says based ONLY on the provided context and reasoning
- Cites sources explicitly
- Tells them concrete next steps
- Ends with: "I am not a lawyer and this is not legal advice."

CRITICAL: Do not add any legal information not present in the provided context or reasoning.
If the context is insufficient to answer fully, say so clearly rather than filling gaps
with general knowledge. A partial honest answer is always better than a complete fabricated one.
Keep the response under 200 words unless complexity requires more."""

def synthesis_agent(state: dict) -> dict:
    question = state["user_question"]
    context = state["formatted_context"]
    reasoning = state["legal_reasoning"]
    counterarguments = state["counterarguments"]
    conversation_history = state.get("conversation_history", [])
    request_id = state.get("request_id", "unknown")

    start = time.time()
    
    # build conversation summary for context
    conversation_context = ""
    if conversation_history:
        recent = conversation_history[-4:]  # last 2 exchanges
        summary_parts = []
        for msg in recent:
            role = "Tenant" if msg["role"] == "user" else "TenantIQ"
            summary_parts.append(f"{role}: {msg['content'][:200]}")
        conversation_context = "\n\nPrior conversation:\n" + "\n".join(summary_parts)
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYNTHESIS_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Tenant's question: {question}{conversation_context}

Legal context:
{context}

Legal reasoning:
{reasoning}

Skeptic review:
{counterarguments}"""
        }]
    )

    latency = time.time() - start

    # record metrics
    agent_latency.labels(agent="synthesis").observe(latency)
    tokens_used.labels(agent="synthesis", token_type="input").inc(
        response.usage.input_tokens
    )
    tokens_used.labels(agent="synthesis", token_type="output").inc(
        response.usage.output_tokens
    )

    log_agent_step(
        request_id=request_id,
        agent="synthesis",
        latency_seconds=latency,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    
    final_answer = response.content[0].text
    print(f"  [Synthesis] Final answer generated")
    
    return {"final_answer": final_answer}