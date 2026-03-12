import requests
import sqlite3
import time
from tqdm import tqdm
from loguru import logger

# ── CONFIG ──────────────────────────────────────
DB_PATH         = "data/papers.db"
DELAY           = 3
LIMIT_PER_QUERY = 100

QUERIES = [
    "machine learning",
    "deep learning",
    "natural language processing",
    "computer vision",
    "reinforcement learning",
    "transformer neural network",
    "large language models",
    "diffusion models",
    "graph neural network",
    "object detection",
    "semantic segmentation",
    "speech recognition",
    "knowledge graph",
    "federated learning",
    "autonomous driving",
    "medical image analysis",
    "neural architecture search",
    "contrastive learning",
    "zero shot learning",
    "multimodal learning",
]
# 20 queries × 100 = 2000 papers
# ────────────────────────────────────────────────

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def fetch_papers(query: str, limit: int = 100):
    papers = []
    offset = 0
    batch  = min(100, limit)

    while offset < limit:
        params = {
            "query":  query,
            "offset": offset,
            "limit":  batch,
            "fields": "paperId,title,abstract,authors,year,externalIds"
        }
        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)

            if resp.status_code == 429:
                logger.warning("Rate limited — waiting 30s...")
                time.sleep(30)
                continue

            resp.raise_for_status()
            data = resp.json().get("data", [])

            if not data:
                break

            papers.extend(data)
            offset += batch
            time.sleep(DELAY)

        except Exception as e:
            logger.error(f"Error fetching '{query}': {e}")
            break

    return papers


def parse_paper(paper: dict, query: str):
    try:
        abstract = paper.get("abstract") or ""
        title    = paper.get("title")    or ""

        if len(abstract) < 100 or not title:
            return None

        authors = ", ".join(
            a.get("name", "") for a in paper.get("authors", [])
        )

        ext_ids  = paper.get("externalIds") or {}
        arxiv_id = ext_ids.get("ArXiv", paper["paperId"])
        url      = f"https://arxiv.org/abs/{arxiv_id}" if ext_ids.get("ArXiv") \
                   else f"https://www.semanticscholar.org/paper/{paper['paperId']}"

        return {
            "id":       arxiv_id,
            "title":    title.strip().replace("\n", " "),
            "abstract": abstract.strip().replace("\n", " "),
            "authors":  authors,
            "year":     paper.get("year") or 2024,
            "field":    query,
            "url":      url,
        }
    except Exception as e:
        logger.warning(f"Skipped paper: {e}")
        return None


def save_papers(papers: list) -> int:
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    saved  = 0

    for p in papers:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO papers
                (id, title, abstract, authors, year, field, url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (p["id"], p["title"], p["abstract"],
                  p["authors"], p["year"], p["field"], p["url"]))
            saved += 1
        except Exception as e:
            logger.warning(f"Could not save: {e}")

    conn.commit()
    conn.close()
    return saved


def show_total():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM papers")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT field, COUNT(*) FROM papers GROUP BY field ORDER BY COUNT(*) DESC LIMIT 5")
    rows = cursor.fetchall()
    conn.close()

    logger.success(f"Total papers in database: {total}")
    print("\n── TOP FIELDS ────────────────────")
    for field, count in rows:
        print(f"  {field}: {count} papers")
    print("──────────────────────────────────")


def main():
    logger.info("🚀 Semantic Scholar ingestion starting...")
    logger.info(f"Fetching {len(QUERIES)} topics × {LIMIT_PER_QUERY} papers = {len(QUERIES)*LIMIT_PER_QUERY} papers")

    grand_total = 0

    for query in tqdm(QUERIES, desc="Topics"):
        logger.info(f"Fetching: '{query}'")
        raw_papers = fetch_papers(query, LIMIT_PER_QUERY)
        parsed     = [p for raw in raw_papers if (p := parse_paper(raw, query))]
        saved      = save_papers(parsed)
        grand_total += saved
        logger.success(f"'{query}' → {saved} papers saved")
        time.sleep(5)

    logger.success(f"✅ DONE! Added {grand_total} new papers")
    show_total()


if __name__ == "__main__":
    main()