import streamlit as st
import sqlite3
import os
import requests
from typing import Optional, Tuple, Any

st.set_page_config(
    page_title="PaperLens",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if "summaries" not in st.session_state:
    st.session_state.summaries = {}

# ── CSS OVERRIDES ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:       #0c0c0c;
    --surface:  #141414;
    --surface2: #1a1a1a;
    --border:   #2a2a2a;
    --accent:   #00ff88;
    --accent2:  #ff6b35;
    --accent3:  #4d9eff;
    --text:     #f0f0f0;
    --muted:    #666;
    --dim:      #2a2a2a;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--bg) !important;
    font-family: 'IBM Plex Sans', sans-serif;
    color: var(--text);
}
[data-testid="stSidebar"]    { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"]     { background: transparent !important; }

.block-container { padding: 1rem 1.5rem !important; max-width: 100% !important; }

/* ── TOPBAR ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.9rem 0 1.2rem;
    border-bottom: 1px solid var(--dim);
    margin-bottom: 1.5rem;
}
.topbar-logo {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1rem;
    font-weight: 600;
    color: var(--accent);
    letter-spacing: 3px;
    text-transform: uppercase;
}
.topbar-logo span { color: #444; }
.topbar-pills { display: flex; gap: 0.5rem; align-items: center; }
.tpill {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    padding: 4px 12px;
    border-radius: 2px;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.tpill.green  { background: rgba(0,255,136,0.1); color: var(--accent);  border: 1px solid rgba(0,255,136,0.3); }
.tpill.orange { background: rgba(255,107,53,0.1); color: var(--accent2); border: 1px solid rgba(255,107,53,0.3); }
.tpill.blue   { background: rgba(77,158,255,0.1); color: var(--accent3); border: 1px solid rgba(77,158,255,0.3); }

/* ── HERO ── */
.hero { margin-bottom: 2rem; }
.hero-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--muted);
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.hero-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 4rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1;
    margin-bottom: 0.5rem;
}
.hero-title .accent { color: var(--accent); }
.hero-sub {
    font-size: 1rem;
    color: var(--muted);
    font-weight: 300;
    margin-bottom: 1.4rem;
}
.hero-stats-row {
    display: flex;
    gap: 2.5rem;
    padding: 1.2rem 0;
    border-top: 1px solid var(--dim);
    border-bottom: 1px solid var(--dim);
    margin-bottom: 1.8rem;
}
.hstat-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--accent);
    line-height: 1;
}
.hstat-label {
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 4px;
}

/* ── SEARCH ── */
.search-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
div[data-testid="stTextInput"] input {
    background: var(--surface2) !important;
    border: 1px solid var(--dim) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1rem !important;
    padding: 0.85rem 1.2rem !important;
    transition: border-color 0.15s;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0,255,136,0.08) !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #444 !important; }

/* ── RESULT HEADER ── */
.result-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: var(--muted);
    margin: 1.2rem 0;
    display: flex;
    gap: 2rem;
    align-items: center;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid var(--dim);
}
.result-meta .hi { color: var(--accent); }

/* ── PAPER CARD ── */
.paper-card {
    background: var(--surface);
    border: 1px solid var(--dim);
    border-left: 3px solid #2a2a2a;
    border-radius: 3px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: border-left-color 0.15s;
    position: relative;
}
.paper-card:hover { border-left-color: var(--accent); background: #161616; }
.paper-card.top1  { border-left-color: var(--accent); }
.rank-badge {
    position: absolute;
    top: 1.1rem; right: 1.2rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--muted);
}
.rank-badge .score { color: var(--accent); font-weight: 600; }
.paper-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1.45;
    margin-bottom: 0.6rem;
    padding-right: 5rem;
}
.paper-chips {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 0.8rem;
}
.chip {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    padding: 3px 10px;
    border-radius: 2px;
    border: 1px solid var(--dim);
    color: var(--muted);
}
.chip.field { color: var(--accent3); border-color: rgba(77,158,255,0.3); background: rgba(77,158,255,0.05); }
.chip.year  { color: var(--accent2); border-color: rgba(255,107,53,0.3); background: rgba(255,107,53,0.05); }
.paper-abstract {
    font-size: 0.875rem;
    color: #888;
    line-height: 1.75;
    margin-bottom: 1rem;
}
.paper-footer {
    display: flex;
    gap: 1rem;
    align-items: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
}
.paper-authors { color: var(--muted); flex: 1; }
.arxiv-btn {
    color: var(--accent);
    text-decoration: none;
    border: 1px solid rgba(0,255,136,0.3);
    padding: 4px 14px;
    border-radius: 2px;
    transition: background 0.15s;
    white-space: nowrap;
}
.arxiv-btn:hover { background: rgba(0,255,136,0.1); }

