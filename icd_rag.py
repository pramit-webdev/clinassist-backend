import os
import faiss
import numpy as np
from openai import OpenAI
from storage_loader import download_from_supabase

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ICD10RAG:
    def __init__(self, dim=1536, index_file="icd10.index", texts_file="icd10_texts.npy"):
        self.dim = dim
        self.index_file = index_file
        self.texts_file = texts_file

        # ⬇️ Download from Supabase Storage if not present
        if not os.path.exists(index_file):
            print("Downloading FAISS index from Supabase...")
            download_from_supabase(index_file)

        if not os.path.exists(texts_file):
            print("Downloading ICD texts from Supabase...")
            download_from_supabase(texts_file)

        # ⬇️ Load FAISS + texts
        print("Loading ICD-10 FAISS index")
        self.index = faiss.read_index(index_file)
        self.texts = np.load(texts_file, allow_pickle=True).tolist()

        print(f"ICD-10 RAG ready: {len(self.texts)} codes loaded")

    # Used only at query time
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
