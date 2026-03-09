import requests
import sqlite3
import time
import xml.etree.ElementTree as ET
from tqdm import tqdm
from loguru import logger


#config
FIELDS = [
    "cs.AI",   # Artificial Intelligence
    "cs.LG",   # Machine Learning
    "cs.CL",   # Computation and Language (NLP)
]
PAPERS_PER_FIELD = 400   # 400 × 3 = 1200 papers
DB_PATH          = "data/papers.db"
DELAY_SECONDS    = 10   # wait 10 seconds between requests


def create_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id       TEXT PRIMARY KEY,
            title    TEXT NOT NULL,
            abstract TEXT NOT NULL,
            authors  TEXT,
            year     INTEGER,
            field    TEXT,
            url      TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logger.success("Database created successfully.")
    
def fetch_papers(field, max_results = PAPERS_PER_FIELD):
        base_url = "http://export.arxiv.org/api/query?"
        papers = [] 
        batch_size = 100
        
        for start in tqdm(range(0, max_results, batch_size), desc=f"Fetching papers for {field}"):
            params = {
                "search_query": f"cat:{field}",
                "start": start,
                "max_results": batch_size,
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            }
            try:
                resp = requests.get(base_url, params=params, timeout=30)
                resp.raise_for_status()
                papers.extend(parse_xml(resp.text, field))
                time.sleep(3) # to respect arXiv's rate limits
            except Exception as e:
                logger.error(f"Error fetching papers for {field}: {e}")
                continue
        return papers
    
def parse_xml(xml_text, field):
    papers = []
    root   = ET.fromstring(xml_text)
    ns     = {"atom": "http://www.w3.org/2005/Atom"}

    for entry in root.findall("atom:entry", ns):
        try:
            paper_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
            title    = entry.find("atom:title",   ns).text.strip().replace("\n", " ")
            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            year     = int(entry.find("atom:published", ns).text[:4])
            url      = f"https://arxiv.org/abs/{paper_id}"
            authors  = ", ".join(
                a.find("atom:name", ns).text
                for a in entry.findall("atom:author", ns)
            )

            if len(abstract) < 100:   # skip junk entries
                continue

            papers.append({
                "id":       paper_id,
                "title":    title,
                "abstract": abstract,
                "authors":  authors,
                "year":     year,
                "field":    field,
                "url":      url,
            })
        except Exception as e:
            logger.warning(f"Skipped entry: {e}")
            continue

    return papers


def save_papers(papers):
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
            logger.warning(f"Could not save {p['id']}: {e}")

    conn.commit()
    conn.close()
    return saved


def show_sample():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT title, authors, year, field FROM papers LIMIT 5"
    )
    rows = cursor.fetchall()
    conn.close()

    print("\n── SAMPLE PAPERS ─────────────────────────────")
    for title, authors, year, field in rows:
        print(f"\n📄  {title[:70]}...")
        print(f"    👤  {authors[:50]}")
        print(f"    📅  {year}  |  🏷  {field}")
    print("\n──────────────────────────────────────────────")


def main():
    logger.info("PaperLens ingestion starting...")
    create_database()

    total = 0
    for field in FIELDS:
        logger.info(f"Fetching: {field}")
        papers = fetch_papers(field, PAPERS_PER_FIELD)
        saved  = save_papers(papers)
        total += saved
        logger.success(f"{field} → {saved} papers saved")

    logger.success(f"DONE! Total papers: {total}")
    show_sample()


if __name__ == "__main__":
    main()    
