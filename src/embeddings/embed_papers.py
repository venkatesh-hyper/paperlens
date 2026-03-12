import sqlite3
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer
import time 

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DB_PATH = "data/papers.db"
IDS_PATH = "data/paper_ids.npy"
EMBEDDINGS_PATH = "data/embeddings.npy"
BATCH_SIZE = 64

def load_papers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id,abstract FROM papers")
    rows = cursor.fetchall()
    conn.close()
    logger.info(f"Loaded {len(rows)} papers from database")
    return rows

def generate_embeddings(papers):
    logger.info(f"Loading Model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    logger.success(f"Model loaded: {EMBEDDING_MODEL}")
    
    ids = [p[0] for p in papers]
    abstracts = [p[1] for p in papers]
    
    logger.info(f"embeddings for {len(abstracts)} papers...")
    start = time.time()
    
    embedding = model.encode(
        abstracts, 
        batch_size=BATCH_SIZE, 
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    
    elapsed = time.time() - start
    logger.success(f"Generated embeddings in {elapsed:.2f} seconds")
    logger.info(f"Shape:{embedding.shape}")
    logger.info(f"Dtype{embedding.dtype}")
    
    return ids, embedding

def save_embeddings(ids, embeddings):
    np.save(EMBEDDINGS_PATH, embeddings)
    np.save(IDS_PATH, np.array(ids))
    logger.success(f"Saved embeddings to {EMBEDDINGS_PATH} and IDs to {IDS_PATH}")    
    
def sanity_check(embeddings):
    
    v1 = embeddings[0]
    v2 = embeddings[1]
    v3 = embeddings[2]
    
    sim_close = np.dot(v1, v2)
    sim_far = np.dot(v1, v3)
    
    logger.info(f"Similarity (nearby papers): {sim_close:.4f}")
    logger.info(f"Similarity (distant papers): {sim_far:.4f}")
    logger.info("Higher = more similar")
    
def main():
    logger.info("🚀 Embedding pipeline starting...")

    papers = load_papers()

    if len(papers) == 0:
        logger.error("No papers found! Run fetch_papers.py first.")
        return

    ids, embeddings = generate_embeddings(papers)
    save_embeddings(ids, embeddings)

    logger.info("Running sanity check...")
    sanity_check(embeddings)

    # Verify saved correctly
    loaded = np.load(EMBEDDINGS_PATH)
    logger.success(f"Verified: {loaded.shape[0]} embeddings × {loaded.shape[1]} dimensions")
    logger.success(" Embedding pipeline complete!")
    logger.info("Next step: python src/embeddings/build_index.py")


if __name__ == "__main__":
    main()