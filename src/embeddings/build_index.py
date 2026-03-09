import faiss
import numpy as np
import time
import json
from loguru import logger

# Config
IDS_PATH = "data/paper_ids.npy"
EMBEDDINGS_PATH = "data/embeddings.npy"
INDEX_PATH = "data/faiss_index.bin"
ID_MAP_PATH = "data/id_map.json"
NLIST = 50
NPROBE = 10

def load_embeddings():
    embeddings = np.load(EMBEDDINGS_PATH).astype('float32')
    ids = np.load(IDS_PATH, allow_pickle=True)
    logger.info(f"Loaded {len(ids)} IDs and embeddings with shape {embeddings.shape}")
    return embeddings, ids

def build_faiss_index(embeddings):
    dim = embeddings.shape[1] # 384
    logger.info(f"Building FAISS index with dimension {dim} and {NLIST} clusters...")
    
    #quantizer - finds nearest cluster 
    quantizer = faiss.IndexFlatIP(dim) # inner product for cosine similarity
    
    #index - stores embeddings in clusters
    index = faiss.IndexIVFFlat(quantizer, dim, NLIST, faiss.METRIC_INNER_PRODUCT)
    
    #train index on sample of embeddings
    logger.info("Training FAISS index...")
    start = time.time()
    index.train(embeddings)
    logger.success(f"Index trained in {time.time() - start:.2f} seconds")
    
    #add embeddings to index
    logger.info("Adding embeddings to FAISS index...")
    start = time.time()
    index.add(embeddings)
    logger.success(f"Added {index.ntotal} embeddings in {time.time() - start:.2f} seconds")
    
    index.nprobe = NPROBE
    logger.info(f"Set nprobe to {NPROBE} for search")
    return index

def save_index(index, ids):
    faiss.write_index(index, INDEX_PATH)
    logger.success(f"FAISS index saved to {INDEX_PATH}")
    
    #save ID to index mapping
    id_map = {i: str(id) for i, id in enumerate(ids)}
    with open(ID_MAP_PATH, 'w') as f:
        json.dump(id_map, f)
    logger.success(f"ID map saved to {ID_MAP_PATH}")
    
def benchmark_index(index, embeddings):
    logger.info("Running benchmark...")

    # Test with 10 queries
    query_vectors = embeddings[:10]
    k = 5  # top-5 results

    # Warmup
    index.search(query_vectors[:1], k)

    # Benchmark
    times = []
    for i in range(10):
        q = embeddings[i:i+1]
        start = time.time()
        distances, indices = index.search(q, k)
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)

    p50 = sorted(times)[4]
    p95 = sorted(times)[9]

    # QPS — run 1000 queries, measure total time
    repeated = np.tile(embeddings, (1000 // len(embeddings) + 1, 1))[:1000]
    start = time.time()
    for i in range(1000):
        index.search(repeated[i:i+1], k)
    qps = 1000 / (time.time() - start)

    logger.success(f"  p50 latency : {p50:.2f}ms")
    logger.success(f"  p95 latency : {p95:.2f}ms")
    logger.success(f"  min latency : {min(times):.2f}ms")
    logger.success(f"  max latency : {max(times):.2f}ms")
    logger.success(f"  QPS         : {qps:.0f} queries/second")

    return p50, p95, qps

def test_search(index, embeddings, ids):
    logger.info("Testing search functionality...")
    
    #search using first paper
    query = embeddings[0:1]
    distances, indices = index.search(query, 5)
    
    logger.info(f"Search results for query ID={ids[0]}:")
    for rank, (idx, dist) in enumerate(zip(indices[0], distances[0])):
        logger.info(f"  Rank {rank+1}: ID={ids[idx]}, Distance={dist:.4f}")
    
    
def main():
    logger.info("🚀 FAISS index building starting...")

    # Load
    embeddings, ids = load_embeddings()

    # Build
    index = build_faiss_index(embeddings)

    # Save
    save_index(index, ids)

    # Benchmark
    p50, p95, qps = benchmark_index(index, embeddings)

    # Test search quality
    test_search(index, embeddings, ids)

    logger.success("✅ FAISS index complete!")
    logger.info(f"Total vectors indexed: {index.ntotal}")
    logger.info(f"Index size: ~{index.ntotal * 384 * 4 / 1024 / 1024:.1f} MB")
    logger.info("Next step: python src/api/main.py")


if __name__ == "__main__":
    main()