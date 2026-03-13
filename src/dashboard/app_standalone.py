import streamlit as st
import sqlite3
import os

st.set_page_config(page_title="PaperLens", page_icon="🔬", layout="wide")

st.title("🔬 PaperLens")
st.caption("Semantic search over 1,854 arXiv papers · cs.AI · cs.LG · cs.CL")

query = st.text_input("Search papers...", placeholder="e.g. attention mechanism transformers")

@st.cache_resource
def load_resources():
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from huggingface_hub import hf_hub_download

    os.makedirs("data", exist_ok=True)
    for f in ["papers.db", "faiss_index.bin"]:
        if not os.path.exists(f"data/{f}"):
            hf_hub_download(repo_id="vengen9840/paperlens-data", filename=f, repo_type="dataset", local_dir="data")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index("data/faiss_index.bin")
    conn = sqlite3.connect("data/papers.db", check_same_thread=False)
    return model, index, conn

if query:
    import faiss
    import numpy as np
    with st.spinner("Loading model... (first time takes ~30s)"):
        model, index, conn = load_resources()
    vec = model.encode([query]).astype("float32")
    faiss.normalize_L2(vec)
    scores, indices = index.search(vec, 10)
    cur = conn.cursor()
    for score, idx in zip(scores[0], indices[0]):
        cur.execute("SELECT id, title, abstract, authors, published FROM papers WHERE rowid=?", (int(idx)+1,))
        row = cur.fetchone()
        if row:
            with st.expander(f"**{row[1]}** — {float(score):.3f}"):
                st.write(f"**Authors:** {row[3]}")
                st.write(f"**Published:** {row[4]}")
                st.write(str(row[2])[:500] + "...")
                st.link_button("View on arXiv", f"https://arxiv.org/abs/{row[0]}")
else:
    st.info("👆 Type a query above to search 1,854 arXiv papers.")