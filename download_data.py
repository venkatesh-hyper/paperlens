from huggingface_hub import hf_hub_download
import os

REPO_ID = os.getenv("HF_REPO_ID", "vengen9840/paperlens-data")
os.makedirs("data", exist_ok=True)
for f in ["papers.db", "faiss_index.bin"]:
    hf_hub_download(repo_id=REPO_ID, filename=f, repo_type="dataset", local_dir="data")
print("Data ready!")