import sqlite3
import faiss
import numpy as np
import time
import json
from oauthlib.uri_validate import query
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from loguru import logger
from functools import lru_cache
from src.api.cache import get_cached_response , set_cache


from src.api.models import (
    SearchResponse, PaperResult, PaperDetail, HealthResponse
)

#config
DB_PATH         = "data/papers.db"
INDEX_PATH      = "data/faiss_index.bin"
EMBEDDINGS_PATH = "data/embeddings.npy"
ID_MAP_PATH     = "data/id_map.json"
MODEL_NAME      = "all-MiniLM-L6-v2"
NPROBE          = 10


# global state 
state = {
    "index": None,
    "id_map": None,
    "model": None,
    "db_conn": None,
    "n_papers": 0,
    
}


@asynccontextmanager

async def lifespan(app: FastAPI):
    #start
    logger.info("Starting up API...")
    
    # Load FAISS index
    logger.info("Loading FAISS index...")
    state["index"] = faiss.read_index(INDEX_PATH)
    state["index"].nprobe = NPROBE
    logger.info(f"FAISS index loaded with {state['index'].ntotal} vectors.")
    
    #loading sentence transformer model
    logger.info("Loading sentence transformer model...")
    state["model"] = SentenceTransformer(MODEL_NAME)
    logger.success("Sentence transformer model loaded successfully.")
    
    # Load ID map
    logger.info("Loading ID map...")
    with open(ID_MAP_PATH, "r") as f:
        state["id_map"] = json.load(f)
    logger.success(f"ID map loaded — {len(state['id_map'])} entries ✓")
    
    # Connect to SQLite database
    logger.info("Connecting to SQLite database...")
    state["db_conn"] = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = state["db_conn"].cursor()
    cursor.execute("SELECT COUNT(*) FROM papers")
    state["n_papers"] = cursor.fetchone()[0]
    logger.success(f"Connected to SQLite database with {state['n_papers']} papers ✓")
    
    logger.info("API startup complete.")
    yield
    
    #shutdown
    logger.info("Shutting down API...")
    if state["db_conn"]:
        state["db_conn"].close()
        logger.info("SQLite connection closed.")
    logger.info("API shutdown complete.")   
    
    
#APP  
app = FastAPI(title="Paperlens API",
                description="Semantic search engine for research papers",
                  version="1.0",
                  lifespan=lifespan,
                  )
    
    
#helper
def get_paper_by_id(paper_id: str) -> dict | None:
    cursor = state["db_conn"].cursor()
    cursor.execute(
        "SELECT id, title, authors, abstract, year, field, url FROM papers WHERE id = ?", (paper_id,)
        )
    row = cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "title": row[1],
            "authors":row[2],
            "abstract": row[3],
            "year": row[4],
            "field": row[5],
            "url": row[6]
        }
    return None
    
#endpoints
@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        paper_indexed=state["n_papers"],
        index_loading=state["index"] is not None,
        embedding_loading=state["model"] is not None
    )
    
@lru_cache(maxsize=512)
def embed_query(query: str):
    return state["model"].encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True
    ).astype("float32")
       
@app.get("/search", response_model=SearchResponse)
def search(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(10, ge=1, le=50, description="Number of top results to return")
):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    start = time.time()
    
    cached = get_cached_response(query, top_k)
    if cached:
        return cached
    
    start = time.time()
    
    # 1 - Embed the query
    query_vector = embed_query(query)
    
    # 2 - Search FAISS index
    distances, indices = state["index"].search(query_vector, top_k)
    
    # 3 - Fetch paper details from DB   
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx == -1:
            continue
        paper_id = state["id_map"].get(str(idx))
        if not paper_id:
            continue
        paper = get_paper_by_id(paper_id)
        if not paper:
            continue
        results.append(PaperResult(**paper, score= float(dist)))
        
    latency_ms = (time.time() - start) * 1000
    logger.info(f"Search completed in {latency_ms:.2f} ms with {len(results)} results.")
    
    return SearchResponse(
        query=query,
        results=results,
        total=len(results),
        latency_ms=round(latency_ms,3),
    )
    
    set_cache(query, top_k, SearchResponse)
    
    return response
    
    @app.get("/papers/{paper_id}", response_model=PaperDetail)
    def get_paper(paper_id: str):
        paper = get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return PaperDetail(**paper) 
    
    