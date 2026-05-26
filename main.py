from dotenv import load_dotenv
from graph import tenantiq_graph
import uuid

load_dotenv()

def run_tenantiq(question: str, conversation_history: list, last_category: str = "") -> str:
    initial_state = {
        "request_id": str(uuid.uuid4())[:8],
        "user_question": question,
        "conversation_history": conversation_history,
        "legal_category": last_category,
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
    return result["final_answer"]


def main():
    conversation_history = []
    
    print("=" * 50)
    print("TenantIQ — Pennsylvania Tenant Rights Advisor")
    print("Multi-agent system powered by LangGraph")
    print("Type 'quit' to exit, 'new' to start fresh")
    print("=" * 50)
    
    last_category = ""

    while True:
        question = input("\nYou: ").strip()
        
        if question.lower() in ["quit", "exit", "q", "bye"]:
            break
        if question.lower() == "new":
            conversation_history = []
            last_category = ""
            print("Started new conversation.")
            continue
        if not question:
            continue
        
        print("\nRunning multi-agent pipeline...")
        
        answer, last_category = run_tenantiq(question, conversation_history, last_category)
        
        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": answer})
        
        print(f"\nTenantIQ: {answer}")

if __name__ == "__main__":
    main()