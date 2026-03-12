import hashlib
from loguru import logger

_cache = {}
MAX_CACHE_SIZE = 512

def _make_key(query: str, top_k:int) -> str:
    raw  = f"{query.lower().strip()}:{top_k}"
    return hashlib.sha256(raw.encode()).hexdigest()

def get_cached_response(query: str, top_k: int):
    key = _make_key(query, top_k)
    if key in _cache:
        logger.info(f"Cache hit for query: '{query}' with top_k={top_k}")
        return _cache.get(key)
    logger.info(f"Cache miss for query: '{query}' with top_k={top_k}")
    return None

def set_cache(query: str, top_k: int, results: dict):
    if len(_cache) >= MAX_CACHE_SIZE:
         # Remove oldest entry
        oldest = next(iter(_cache))
        del _cache[oldest]
        logger.info("Cache full — evicted oldest entry")
        
    key = _make_key(query, top_k)
    _cache[key] = results
    logger.info(f"Cache SET — '{query}' ({len(_cache)}/{MAX_CACHE_SIZE})")
    
def cache_stats() -> dict:
    return {
        "cache_size": len(_cache),
        "max_cache_size": MAX_CACHE_SIZE,
        "hit_rate": "tracked per request in logs",  
    }
    
    