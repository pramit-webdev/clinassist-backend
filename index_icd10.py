import pandas as pd
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

df = pd.read_csv("data/ICD10codes.csv")

texts = [f"{row['Code']} - {row['Description']}" for _, row in df.iterrows()]

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(texts, show_progress_bar=True)

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(np.array(embeddings).astype("float32"))

faiss.write_index(index, "icd10.index")

with open("icd10_texts.pkl", "wb") as f:
    pickle.dump(texts, f)

print("ICD-10 FAISS index built.")
