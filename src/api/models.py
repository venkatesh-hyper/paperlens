from pydantic import BaseModel
from typing import Optional, List

class SearchRequest (BaseModel):
    query: str
    top_k: Optional[int] = 10
    
class PaperResult (BaseModel):
    id:str
    title: str
    authors: str
    abstract: str
    year :int
    field :str
    url: str
    score: float
 
 
class SearchResponse (BaseModel):
    query: str
    results: List[PaperResult]
    total:int
    latency_ms: float
    
class PaperDetail(BaseModel):
    id:str
    title: str
    authors: str
    abstract: str
    year:int
    field :str
    url: str
    
class HealthResponse(BaseModel):
    status: str
    paper_indexed: int
    index_loading:bool
    embedding_loading: bool
    