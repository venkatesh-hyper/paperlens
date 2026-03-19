#  PaperLens

> Semantic search engine for research papers — find papers by meaning, not keywords.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com)
[![FAISS](https://img.shields.io/badge/FAISS-IVFFlat-orange.svg)](https://github.com/facebookresearch/faiss)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/venkatesh-hyper/paperlens/actions/workflows/ci.yml/badge.svg)](https://github.com/venkatesh-hyper/paperlens/actions)
[![HuggingFace](https://img.shields.io/badge/🤗%20Live%20Demo-HuggingFace-yellow)](https://huggingface.co/spaces/vengen9840/paperlens)

---

## 🎯 What is PaperLens?

A researcher reads one paper. PaperLens instantly finds 10 more papers with similar meaning — not keyword matching, but true **semantic understanding** using AI embeddings.

Type *"how transformers handle long sequences"* → PaperLens finds the right papers even if those exact words don't appear in the title or abstract.

Built on **42,549 real arXiv papers** across 8 scientific domains — CS, Biology, Physics, Statistics, Engineering, and Mathematics.

🔗 **[Live Demo → HuggingFace Spaces](https://paperlens-i.streamlit.app/)**

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Papers indexed | **42,549** (8 domains) |
| Embedding dimensions | 384 |
| FAISS index type | IVFFlat (nlist=50, nprobe=10) |
| p50 query latency | **0.31ms** |
| p95 query latency | **0.53ms** |
| min latency | 0.26ms |
| QPS | **2,979 queries/second** |
| Index size | 62.3 MB |
| Embedding time | 311.52 seconds (42,549 papers) |
| Cached search | 0.44ms (1,738× faster) |
| RAG summary latency | ~1,200ms (Groq LLaMA-3.3-70b) |
| Test suite | 27/27 passing |

---

## 🗂 Domains Indexed

| Domain | Category | Papers |
|--------|----------|--------|
| Artificial Intelligence | cs.AI | 5,000 |
| Machine Learning | cs.LG | 5,000 |
| Computation & Language (NLP) | cs.CL | 5,000 |
| Computer Vision | cs.CV | 5,000 |
| Information Retrieval | cs.IR | 5,000 |
| Neural & Evolutionary Computing | cs.NE | 5,000 |
| Robotics | cs.RO | 5,000 |
| Genomics | q-bio.GN | ~3,729 |
| + more fields in progress | q-bio.NC, stat.ML, eess.SP... | — |

---

## 🏗 Architecture

```
arXiv API → SQLite → sentence-transformers → FAISS Index → FastAPI → Streamlit
                                                    ↓
                                          Groq LLaMA-3.3-70b (RAG summaries)
```

| Layer | Tool | Purpose |
|-------|------|---------|
| Data Ingestion | requests + SQLite | Fetch and store papers from arXiv API |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Convert abstracts to 384-dim vectors |
| Vector Index | FAISS IVFFlat | Sub-millisecond approximate nearest neighbor search |
| API Backend | FastAPI + Uvicorn + LRU Cache | Serve search with caching |
| RAG | Groq LLaMA-3.3-70b | AI-generated paper summaries |
| Dashboard | Streamlit | User-facing search interface |
| MLOps | MLflow + Docker Compose | Experiment tracking + containerization |
| CI/CD | GitHub Actions | Automated test + lint pipeline |
| Deployment | HuggingFace Spaces (Docker) | Live demo hosting |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/venkatesh-hyper/paperlens.git
cd paperlens

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Run pipeline
python src/ingestion/fetch_papers.py      # fetch papers from arXiv
python src/embeddings/embed_papers.py     # generate embeddings
python src/embeddings/build_index.py      # build FAISS index

# Start API
uvicorn src.api.main:app --reload         # http://localhost:8000

# Start Dashboard
streamlit run src/dashboard/app.py        # http://localhost:8501
```

### Docker (recommended)

```bash
docker-compose up --build
# FastAPI  → http://localhost:8000
# Streamlit → http://localhost:8501
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Status, papers indexed, index loading state |
| `/search?query=...&top_k=10` | GET | Semantic search — returns top-k results with scores |
| `/papers/{id}` | GET | Full paper metadata from SQLite |
| `/summarize/{id}` | GET | LLaMA-3 RAG summary via Groq |

---

## 📁 Project Structure

```
paperlens/
├── src/
│   ├── ingestion/
│   │   ├── fetch_papers.py              # arXiv API pipeline (20 domains)
│   │   └── fetch_semantic_scholar.py    # Semantic Scholar API
│   ├── embeddings/
│   │   ├── embed_papers.py              # sentence-transformers inference
│   │   └── build_index.py              # FAISS IVFFlat index builder
│   ├── api/
│   │   ├── main.py                     # FastAPI app (4 endpoints)
│   │   ├── models.py                   # Pydantic response models
│   │   └── cache.py                    # LRU cache layer
│   ├── rag/
│   │   ├── pipeline.py                 # Groq LLaMA-3.3-70b RAG
│   │   └── prompts.py                  # System + user prompt templates
│   └── dashboard/
│       ├── app.py                      # Full Streamlit UI (local)
│       └── app_standalone.py           # HuggingFace Spaces version
├── tests/
│   └── test_api.py                     # 27/27 pytest tests passing
├── data/                               # papers.db, faiss_index.bin (gitignored)
├── Dockerfile.api                      # FastAPI container
├── Dockerfile.dashboard                # Streamlit container
├── Dockerfile.space                    # HuggingFace Spaces container
├── docker-compose.yml                  # Full stack in one command
├── download_data.py                    # Downloads data from HF Dataset at build time
├── .github/workflows/ci.yml            # GitHub Actions CI (test + lint)
└── DEVLOG.md                           # Day-by-day build journal
```

---

## 🛠 Tech Stack

- **Embeddings** — sentence-transformers/all-MiniLM-L6-v2
- **Vector Search** — FAISS IVFFlat (nlist=50, nprobe=10)
- **API** — FastAPI + Uvicorn + LRU Cache
- **RAG** — Groq LLaMA-3.3-70b (llama-3.3-70b-versatile)
- **Dashboard** — Streamlit with custom dark theme
- **MLOps** — MLflow + Docker Compose + GitHub Actions CI
- **Data** — arXiv API + Semantic Scholar API + SQLite
- **Deployment** — HuggingFace Spaces (Docker SDK)

---

## 📔 Dev Log

Built in public — one day at a time. Full journey in [DEVLOG.md](DEVLOG.md)

| Day | Built | Key Result |
|-----|-------|------------|
| Day 1 | Data ingestion — arXiv API pipeline | 1,854 papers in SQLite |
| Day 2 | FAISS index + benchmarks | p50=0.02ms, QPS=76,540 |
| Day 3 | FastAPI backend + RAG pipeline | 4 endpoints, Groq LLaMA-3 summaries |
| Day 4 | Portfolio + Resume rebuild | ATS-optimized resume, dark portfolio |
| Day 5 | Docker + Tests + CI/CD | 27/27 tests passing, CI green |
| Day 6 | HuggingFace deployment + Scale | 42,549 papers, live demo deployed |

---

## 👤 Author

**Venkatesh P** — ML Engineer  
MCA, University of Madras (2023–2025)

[LinkedIn](https://linkedin.com/in/venkatesh-ml) · [Portfolio](https://venkatesh-hyper.github.io/resume) · [GitHub](https://github.com/venkatesh-hyper) · [HuggingFace](https://huggingface.co/vengen9840)

---
