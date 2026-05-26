Build the knowledge base:
```bash
python build_kb.py
```

Run the multi-agent advisor:
```bash
python main.py
```

Run as a REST API:
```bash
uvicorn server:app --port 8000
```

Run evaluation suite:
```bash
python eval.py
```

Bring up observability stack:
```bash
docker-compose up
```

---

## Tech Stack

- **Claude API** (Anthropic) — reasoning and generation across 5 specialized agents
- **LangGraph** — multi-agent state machine orchestration
- **Chroma** — local vector database for persistent embeddings
- **sentence-transformers** — local embedding model (all-MiniLM-L6-v2)
- **LangChain** — recursive character text splitting
- **FastAPI + uvicorn** — REST API and metrics endpoint
- **Prometheus + Grafana** — production observability
- **Docker Compose** — single-command infrastructure
- **GitHub Actions** — automated eval CI/CD pipeline
- **MCP** — Model Context Protocol server for Claude Desktop integration

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

---

## Business Context

44 million renter households in the US face legal situations they cannot afford to resolve — 97% of tenants go unrepresented while nearly all landlords have legal counsel. TenantIQ addresses this access gap by making legal knowledge instantly accessible.

Primary B2B customers: legal aid organizations and city housing authorities, who currently spend ~$400/case on manual intake that TenantIQ automates at near-zero marginal cost.