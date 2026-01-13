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

# Download vector DB once
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

# Load FAISS indexes
leaf_index = faiss.read_index(f"{DATA_DIR}/icd_leaf.index")
family_index = faiss.read_index(f"{DATA_DIR}/icd_family.index")
block_index = faiss.read_index(f"{DATA_DIR}/icd_block.index")

# Load metadata
leaf_meta = np.load(f"{DATA_DIR}/icd_leaf.npy", allow_pickle=True)
family_meta = np.load(f"{DATA_DIR}/icd_family.npy", allow_pickle=True)
block_meta = np.load(f"{DATA_DIR}/icd_block.npy", allow_pickle=True)

# Embedding model (lightweight & HF-safe)
model = SentenceTransformer("BAAI/bge-small-en-v1.5")


def embed(texts):
    return model.encode(texts, normalize_embeddings=True).astype("float32")


class ICDVectorEngine:
    def search(self, query, k=5, mode="symptom"):
        """
        mode = "symptom" → only R-codes allowed
        mode = "disease" → R-codes blocked
        """

        q = embed([query])

        # -------------------------
        # 1️⃣ Block-level search
        # -------------------------
        _, b_ids = block_index.search(q, 3)
        selected_blocks = {block_meta[i] for i in b_ids[0] if i < len(block_meta)}

        # -------------------------
        # 2️⃣ Family filtering
        # -------------------------
        valid_families = [
            fam for fam in family_meta
            if any(fam.startswith(b) for b in selected_blocks)
        ]

        if not valid_families:
            valid_families = list(family_meta)

        fam_vecs = embed(valid_families)
        fam_index = faiss.IndexFlatIP(fam_vecs.shape[1])
        fam_index.add(fam_vecs)

        _, fam_ids = fam_index.search(q, 5)
        chosen_families = {valid_families[i] for i in fam_ids[0] if i < len(valid_families)}

        # -------------------------
        # 3️⃣ Leaf-level filtering
        # -------------------------
        leaf_texts = []
        leaf_map = []

        for code, desc, fam, blk in leaf_meta:
            if fam not in chosen_families:
                continue

            # 🔐 HARD SAFETY WALL
            if mode == "symptom" and not code.startswith("R"):
                continue
            if mode == "disease" and code.startswith("R"):
                continue

            leaf_texts.append(f"ICD {code}. {desc}.")
            leaf_map.append((code, desc))

        if not leaf_texts:
            return []

        leaf_vecs = embed(leaf_texts)
        temp_index = faiss.IndexFlatIP(leaf_vecs.shape[1])
        temp_index.add(leaf_vecs)

        _, leaf_ids = temp_index.search(q, k)

        results = []
        for i in leaf_ids[0]:
            if i < len(leaf_map):
                results.append(f"{leaf_map[i][0]} – {leaf_map[i][1]}")

        return results
