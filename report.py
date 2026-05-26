import json

with open('eval_results.json') as f:
    data = json.load(f)

print("FAILED QUESTIONS:")
for r in data['results']:
    if not r['scores']['answer_correct']:
        print(f"\n{r['id']} — {r['question']}")
        print(f"Judge: {r['scores']['reasoning']}")

print("\nHALLUCINATIONS:")
for r in data['results']:
    if not r['scores']['hallucination_free']:
        print(f"\n{r['id']} — {r['question']}")
        print(f"Actual answer: {r['actual_answer'][:200]}")
        print(f"Judge: {r['scores']['reasoning']}")