import time
import anthropic
from dotenv import load_dotenv
from metrics import agent_latency, tokens_used
from logger import log_agent_step

load_dotenv()
import os
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SKEPTIC_PROMPT = """You are a skeptical legal reviewer. Your job is to challenge legal reasoning 
on behalf of tenant rights — find weaknesses, gaps, and counterarguments.

You will be given:
1. A tenant's question
2. Legal context (statutes and guides)
3. An initial legal analysis

Your job:
1. Identify any counterarguments a landlord could make
2. Identify any conditions or exceptions in the law that could weaken the tenant's position
3. Identify anything the initial reasoning missed or overstated
4. Give a verdict: "reasoning stands" or "reasoning needs qualification"

Be concise. One paragraph maximum. If the reasoning is solid, say so briefly."""

def skeptic_agent(state: dict) -> dict:
    question = state["user_question"]
    context = state["formatted_context"]
    reasoning = state["legal_reasoning"]
    request_id = state.get("request_id", "unknown")

    start = time.time()
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SKEPTIC_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Legal context:\n{context}

Initial reasoning:\n{reasoning}

Tenant's question: {question}"""
        }]
    )

    latency = time.time() - start

    # record metrics
    agent_latency.labels(agent="skeptic").observe(latency)
    tokens_used.labels(agent="skeptic", token_type="input").inc(
        response.usage.input_tokens
    )
    tokens_used.labels(agent="skeptic", token_type="output").inc(
        response.usage.output_tokens
    )

    log_agent_step(
        request_id=request_id,
        agent="skeptic",
        latency_seconds=latency,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    
    skeptic_output = response.content[0].text
    
    # determine verdict from output
    verdict = "reasoning stands" if "stands" in skeptic_output.lower() else "reasoning needs qualification"
    
    print(f"  [Skeptic] Verdict: {verdict}")
    
    return {
        "counterarguments": skeptic_output,
        "skeptic_verdict": verdict
    }