import streamlit as st
import sqlite3
import os

st.set_page_config(
    page_title="PaperLens",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #0a0e1a;
    --surface:   #111827;
    --border:    #1e2d45;
    --accent:    #38bdf8;
    --accent2:   #818cf8;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --success:   #34d399;
    --tag-bg:    #1e3a5f;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Header */
.hero {
    padding: 2.5rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.hero-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.6rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -1px;
    margin: 0;
}
.hero-sub {
    color: var(--muted);
    font-size: 0.95rem;
    margin-top: 0.3rem;
    font-family: 'Space Mono', monospace;
}
.hero-badges {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.9rem;
    flex-wrap: wrap;
}
.badge {
    background: var(--tag-bg);
    color: var(--accent);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.5px;
}
.badge.green  { color: var(--success); background: #0d2e22; border-color: #1a4a38; }
.badge.purple { color: var(--accent2); background: #1e1b4b; border-color: #312e81; }

/* Stats bar */
.stats-bar {
    display: flex;
    gap: 2rem;
    padding: 1rem 1.4rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 1.8rem;
}
.stat { text-align: center; }
.stat-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent);
}
.stat-label {
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
}

/* Search */
.search-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.4rem;
}

div[data-testid="stTextInput"] input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.1) !important;
}

/* Result count */
.result-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}
.result-header span { color: var(--accent); }

/* Paper card */
.paper-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s, transform 0.1s;
    position: relative;
}
.paper-card:hover {
    border-color: var(--accent);
    transform: translateY(-1px);
}
.score-pill {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.3);
    color: var(--accent);
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 20px;
}
.paper-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    margin: 0 0 0.5rem 0;
    padding-right: 4rem;
    line-height: 1.4;
}
.paper-meta {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 0.8rem;
}
.meta-item {
    font-size: 0.8rem;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 4px;
}
.meta-item .val { color: var(--text); font-weight: 500; }
.field-tag {
    display: inline-block;
    background: var(--tag-bg);
    color: var(--accent);
    border: 1px solid rgba(56,189,248,0.2);
    border-radius: 4px;
    font-size: 0.72rem;
    padding: 1px 8px;
    font-family: 'Space Mono', monospace;
}
.abstract {
    font-size: 0.875rem;
    color: #94a3b8;
    line-height: 1.65;
    margin-top: 0.8rem;
    border-top: 1px solid var(--border);
    padding-top: 0.8rem;
}
.arxiv-link {
    display: inline-block;
    margin-top: 0.8rem;
    color: var(--accent);
    font-size: 0.8rem;
    font-family: 'Space Mono', monospace;
    text-decoration: none;
    border: 1px solid rgba(56,189,248,0.3);
    padding: 3px 12px;
    border-radius: 4px;
    transition: background 0.2s;
}
.arxiv-link:hover { background: rgba(56,189,248,0.1); }

/* Empty state */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--muted);
}
.empty-icon { font-size: 3rem; margin-bottom: 1rem; }
.empty-title {
    font-family: 'Space Mono', monospace;
    font-size: 1rem;
    color: var(--text);
    margin-bottom: 0.5rem;
}
.suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: center;
    margin-top: 1.2rem;
}
.suggestion {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-family: 'Space Mono', monospace;
}

