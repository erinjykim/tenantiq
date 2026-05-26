import time
import anthropic
from dotenv import load_dotenv
from metrics import agent_latency, tokens_used
from logger import log_agent_step

load_dotenv()
import os
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

REASONING_PROMPT = """You are a legal reasoning specialist for Pennsylvania tenant law.

You will be given:
1. A tenant's question
2. Relevant legal passages from Pennsylvania statutes and guides

Your job is to reason explicitly through the question in three steps:
STEP 1 - What the law says: Quote and explain the relevant legal rules from the provided context
STEP 2 - Applying law to facts: Map the legal rules to the tenant's specific situation  
STEP 3 - Likely outcome: What does this mean for the tenant's rights or next steps

CRITICAL RULES:
- Use ONLY information explicitly stated in the provided legal context
- If the context does not address something, say so — do not fill gaps with general knowledge
- Do not infer rules that are not directly stated in the passages
- If you are uncertain, say you are uncertain — never speculate about what the law might say
- Do not cite any statute section not mentioned in the provided context"""

def reasoning_agent(state: dict) -> dict:
    question = state["user_question"]
    context = state["formatted_context"]
    request_id = state.get("request_id", "unknown")

    start = time.time()
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=REASONING_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Legal context:\n{context}\n\nTenant's question: {question}"
        }]
    )

    latency = time.time() - start

    # record metrics
    agent_latency.labels(agent="reasoning").observe(latency)
    tokens_used.labels(agent="reasoning", token_type="input").inc(
        response.usage.input_tokens
    )
    tokens_used.labels(agent="reasoning", token_type="output").inc(
        response.usage.output_tokens
    )

    log_agent_step(
        request_id=request_id,
        agent="reasoning",
        latency_seconds=latency,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    
    reasoning = response.content[0].text
    print(f"  [Reasoning] Completed legal analysis")
    
    return {"legal_reasoning": reasoning}