import json
import os
import sys

with open("eval_results.json") as f:
    current = json.load(f)["summary"]

with open("baseline.json") as f:
    baseline = json.load(f)

acc_delta = current["answer_accuracy_pct"] - baseline["answer_accuracy_pct"]
hall_delta = current["hallucination_rate_pct"] - baseline["hallucination_rate_pct"]
p95_delta = current["latency_p95_seconds"] - baseline["latency_p95_seconds"]
cite_delta = current["citation_accuracy_pct"] - baseline["citation_accuracy_pct"]

def fmt_delta(val, invert=False):
    sign = "+" if val > 0 else ""
    emoji = "✅" if (val <= 0 if invert else val >= 0) else "⚠️"
    return f"{sign}{val:.1f} {emoji}"

comment = f"""## 📊 TenantIQ Eval Results

| Metric | This PR | Baseline | Δ |
|--------|---------|----------|---|
| Answer accuracy | {current['answer_accuracy_pct']:.1f}% | {baseline['answer_accuracy_pct']:.1f}% | {fmt_delta(acc_delta)} |
| Citation accuracy | {current['citation_accuracy_pct']:.1f}% | {baseline['citation_accuracy_pct']:.1f}% | {fmt_delta(cite_delta)} |
| Hallucination rate | {current['hallucination_rate_pct']:.1f}% | {baseline['hallucination_rate_pct']:.1f}% | {fmt_delta(hall_delta, invert=True)} |
| Latency p50 | {current['latency_p50_seconds']:.2f}s | {baseline['latency_p50_seconds']:.2f}s | {fmt_delta(current['latency_p50_seconds'] - baseline['latency_p50_seconds'], invert=True)} |
| Latency p95 | {current['latency_p95_seconds']:.2f}s | {baseline['latency_p95_seconds']:.2f}s | {fmt_delta(p95_delta, invert=True)} |

"""

failures = []
if current["hallucination_rate_pct"] > 10:
    failures.append(f"Hallucination rate {current['hallucination_rate_pct']:.1f}% exceeds 10% threshold")

p95_degradation = (p95_delta / baseline["latency_p95_seconds"]) * 100
if p95_degradation > 20:
    failures.append(f"p95 latency degraded by {p95_degradation:.1f}% (threshold: 20%)")

if failures:
    comment += "### ❌ Pipeline Failed\n"
    for f in failures:
        comment += f"- ❌ {f}\n"
else:
    comment += "### ✅ All quality gates passed\n"

print(comment)

with open("eval_comment.md", "w") as f:
    f.write(comment)

github_output = os.environ.get("GITHUB_OUTPUT", "")
if github_output:
    with open(github_output, "a") as f:
        f.write(f"failed={'true' if failures else 'false'}\n")
        f.write(f"failures={'; '.join(failures)}\n")

if failures:
    sys.exit(1)