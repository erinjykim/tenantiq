from typing import TypedDict, Optional, List

class TenantIQState(TypedDict):
    # input
    request_id: str
    user_question: str
    conversation_history: List[dict]
    
    # intake agent output
    legal_category: str          # "security_deposit", "eviction", "habitability", etc.
    category_confidence: str     # "high", "medium", "low"
    
    # retrieval agent output
    retrieved_chunks: List[str]
    retrieved_sources: List[str]
    formatted_context: str
    
    # reasoning agent output
    legal_reasoning: str         # step-by-step application of law to facts
    
    # skeptic agent output
    counterarguments: str        # what the landlord could argue
    skeptic_verdict: str         # "reasoning stands", "reasoning revised"
    
    # synthesis agent output
    final_answer: str