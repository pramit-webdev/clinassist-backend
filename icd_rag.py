import os
import faiss
import numpy as np
from openai import OpenAI
from storage_loader import download_from_hf

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_DIR = "data"


class ICD10RAG:
    def __init__(self, dim=1536, index_file="icd10.index", texts_file="icd10_texts.npy"):
        self.dim = dim

        os.makedirs(DATA_DIR, exist_ok=True)

        self.index_path = os.path.join(DATA_DIR, index_file)
        self.texts_path = os.path.join(DATA_DIR, texts_file)

        # Download FAISS + text files from HuggingFace if missing
        if not os.path.exists(self.index_path):
            print("Downloading FAISS index from HuggingFace Hub...")
            download_from_hf(index_file)

        if not os.path.exists(self.texts_path):
            print("Downloading ICD text file from HuggingFace Hub...")
            download_from_hf(texts_file)

        # Load FAISS + texts
        print("Loading ICD-10 FAISS index...")
        self.index = faiss.read_index(self.index_path)
        self.texts = np.load(self.texts_path, allow_pickle=True).tolist()

        print(f"ICD-10 RAG ready — {len(self.texts)} codes loaded")

    # Embed user query (small, safe)
    def embed(self, texts):
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [d.embedding for d in resp.data]

    def search(self, query, k=8):
        vec = self.embed([query])
        D, I = self.index.search(np.array(vec, dtype="float32"), k)
        return [self.texts[i] for i in I[0] if 0 <= i < len(self.texts)]
