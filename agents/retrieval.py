import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import agent_latency, retrieval_similarity
from retrieve import retrieve
import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")

CATEGORY_SEARCH_TERMS = {
    "security_deposit": "security deposit return timeline damages withheld",
    "eviction_and_notice": "eviction notice quit writ possession landlord procedure",
    "habitability_and_repairs": "habitability repairs heat hot water landlord duty maintain",
    "landlord_entry": "landlord entry notice permission 24 hours privacy quiet enjoyment",
    "lease_terms": "lease agreement terms conditions sublease provisions",
    "tenant_retaliation": "retaliation prohibited tenant complaint organizing",
    "rent_payment": "rent payment late fee increase",
    "general_rights": "tenant rights Pennsylvania landlord"
}

def retrieval_agent(state: dict) -> dict:
    question = state["user_question"]
    category = state.get("legal_category", "general_rights")
    
    # detect multi-issue questions — fetch more chunks
    multi_issue_indicators = ["and also", "as well as", "both", "two issues", 
                               "another problem", "on top of that"]
    is_multi_issue = any(phrase in question.lower() 
                         for phrase in multi_issue_indicators)
    top_k = 5 if is_multi_issue else 3
    
    enriched_query = f"{question} {CATEGORY_SEARCH_TERMS.get(category, '')}"
    
    collection = chroma_client.get_collection(name="tenant-rights")
    results = retrieve(enriched_query, collection, top_k=top_k)

    distances = results["distances"][0]
    for dist in distances:
        # Chroma returns distances — convert to similarity (1 - distance)
        similarity = 1 - dist
        retrieval_similarity.observe(similarity)
    
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    
    context_pieces = []
    sources = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        context_pieces.append(f"[Source {i+1}: {meta['source']}]\n{doc}")
        sources.append(meta['source'])
    
    formatted_context = "\n\n".join(context_pieces)
    print(f"  [Retrieval] Retrieved {len(documents)} chunks for category: {category}")
    
    return {
        "retrieved_chunks": documents,
        "retrieved_sources": sources,
        "formatted_context": formatted_context
    }