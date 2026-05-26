import os
from dotenv import load_dotenv
import anthropic
import chromadb
from sentence_transformers import SentenceTransformer
from retrieve import retrieve

load_dotenv()

SYSTEM_PROMPT = """You are TenantIQ, a tenant rights advisor specializing in 
Pennsylvania landlord-tenant law, specifically for renters in Pittsburgh.

Your job is to help tenants understand their legal rights in plain, accessible 
language based on the legal context provided to you.

Rules you must follow:
1. Answer ONLY based on the legal context provided. Do not use outside knowledge.
2. If the provided context does not contain enough information to answer the 
   question, say clearly: "I don't have enough information in my current 
   knowledge base to answer this question. I recommend contacting a local 
   legal aid organization."
3. Always cite which section or source your answer comes from.
4. Be specific — tell the tenant exactly what the law says and what they can do.
5. Use plain language. Avoid legal jargon where possible.
6. Always end your response by noting you are not a lawyer and this is not 
   legal advice."""

def build_context(retrieved_results):
    # retrieved_results is the raw Chroma response object
    # need to extract documents and metadatas and format them clearly
    
    documents = retrieved_results["documents"][0]
    metadatas = retrieved_results["metadatas"][0]
    
    context_pieces = []
    for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
        # format each chunk clearly so Claude knows where it came from
        context_pieces.append(
            f"[Source {i+1}: {metadata['source']}]\n{doc}"
        )
    
    return "\n\n".join(context_pieces)


# RAG
def ask_tenantiq(question, collection, client, conversation_history):
    # step 1: retrieve relevant chunks
    retrieval_query = build_retrieval_query(question, conversation_history)
    retrieved = retrieve(retrieval_query, collection, top_k=3)
    
    # step 2: format chunks into context string
    context = build_context(retrieved)
    
    # step 3: build the user message that combines context + question
    # notice the structure — context first, then question
    # this is deliberate: Claude reads context before seeing the question
    user_message = f"""Here is the relevant legal context for your question:

{context}

Based only on the above legal context, please answer this question:
{question}"""
    
    # step 4: add to conversation history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # step 5: call Claude
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )
    
    answer = response.content[0].text
    
    # step 6: add Claude's response to history for follow-up questions
    conversation_history.append({
        "role": "assistant",
        "content": answer
    })
    
    return answer, context, conversation_history

import re

def build_retrieval_query(question, conversation_history):
    if len(conversation_history) == 0:
        return question
    
    vague_indicators = [
        "they", "it", "this", "that", "again", "more", "else",
        "what about", "and if", "what should i do", "how about",
        "do it", "can they", "will they", "if so"
    ]
    
    question_lower = question.lower()
    
    # use word boundaries so "it" doesn't match inside "without", "limit", etc.
    is_vague = any(
        re.search(r'\b' + re.escape(indicator) + r'\b', question_lower)
        for indicator in vague_indicators
    )
    
    if not is_vague:
        return question
    
    recent_context = ""
    for msg in reversed(conversation_history):
        if msg["role"] == "user":
            content = msg["content"]
            if "answer this question:" in content:
                content = content.split("answer this question:")[-1].strip()
            if content != question:
                recent_context = content[:150]
                break
    
    if recent_context:
        combined = f"{recent_context} {question}"
        print(f"  [Context-aware query: '{combined[:100]}...']")
        return combined
    
    return question

def main():
    # initialize everything
    client = anthropic.Anthropic()
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection(name="tenant-rights")
    conversation_history = []
    
    print("=" * 50)
    print("TenantIQ — Pennsylvania Tenant Rights Advisor")
    print("Type 'quit' to exit, 'new' to start a new conversation")
    print("=" * 50)
    
    while True:
        question = input("\nYou: ").strip()
        
        if question.lower() == "quit":
            break
        
        if question.lower() == "new":
            conversation_history = []
            print("Started new conversation.")
            continue
            
        if not question:
            continue
        
        print("\nSearching legal knowledge base...")
        
        answer, context, conversation_history = ask_tenantiq(
            question, 
            collection, 
            client,
            conversation_history
        )
        
        print(f"\nTenantIQ: {answer}")
        
        # optionally show what was retrieved — useful for debugging
        show_sources = input("\n[Show sources used? y/n]: ").strip().lower()
        if show_sources == "y":
            print("\n--- Sources Retrieved ---")
            print(context)
            print("------------------------")

if __name__ == "__main__":
    main()