/* ── AI BOX ── */
.ai-box {
    background: #0a1a12;
    border: 1px solid rgba(0,255,136,0.2);
    border-radius: 3px;
    padding: 1.1rem 1.3rem;
    margin-top: 0.9rem;
}
.ai-box-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: var(--accent);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.ai-box-text { font-size: 0.9rem; color: #aaa; line-height: 1.75; }

/* ── EMPTY STATE ── */
.empty-state { text-align: center; padding: 6rem 2rem; }
.empty-mono {
    font-family: 'IBM Plex Mono', monospace;
    color: #333;
    font-size: 0.9rem;
    line-height: 2.2;
}
.empty-prompt { color: var(--accent); }
.suggestions-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    justify-content: center;
    margin-top: 1.8rem;
}
.sug {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    border: 1px solid var(--dim);
    padding: 6px 14px;
    border-radius: 2px;
}

/* ── RIGHT PANEL ── */
.bench-panel {
    background: var(--surface);
    border: 1px solid var(--dim);
    border-radius: 4px;
    padding: 1.4rem;
    height: 100%;
}
.bench-brand {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1;
    margin-bottom: 2px;
}
.bench-brand .acc { color: var(--accent); }
.bench-tagline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--dim);
}
.bench-section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    color: var(--accent);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin: 1.2rem 0 0.6rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid var(--dim);
}
.brow {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 0.28rem 0;
    border-bottom: 1px solid #1c1c1c;
}
.bkey { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: var(--muted); }
.bval { font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; font-weight: 600; }
.bval.g { color: var(--accent); }
.bval.o { color: var(--accent2); }
.bval.b { color: var(--accent3); }
.bval.w { color: var(--text); }

.lat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem; margin-top: 0.4rem; }
.lat-cell {
    background: var(--surface2);
    border: 1px solid var(--dim);
    border-radius: 2px;
    padding: 0.5rem 0.6rem;
}
.lat-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.6rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
.lat-val   { font-family: 'IBM Plex Mono', monospace; font-size: 1rem; font-weight: 600; color: var(--accent); margin-top: 2px; }

.qps-box {
    background: rgba(0,255,136,0.05);
    border: 1px solid rgba(0,255,136,0.2);
    border-radius: 3px;
    padding: 0.9rem;
    text-align: center;
    margin-top: 0.5rem;
}
.qps-num   { font-family: 'IBM Plex Mono', monospace; font-size: 1.8rem; font-weight: 600; color: var(--accent); }
.qps-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; color: var(--muted); letter-spacing: 2px; text-transform: uppercase; margin-top: 2px; }

.trow {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.74rem;
    color: var(--muted);
    padding: 0.22rem 0;
}
.tdot { width: 5px; height: 5px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }

.by-name    { font-family: 'IBM Plex Mono', monospace; font-size: 0.88rem; font-weight: 600; color: var(--text); margin-bottom: 3px; }
.by-role    { font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: var(--accent); }
.by-sub     { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: var(--muted); }
.by-links   { display: flex; gap: 0.5rem; margin-top: 0.7rem; }
.by-link {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: var(--accent3);
    text-decoration: none;
    border: 1px solid rgba(77,158,255,0.3);
    padding: 3px 12px;
    border-radius: 2px;
}
.by-link:hover { background: rgba(77,158,255,0.1); }

/* Streamlit overrides */
[data-testid="stSpinner"] > div {
    color: var(--accent) !important;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
}
.stAlert {
    background: var(--surface2) !important;
    border-color: var(--dim) !important;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
}
button[data-testid="stBaseButton-secondary"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    background: var(--surface2) !important;
    border: 1px solid var(--dim) !important;
    color: var(--muted) !important;
    border-radius: 2px !important;
    padding: 0.4rem 1rem !important;
    transition: border-color 0.15s, color 0.15s;
}
button[data-testid="stBaseButton-secondary"]:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Groq Summary Function ─────────────────────────────────────────────────────
def get_summary(paper_id: str, title: str, abstract: str) -> Optional[str]:
    """Fetches a summarized version of the paper abstract using Groq's LLaMA-3."""
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content":
                    f"Summarize this arXiv paper in 3-4 sentences for an ML engineer. "
                    f"Focus on: problem, method, key results.\n\nTitle: {title}\nAbstract: {abstract}\n\nSummary:"}],
                "max_tokens": 200, "temperature": 0.3,
            }, timeout=15,
        )
        
        # Handle Rate Limits Gracefully
        if r.status_code == 429:
            st.warning("Groq rate limit reached. Please try again in a minute.")
            return None
            
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
        
    except requests.exceptions.Timeout:
        st.error("Groq API timed out. The model is currently overloaded.")
        return None
    except Exception as e:
        st.error(f"Groq API Error: {e}")
        return None


