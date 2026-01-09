import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

index = faiss.read_index("icd10.index")

with open("icd10_texts.pkl", "rb") as f:
    icd_texts = pickle.load(f)

def get_relevant_icd(query, k=5):
    emb = model.encode([query])
    D, I = index.search(np.array(emb).astype("float32"), k)
    return [icd_texts[i] for i in I[0]]
