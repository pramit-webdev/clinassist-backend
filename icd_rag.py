import os
import faiss
import numpy as np
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ICD10RAG:
    def __init__(self, dim=1536, index_file="icd10.index", texts_file="icd10_texts.npy"):
        self.dim = dim
        self.index_file = index_file
        self.texts_file = texts_file

        if os.path.exists(index_file) and os.path.exists(texts_file):
            print("Loading existing ICD-10 FAISS index")
            self.index = faiss.read_index(index_file)
            self.texts = np.load(texts_file, allow_pickle=True).tolist()
        else:
            print("Creating new ICD-10 FAISS index")
            self.index = faiss.IndexFlatL2(dim)
            self.texts = []

    def embed_batch(self, texts):
        """Embed a batch of texts using OpenAI"""
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [d.embedding for d in resp.data]

    def build_from_csv(self, csv_path, batch_size=200):
        rows = []

        # Read ICD file safely (works for your space-separated format)
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()

                # Must have: chapter, order, ICD-code, description...
                if len(parts) < 4:
                    continue

                code = parts[2]
                description = " ".join(parts[3:])

                rows.append(f"{code} - {description}")

        print(f"Loaded {len(rows)} ICD-10 rows")

        all_vectors = []

        # 🔥 BATCHED embedding to avoid OpenAI token limits
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            print(f"Embedding ICD batch {i} → {i + len(batch)}")

            vectors = self.embed_batch(batch)
            all_vectors.extend(vectors)

        # Convert to FAISS array
        vec_array = np.array(all_vectors, dtype="float32")

        self.index.add(vec_array)
        self.texts = rows

        faiss.write_index(self.index, self.index_file)
        np.save(self.texts_file, np.array(self.texts, dtype=object))

        print("ICD-10 FAISS index built successfully")

    def search(self, query, k=8):
        vec = self.embed_batch([query])
        D, I = self.index.search(np.array(vec, dtype="float32"), k)
        return [self.texts[i] for i in I[0] if 0 <= i < len(self.texts)]
