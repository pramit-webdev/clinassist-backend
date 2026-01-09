import os
import faiss
import numpy as np
import pandas as pd
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ICD10RAG:
    def __init__(self, dim=1536, index_file="icd10.index", texts_file="icd10_texts.npy"):
        self.dim = dim
        self.index_file = index_file
        self.texts_file = texts_file

        if os.path.exists(index_file) and os.path.exists(texts_file):
            self.index = faiss.read_index(index_file)
            self.texts = np.load(texts_file, allow_pickle=True).tolist()
        else:
            self.index = faiss.IndexFlatL2(dim)
            self.texts = []

    def embed(self, texts):
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [d.embedding for d in resp.data]

    def build_from_csv(self, csv_path):
        # Your file is tab-separated with no header
        df = pd.read_csv(csv_path, sep="\t", header=None)

        # Column meaning from your sample:
        # 0 = category
        # 1 = order
        # 2 = ICD code (A000, A001…)
        # 3 = long description

        rows = [
            f"{row[2]} - {row[3]}"
            for _, row in df.iterrows()
            if str(row[2]).strip() != "" and str(row[3]).strip() != ""
        ]

        vectors = self.embed(rows)

        self.index.add(np.array(vectors, dtype="float32"))
        self.texts = rows

        faiss.write_index(self.index, self.index_file)
        np.save(self.texts_file, np.array(self.texts, dtype=object))

    def search(self, query, k=8):
        vec = self.embed([query])
        D, I = self.index.search(np.array(vec, dtype="float32"), k)
        return [self.texts[i] for i in I[0] if 0 <= i < len(self.texts)]
