# TenantIQ — AI Tenant Rights Advisor

> A production-grade multi-agent legal advisory system for Pennsylvania tenant rights.

🚀 **Live Demo:** https://tenantiq-6gluhwvttq-uc.a.run.app/docs  
📊 **API Docs:** https://tenantiq-6gluhwvttq-uc.a.run.app/docs  
☁️ **Deployed on:** Google Cloud Run via Terraform

---

## Overview

44 million renter households in the US face legal situations they cannot afford to resolve — 97% of tenants go unrepresented while nearly all landlords have legal counsel. TenantIQ addresses this access gap by making legal knowledge instantly accessible.

A 5-agent LangGraph pipeline (intake → retrieval → reasoning → skeptic → synthesis) answers tenant rights questions grounded in Pennsylvania housing statutes, achieving **96% answer accuracy** and **4% hallucination rate** evaluated via LLM-as-judge across 25 curated ground-truth Q&A pairs.

Primary B2B customers: legal aid organizations and city housing authorities, who currently spend ~$400/case on manual intake that TenantIQ automates at near-zero marginal cost.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────┐
│ Intake Agent│  — classifies query category (deposit, eviction, habitability...)
└──────┬──────┘
       │
    ▼
┌──────────────────┐
│ Retrieval Agent  │  — semantic search over 661 chunks, cosine dedup (0.95 threshold)
└──────┬───────────┘
       │
    ▼
┌──────────────────┐
│ Reasoning Agent  │  — applies statute to user facts, step-by-step
└──────┬───────────┘
       │
    ▼
┌──────────────────┐
│ Skeptic Agent    │  — adversarially challenges reasoning, surfaces counterarguments
└──────┬───────────┘
       │
    ▼
┌──────────────────┐
│ Synthesis Agent  │  — final answer with citations, confidence, next steps
└──────────────────┘
```

---

## Evaluation Results

| Metric | Score |
|---|---|
| Answer accuracy | 96% |
| Citation accuracy | 91% |
| Hallucination rate | 4% |
| p50 latency | ~1.2s |
| p95 latency | ~3.8s |

Evaluated via LLM-as-judge across 25 curated ground-truth Q&A pairs drawn directly from Pennsylvania housing statutes.

---

## Quickstart

**Build the knowledge base:**
```bash
python build_kb.py
```

**Run the multi-agent advisor:**
```bash
python main.py
```

**Run as a REST API:**
```bash
uvicorn server:app --port 8000
```

**Run evaluation suite:**
```bash
python eval.py
```

**Bring up observability stack:**
```bash
docker-compose up
```

---

## Cloud Deployment

TenantIQ is deployed to Google Cloud Run. Infrastructure is managed via Terraform:

```bash
cd infra/
terraform init
terraform apply
```

The Terraform config provisions the Cloud Run service, sets resource limits (1Gi memory, 1 vCPU), and configures public IAM access. See `/infra/main.tf` for the full configuration.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Reasoning & generation | Claude API (Anthropic) |
| Agent orchestration | LangGraph |
| Vector database | Chroma |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Text splitting | LangChain recursive character splitter |
| API layer | FastAPI + uvicorn |
| Observability | Prometheus + Grafana |
| Infrastructure | Docker Compose |
| CI/CD | GitHub Actions (automated eval pipeline) |
| Cloud deployment | Google Cloud Run |
| Infrastructure-as-code | Terraform |
| Agent integration | MCP (Model Context Protocol) server |

---

## CI/CD Eval Pipeline

Every PR to `main` triggers an automated evaluation run via GitHub Actions:
- Runs 25 ground-truth Q&A pairs through the full agent pipeline
- Scores answer correctness, citation accuracy, and hallucination rate via LLM-as-judge
- Compares against baseline metrics
- **Blocks merge** if hallucination rate exceeds 10% or p95 latency degrades >20%

---

## Observability

Production metrics exposed via Prometheus and visualized in Grafana:
- Per-agent latency histograms
- Token throughput counters
- Cost-per-request gauge
- Retrieval similarity score distribution

```bash
docker-compose up   # starts app + Prometheus + Grafana
```

Grafana dashboard available at `localhost:3000`.

---

## MCP Server

TenantIQ's legal retrieval is exposed as a Model Context Protocol (MCP) server, enabling direct integration with Claude Desktop and any MCP-compatible client:

```
Tools available:
- search_tenant_law(query, category) → list[LegalPassage]
- get_statute(citation) → StatuteText
```

---

## Planned Features

**In progress:**
- Streamlit web UI
- Pinecone migration for multi-state deployment

**Planned:**
- Jurisdiction detection for automatic state routing
- Lease PDF upload with two-layer PII scrubbing (regex + spaCy NER)
- Expanding knowledge base to cover New York and California tenant law

**Known limitations:**
- Scoped to Pennsylvania law only (Pittsburgh focus for MVP)
- Knowledge base reflects documents as of April 2026
- Not a substitute for legal advice — designed to triage and inform, not replace an attorney