# ── Resources Loader ──────────────────────────────────────────────────────────
@st.cache_resource
def load_resources() -> Tuple[Any, Any, sqlite3.Connection, Any]:
    """Downloads DB and Vector Index from HuggingFace and loads them into memory."""
    import faiss
    from sentence_transformers import SentenceTransformer
    from huggingface_hub import hf_hub_download
    
    os.makedirs("data", exist_ok=True)
    for f in ["papers.db", "faiss_index.bin"]:
        if not os.path.exists(f"data/{f}"):
            hf_hub_download(repo_id="vengen9840/paperlens-data", filename=f,
                            repo_type="dataset", local_dir="data")
                            
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index("data/faiss_index.bin")
    conn  = sqlite3.connect("data/papers.db", check_same_thread=False)
    
    return model, index, conn, faiss


# ── TOPBAR ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='topbar'>
    <div class='topbar-logo'>Paper<span>Lens</span></div>
    <div class='topbar-pills'>
        <span class='tpill green'>● Live</span>
        <span class='tpill blue'>cs.AI · cs.LG · cs.CL</span>
        <span class='tpill orange'>Groq LLaMA-3</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── LAYOUT COLUMNS ────────────────────────────────────────────────────────────
left, right = st.columns([2.8, 1], gap="large")

# ════════════════════════════════
# RIGHT — BENCHMARKS
# ════════════════════════════════
with right:
    st.subheader("arXiv Semantic Search • Benchmarks")
    
    st.divider()
    
    # --- Index Stats Section ---
    st.subheader("Index Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Papers indexed**")
        st.write("**Vectors indexed**")
        st.write("**Index type**")
        st.write("**Dimensions**")
    with col2:
        st.write(":green[10,200]")
        st.write("956")
        st.write(":blue[IVFFlat]")
        st.write("384")
    
    st.divider()

    # --- Latency Section ---
    st.subheader("Latency")
    l_col1, l_col2 = st.columns(2)
    l_col1.metric("p50", "0.02ms")
    l_col1.metric("min", "0.01ms")
    l_col2.metric("p95", "0.02ms")
    l_col2.metric("max", "0.03ms")

    st.divider()

    # --- Throughput Section ---
    st.subheader("Throughput")
    st.info("76,540 queries / second")

    st.divider()

    # --- Tech Stack Section ---
    st.subheader("Tech Stack")
    stack = [
        "sentence-transformers", "FAISS • IVFFlat", 
        "all-MiniLM-L6-v2", "SQLite", "Groq LLaMA-3", 
        "HuggingFace Hub", "arXiv API • Streamlit"
    ]
    for item in stack:
        st.markdown(f"● {item}")

    st.divider()

    # --- Built By Section ---
    st.subheader("Built By")
    st.markdown("**Venkatesh P**")
    st.caption("ML Engineer • Chennai")
    st.caption("MCA • University of Madras")
    
    btn_col1, btn_col2 = st.columns(2)
    btn_col1.link_button("GitHub", "https://github.com/vengen9840")
    btn_col2.link_button("LinkedIn", "https://linkedin.com/in/venkateshp")


