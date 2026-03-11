import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="PaperLens", page_icon="🔍", layout="wide")

# ── INIT SESSION STATE — MUST BE FIRST ───────────
if "summaries" not in st.session_state:
    st.session_state.summaries = {}
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# ── HELPERS ──────────────────────────────────────
def search_papers(query: str, top_k: int = 10):
    try:
        resp = requests.get(f"{API_BASE}/search", params={"query": query, "top_k": top_k}, timeout=30)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        st.error(f"Search failed: {e}")
        return None

def get_summary(paper_id: str):
    try:
        resp = requests.get(f"{API_BASE}/summarize/{paper_id}", timeout=30)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        st.error(f"Summary failed: {e}")
        return None

def check_api():
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        if resp.status_code == 200:
            return True, resp.json()
        return False, {}
    except:
        return False, {}

# ── HEADER ───────────────────────────────────────
st.markdown("# 🔍 PaperLens")
st.markdown("**Semantic search engine for research papers — find papers by meaning, not keywords**")
st.divider()

# ── API STATUS ───────────────────────────────────
is_up, health = check_api()
if is_up:
    st.markdown(
        f" **Online** &nbsp;|&nbsp; "
        f"**{health.get('paper_indexed', 0)} papers** &nbsp;|&nbsp; "
        f"**all-MiniLM-L6-v2** &nbsp;|&nbsp; "
        f"**FAISS IVFFlat** &nbsp;|&nbsp; "
        f"**Groq LLaMA-3.3-70b**",
        unsafe_allow_html=True
    )
else:
    st.error("❌ API offline — run: uvicorn src.api.main:app --reload")
    st.stop()

st.divider()

# ── SEARCH BAR ───────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("Search", placeholder="e.g. transformer attention mechanism...", label_visibility="collapsed")
with col2:
    top_k = st.selectbox("Results", [5, 10, 20], index=1, label_visibility="collapsed")

search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)

# ── SAVE RESULTS ON SEARCH ───────────────────────
if search_clicked and query.strip():
    with st.spinner("Searching..."):
        data = search_papers(query, top_k)
    st.session_state.search_results = data
    st.session_state.last_query = query

# ── DISPLAY RESULTS FROM SESSION STATE ───────────
data  = st.session_state.search_results
query = st.session_state.last_query

if data and data.get("results"):
    st.markdown(f"**{data['total']} results** for *\"{query}\"* — `{data['latency_ms']}ms`")
    st.divider()

    for i, paper in enumerate(data["results"]):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"### {i+1}. {paper['title']}")
        with col2:
            st.markdown(f"**Score:** `{paper['score']:.3f}`")

        st.markdown(
            f"{paper['authors'][:80]}{'...' if len(paper['authors']) > 80 else ''}  "
            f"|  {paper.get('year', 'N/A')}  |  `{paper.get('field', '')}`"
        )

        with st.expander("Abstract"):
            st.write(paper["abstract"])

        if st.button("🤖 AI Summary", key=f"sum_{paper['id']}_{i}"):
            with st.spinner("Groq LLaMA-3 reading the paper..."):
                summary = get_summary(paper["id"])
            if summary:
                st.session_state.summaries[paper["id"]] = summary

        if paper["id"] in st.session_state.summaries:
            s = st.session_state.summaries[paper["id"]]
            st.success(f"Generated in {s['latency_ms']}ms  |  Tokens: {s['tokens_used']}")
            st.markdown(s["summary"])

        st.markdown(f"[View on arXiv]({paper['url']})")
        st.divider()

# ── SIDEBAR ──────────────────────────────────────
with st.sidebar:
    st.markdown("## About PaperLens")
    st.markdown("""
    **Stack:**
    - sentence-transformers
    - FAISS IVFFlat
    - FastAPI + LRU cache
    - Groq LLaMA-3.3-70b
    - Streamlit
    
    **Benchmarks:**
    - 956 papers indexed
    - p50 latency: 0.02ms
    - QPS: 76,540
    - Cache: 1738x speedup
    """)
    st.divider()
    st.markdown("**Try these:**")
    st.code("transformer attention")
    st.code("reinforcement learning")
    st.code("computer vision CNN")
    st.code("large language models")
    st.divider()
    st.markdown("Built by [Venkatesh P](https://linkedin.com/in/venkatesh-ml)")