import os
import zipfile
import gdown
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ==== Google Drive ====
DRIVE_FILE_ID = "12gy4kXd14L78wceSPFEIdmH_jeuzu-8n"
DATA_DIR = "data"
ZIP_PATH = os.path.join(DATA_DIR, "icd_vectordb.zip")

os.makedirs(DATA_DIR, exist_ok=True)

# Download once
if not os.path.exists(os.path.join(DATA_DIR, "icd_leaf.index")):
    print("Downloading ICD vector DB from Google Drive...")
    gdown.download(
        f"https://drive.google.com/uc?id={DRIVE_FILE_ID}",
        ZIP_PATH,
        quiet=False
    )

    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(DATA_DIR)

    os.remove(ZIP_PATH)

# Load FAISS
leaf_index = faiss.read_index(f"{DATA_DIR}/icd_leaf.index")
family_index = faiss.read_index(f"{DATA_DIR}/icd_family.index")
block_index = faiss.read_index(f"{DATA_DIR}/icd_block.index")

leaf_meta = np.load(f"{DATA_DIR}/icd_leaf.npy", allow_pickle=True)
family_meta = np.load(f"{DATA_DIR}/icd_family.npy", allow_pickle=True)
block_meta = np.load(f"{DATA_DIR}/icd_block.npy", allow_pickle=True)

# Load embedding model
model = SentenceTransformer("BAAI/bge-small-en-v1.5")


def embed(text: str):
    return model.encode([text], normalize_embeddings=True)


class ICDVectorEngine:
    def search(self, query: str, k=5):
        q = embed(query)

        # 1️⃣ block
        _, b_ids = block_index.search(q, 3)
        blocks = {block_meta[i] for i in b_ids[0]}

        # 2️⃣ family
        fam_candidates = []
        for i, fam in enumerate(family_meta):
            if any(fam.startswith(b) for b in blocks):
                fam_candidates.append(i)

        fam_vecs = family_index.reconstruct_n(0, family_index.ntotal)
        fam_subset = fam_vecs[fam_candidates]

        _, f_ids = faiss.IndexFlatIP(fam_subset.shape[1]).search(q, 5)
        families = {family_meta[fam_candidates[i]] for i in f_ids[0]}

        # 3️⃣ leaf
        results = []
        for code, desc, fam, blk in leaf_meta:
            if fam in families:
                results.append(f"{code} – {desc}")

        return results[:k]