/* Sidebar */
.sidebar-section {
    background: #0f1929;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.sidebar-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.6rem;
}
.sidebar-text {
    font-size: 0.82rem;
    color: var(--muted);
    line-height: 1.6;
}
.tech-stack {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.5rem;
}
.tech-pill {
    background: #1e2d45;
    color: var(--accent2);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.72rem;
    font-family: 'Space Mono', monospace;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Streamlit overrides */
[data-testid="stSpinner"] > div { color: var(--accent) !important; }
.stAlert { background: var(--surface) !important; border-color: var(--border) !important; }
button[kind="primary"] {
    background: var(--accent) !important;
    color: #0a0e1a !important;
    border: none !important;
    font-family: 'Space Mono', monospace !important;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class='sidebar-section'>
        <div class='sidebar-title'>🔬 About PaperLens</div>
        <div class='sidebar-text'>
            A semantic search engine for arXiv research papers.
            Unlike keyword search, PaperLens understands the <em>meaning</em>
            of your query and returns conceptually relevant papers.
        </div>
    </div>

    <div class='sidebar-section'>
        <div class='sidebar-title'>⚙️ How It Works</div>
        <div class='sidebar-text'>
            1. Your query is encoded into a <strong>384-dim vector</strong> using a Sentence Transformer.<br><br>
            2. <strong>FAISS</strong> performs approximate nearest-neighbour search across all paper embeddings.<br><br>
            3. Top-10 most semantically similar papers are returned instantly.
        </div>
    </div>

    <div class='sidebar-section'>
        <div class='sidebar-title'>🛠 Tech Stack</div>
        <div class='tech-stack'>
            <span class='tech-pill'>sentence-transformers</span>
            <span class='tech-pill'>FAISS</span>
            <span class='tech-pill'>SQLite</span>
            <span class='tech-pill'>Streamlit</span>
            <span class='tech-pill'>all-MiniLM-L6-v2</span>
            <span class='tech-pill'>HuggingFace Hub</span>
            <span class='tech-pill'>arXiv API</span>
        </div>
    </div>

    <div class='sidebar-section'>
        <div class='sidebar-title'>💡 Try These Queries</div>
        <div class='sidebar-text'>
            • attention mechanism transformers<br>
            • federated learning privacy<br>
            • graph neural networks<br>
            • diffusion models image generation<br>
            • reinforcement learning robotics<br>
            • large language model fine-tuning
        </div>
    </div>

    <div class='sidebar-section'>
        <div class='sidebar-title'>👤 Built By</div>
        <div class='sidebar-text'>
            <strong style='color:#e2e8f0'>Venkatesh P</strong><br>
            MCA · University of Madras<br>
            <span style='color:#38bdf8'>ML Engineer</span> · Chennai, India<br><br>
            <a href='https://github.com/vengen9840' style='color:#818cf8'>GitHub</a> &nbsp;·&nbsp;
            <a href='https://linkedin.com/in/venkateshp' style='color:#818cf8'>LinkedIn</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero'>
    <p class='hero-title'> PaperLens</p>
    <p class='hero-sub'>search with meaning not with keywords</p>
    <p class='hero-sub'>Semantic search engine for arXiv research papers</p>
    <div class='hero-badges'>
        <span class='badge'>cs.AI</span>
        <span class='badge'>cs.LG</span>
        <span class='badge'>cs.CL</span>
        <span class='badge green'>● Live</span>
        <span class='badge purple'>FAISS · MiniLM-L6-v2</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Stats Bar ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class='stats-bar'>
    <div class='stat'><div class='stat-value'>1,854</div><div class='stat-label'>Papers Indexed</div></div>
    <div class='stat'><div class='stat-value'>384</div><div class='stat-label'>Embedding Dims</div></div>
    <div class='stat'><div class='stat-value'>MiniLM</div><div class='stat-label'>Encoder Model</div></div>
    <div class='stat'><div class='stat-value'>FAISS</div><div class='stat-label'>Vector Search</div></div>
    <div class='stat'><div class='stat-value'>Top-10</div><div class='stat-label'>Results Returned</div></div>
</div>
""", unsafe_allow_html=True)


# ── Search Input ──────────────────────────────────────────────────────────────
st.markdown("<div class='search-label'>Search Query</div>", unsafe_allow_html=True)
query = st.text_input(
    label="query",
    label_visibility="collapsed",
    placeholder="e.g. attention mechanism in transformers, graph neural networks, diffusion models...",
)


# ── Resource Loader ───────────────────────────────────────────────────────────
@st.cache_resource
def load_resources():
    import faiss
    from sentence_transformers import SentenceTransformer
    from huggingface_hub import hf_hub_download

    os.makedirs("data", exist_ok=True)
    for f in ["papers.db", "faiss_index.bin"]:
        if not os.path.exists(f"data/{f}"):
            hf_hub_download(
                repo_id="vengen9840/paperlens-data",
                filename=f,
                repo_type="dataset",
                local_dir="data"
            )
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index("data/faiss_index.bin")
    conn = sqlite3.connect("data/papers.db", check_same_thread=False)
    return model, index, conn, faiss


# ── Results ───────────────────────────────────────────────────────────────────
if query:
    with st.spinner("Encoding query and searching..."):
        model, index, conn, faiss = load_resources()
        vec = model.encode([query]).astype("float32")
        faiss.normalize_L2(vec)
        scores, indices = index.search(vec, 10)

    st.markdown(
        f"<div class='result-header'>Showing <span>10 results</span> for: <span>\"{query}\"</span></div>",
        unsafe_allow_html=True
    )

    cur = conn.cursor()
    for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
        cur.execute(
            "SELECT id, title, abstract, authors, year, field, url FROM papers WHERE rowid=?",
            (int(idx) + 1,)
        )
        row = cur.fetchone()
        if row:
            paper_id, title, abstract, authors, year, field, url = row
            arxiv_url = url or f"https://arxiv.org/abs/{paper_id}"
            abstract_preview = str(abstract or "")[:400] + "..."

            st.markdown(f"""
            <div class='paper-card'>
                <span class='score-pill'>#{rank} · {float(score):.3f}</span>
                <p class='paper-title'>{title or 'Untitled'}</p>
                <div class='paper-meta'>
                    <span class='meta-item'>✍️ <span class='val'>{(authors or 'N/A')[:60]}{'...' if len(authors or '') > 60 else ''}</span></span>
                    <span class='meta-item'>📅 <span class='val'>{year or 'N/A'}</span></span>
                    <span class='field-tag'>{field or 'cs.AI'}</span>
                </div>
                <div class='abstract'>{abstract_preview}</div>
                <a class='arxiv-link' href='{arxiv_url}' target='_blank'>→ View on arXiv</a>
            </div>
            """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div class='empty-state'>
        <div class='empty-icon'>🔭</div>
        <div class='empty-title'>Search 1,854 arXiv papers semantically</div>
        <div class='sidebar-text'>Enter a concept, topic, or research question above</div>
        <div class='suggestions'>
            <span class='suggestion'>attention mechanism</span>
            <span class='suggestion'>GAN image synthesis</span>
            <span class='suggestion'>BERT pretraining</span>
            <span class='suggestion'>RL policy gradient</span>
            <span class='suggestion'>knowledge graphs</span>
            <span class='suggestion'>contrastive learning</span>
        </div>
    </div>
    """, unsafe_allow_html=True)