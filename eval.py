import json
import time
import anthropic
from dotenv import load_dotenv
from main import run_tenantiq

load_dotenv()
import os
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

JUDGE_PROMPT = """You are an expert evaluator for a legal AI system focused on 
Pennsylvania tenant rights law.

You will be given:
1. A tenant's question
2. The expected correct answer (drawn from PA statutes)
3. The system's actual answer

Score the system's answer on three dimensions, each 0 or 1:

answer_correct: 1 if the answer correctly applies the law and reaches the right conclusion, 0 if wrong or misleading
citation_accurate: 1 if the answer cites a real, relevant source (doesn't have to be exact wording), 0 if no citation or wrong source
hallucination_free: 1 if the answer contains no fabricated legal facts not supported by the expected answer, 0 if it invents statutes or facts

Respond ONLY with valid JSON, no other text:
{
    "answer_correct": 0 or 1,
    "citation_accurate": 0 or 1,
    "hallucination_free": 0 or 1,
    "reasoning": "one sentence explaining your scores"
}"""

def judge_answer(question: str, expected: str, expected_citation: str, actual: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=256,
        system=JUDGE_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Question: {question}

Expected answer: {expected}
Expected citation: {expected_citation}

System's actual answer: {actual}"""
        }]
    )
    
    raw = response.content[0].text.strip()
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return {
            "answer_correct": 0,
            "citation_accurate": 0,
            "hallucination_free": 0,
            "reasoning": "Failed to parse judge response"
        }

def run_evaluation(eval_set_path: str = "eval_set.json") -> dict:
    with open(eval_set_path, "r") as f:
        eval_set = json.load(f)
    
    print(f"Running evaluation on {len(eval_set)} questions...\n")
    
    results = []
    latencies = []
    
    for i, item in enumerate(eval_set):
        print(f"[{i+1}/{len(eval_set)}] {item['id']}: {item['question'][:60]}...")
        
        # time the full pipeline
        start = time.time()
        actual_answer = run_tenantiq(item["question"], conversation_history=[])
        latency = time.time() - start
        latencies.append(latency)
        
        # judge the answer
        scores = judge_answer(
            question=item["question"],
            expected=item["expected_answer"],
            expected_citation=item.get("expected_citation", ""),
            actual=actual_answer
        )
        
        result = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "expected_answer": item["expected_answer"],
            "actual_answer": actual_answer,
            "latency_seconds": round(latency, 2),
            "scores": scores
        }
        results.append(result)
        
        status = "✓" if scores["answer_correct"] else "✗"
        print(f"  {status} correct={scores['answer_correct']} citation={scores['citation_accurate']} hallucination_free={scores['hallucination_free']} ({latency:.1f}s)")
        print(f"  Judge: {scores['reasoning']}\n")
    
    # compute aggregate metrics
    n = len(results)
    answer_accuracy = sum(r["scores"]["answer_correct"] for r in results) / n * 100
    citation_accuracy = sum(r["scores"]["citation_accurate"] for r in results) / n * 100
    hallucination_rate = (1 - sum(r["scores"]["hallucination_free"] for r in results) / n) * 100
    
    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[n // 2]
    p95 = latencies_sorted[int(n * 0.95)]
    
    # break down accuracy by category
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"correct": 0, "total": 0}
        categories[cat]["total"] += 1
        categories[cat]["correct"] += r["scores"]["answer_correct"]
    
    category_breakdown = {
        cat: f"{v['correct']}/{v['total']} ({v['correct']/v['total']*100:.0f}%)"
        for cat, v in categories.items()
    }
    
    summary = {
        "total_questions": n,
        "answer_accuracy_pct": round(answer_accuracy, 1),
        "citation_accuracy_pct": round(citation_accuracy, 1),
        "hallucination_rate_pct": round(hallucination_rate, 1),
        "latency_p50_seconds": round(p50, 2),
        "latency_p95_seconds": round(p95, 2),
        "category_breakdown": category_breakdown
    }
    
    # save full results
    output = {"summary": summary, "results": results}
    with open("eval_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    # print human readable summary
    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"{'Metric':<30} {'Score'}")
    print("-" * 50)
    print(f"{'Answer accuracy':<30} {answer_accuracy:.1f}%")
    print(f"{'Citation accuracy':<30} {citation_accuracy:.1f}%")
    print(f"{'Hallucination rate':<30} {hallucination_rate:.1f}%")
    print(f"{'Mean latency (p50)':<30} {p50:.2f}s")
    print(f"{'Mean latency (p95)':<30} {p95:.2f}s")
    print("\nBy category:")
    for cat, score in category_breakdown.items():
        print(f"  {cat:<28} {score}")
    print("=" * 50)
    print(f"\nFull results saved to eval_results.json")
    
    return output

if __name__ == "__main__":
    run_evaluation()