# ════════════════════════════════
# LEFT — SEARCH + RESULTS
# ════════════════════════════════
with left:
    st.markdown("""
    <div class='hero'>
        <div class='hero-eyebrow'>arXiv Semantic Search Engine</div>
        <div class='hero-title'>Paper<span class='accent'>Lens</span></div>
        <div class='hero-sub'>Search with meaning · not with keywords</div>
        <div class='hero-stats-row'>
            <div><div class='hstat-val'>10,200</div><div class='hstat-label'>Papers</div></div>
            <div><div class='hstat-val'>76K</div><div class='hstat-label'>QPS</div></div>
            <div><div class='hstat-val'>0.02ms</div><div class='hstat-label'>p50 Latency</div></div>
            <div><div class='hstat-val'>384d</div><div class='hstat-label'>Embeddings</div></div>
            <div><div class='hstat-val'>IVFFlat</div><div class='hstat-label'>Index</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='search-eyebrow'>Search Query</div>", unsafe_allow_html=True)
    query = st.text_input(
        label="query", label_visibility="collapsed",
        placeholder="e.g. attention mechanism · diffusion models · federated learning ...",
    )

    if query:
        with st.spinner("› encoding + searching..."):
            model, index, conn, faiss = load_resources()
            vec = model.encode([query]).astype("float32")
            faiss.normalize_L2(vec)
            scores, indices = index.search(vec, 10)

        st.markdown(
            f"<div class='result-meta'>"
            f"<span>results <span class='hi'>10</span></span>"
            f"<span>query <span class='hi'>\"{query}\"</span></span>"
            f"<span>model <span class='hi'>MiniLM-L6-v2</span></span>"
            f"</div>",
            unsafe_allow_html=True
        )

        cur = conn.cursor()
        results_found = False
        
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
            cur.execute(
                "SELECT id, title, abstract, authors, year, field, url FROM papers WHERE rowid=?",
                (int(idx) + 1,)
            )
            row = cur.fetchone()
            if not row:
                continue

            results_found = True
            paper_id, title, abstract, authors, year, field, url = row
            arxiv_url   = url or f"https://arxiv.org/abs/{paper_id}"
            abstract_txt = str(abstract or "")
            top_cls      = "top1" if rank == 1 else ""

            st.markdown(f"""
            <div class='paper-card {top_cls}'>
                <div class='rank-badge'>#{rank} · <span class='score'>{float(score):.3f}</span></div>
                <div class='paper-title'>{title or 'Untitled'}</div>
                <div class='paper-chips'>
                    <span class='chip field'>{field or 'cs.AI'}</span>
                    <span class='chip year'>{year or 'N/A'}</span>
                </div>
                <div class='paper-abstract'>{abstract_txt[:420]}...</div>
                <div class='paper-footer'>
                    <span class='paper-authors'>{(authors or 'N/A')[:75]}{'...' if len(authors or '')>75 else ''}</span>
                    <a class='arxiv-btn' href='{arxiv_url}' target='_blank'>arXiv →</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

            has_groq = bool(os.environ.get("GROQ_API_KEY", ""))
            already_done = paper_id in st.session_state.summaries

            if not already_done:
                btn_label = "🤖 AI Summary" if has_groq else "🤖 AI Summary (needs GROQ_API_KEY)"
                
                # Render Button
                if st.button(btn_label, key=f"sum_btn_{paper_id}_{rank}"):
                    if not has_groq:
                        st.warning("Add GROQ_API_KEY in Streamlit Cloud → Settings → Secrets")
                    else:
                        with st.spinner("LLaMA-3 reading..."):
                            result = get_summary(paper_id, title, abstract_txt)
                            
                        if result:
                            st.session_state.summaries[paper_id] = result
                            st.rerun()

            if already_done:
                st.markdown(f"""
                <div class='ai-box'>
                    <div class='ai-box-header'>🤖 LLaMA-3 · Groq</div>
                    <div class='ai-box-text'>{st.session_state.summaries[paper_id]}</div>
                </div>
                """, unsafe_allow_html=True)

        # Handle case where FAISS returns indices but SQLite has no corresponding records
        if not results_found:
            st.info("No matching metadata found in the database. Ensure your SQLite DB and FAISS index are synced.")

    else:
        st.markdown("""
        <div class='empty-state'>
            <div class='empty-mono'>
                <span class='empty-prompt'>›</span> paperlens.search(<span class='empty-prompt'>query</span>)<br>
                <span style='color:#2a2a2a'>  // 10,200 arXiv papers indexed</span><br>
                <span style='color:#2a2a2a'>  // cs.AI · cs.LG · cs.CL</span><br>
                <span style='color:#2a2a2a'>  // FAISS IVFFlat · 76K QPS · 0.02ms p50</span>
            </div>
            <div class='suggestions-wrap'>
                <span class='sug'>attention mechanism</span>
                <span class='sug'>GAN image synthesis</span>
                <span class='sug'>BERT pretraining</span>
                <span class='sug'>RL policy gradient</span>
                <span class='sug'>knowledge graphs</span>
                <span class='sug'>contrastive learning</span>
                <span class='sug'>diffusion models</span>
                <span class='sug'>LLM fine-tuning</span>
            </div>
        </div>
        """, unsafe_allow_html=True)