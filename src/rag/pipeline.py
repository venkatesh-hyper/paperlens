import os 
from groq import Groq
from loguru import logger
from dotenv import load_dotenv
from src.rag.prompts import SUMMARY_PROMPT

 
load_dotenv()

#config

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 500
TEMPERATURE = 0.5

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def summarize_paper(title:str, abstract:str) -> dict:
    logger.info(f"Summarizing paper: {title}")
    prompt = SUMMARY_PROMPT.format(abstract=abstract)
    
    try:
        import time
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        
        elapsed_time = (time.time() - start_time) * 1000
        summary = response.choices[0].message.content.strip()
        
        logger.success(f"Summary generated in {elapsed_time:.0f} ms")
        
        return{
            "title" : title,
            "summary": summary,
            "model": GROQ_MODEL,
            "latency_ms": round(elapsed_time, 2),
            "tokens_used": response.usage.total_tokens
        }

    except Exception as e:
        logger.error(f"groq API error: {e}")
        raise RuntimeError("Failed to generate summary")
    
