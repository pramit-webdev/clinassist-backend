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

if not os.path.exists(os.path.join(DATA_DIR, "icd_leaf.index")):
    print("Downloading ICD vector DB from Google Drive...")
    gdown.download(f"https://drive.google.com/uc?id={DRIVE_FILE_ID}", ZIP_PATH, quiet=False)
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(DATA_DIR)
    os.remove(ZIP_PATH)

# Load indexes
leaf_index = faiss.read_index(f"{DATA_DIR}/icd_leaf.index")
family_index = faiss.read_index(f"{DATA_DIR}/icd_family.index")
block_index = faiss.read_index(f"{DATA_DIR}/icd_block.index")

leaf_meta = np.load(f"{DATA_DIR}/icd_leaf.npy", allow_pickle=True)
family_meta = np.load(f"{DATA_DIR}/icd_family.npy", allow_pickle=True)
block_meta = np.load(f"{DATA_DIR}/icd_block.npy", allow_pickle=True)

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def embed(texts):
    return model.encode(texts, normalize_embeddings=True).astype("float32")

# -----------------------------
# Confidence calibration
# -----------------------------
MIN_CONFIDENCE = 0.35   # below this → unreliable
HIGH_CONFIDENCE = 0.65  # above this → strong

def calibrate(score):
    if score < MIN_CONFIDENCE:
        return 0.0
    if score >= HIGH_CONFIDENCE:
        return 1.0
    return round((score - MIN_CONFIDENCE) / (HIGH_CONFIDENCE - MIN_CONFIDENCE), 3)

class ICDVectorEngine:
    def search(self, query, k=5, mode="symptom"):
        q = embed([query])

        # 1️⃣ Block narrowing
        _, b_ids = block_index.search(q, 3)
        selected_blocks = {block_meta[i] for i in b_ids[0] if i < len(block_meta)}

        # 2️⃣ Family narrowing
        valid_families = [f for f in family_meta if any(f.startswith(b) for b in selected_blocks)]
        if not valid_families:
            valid_families = list(family_meta)

        fam_vecs = embed(valid_families)
        fam_index = faiss.IndexFlatIP(fam_vecs.shape[1])
        fam_index.add(fam_vecs)

        _, fam_ids = fam_index.search(q, 5)
        chosen_families = {valid_families[i] for i in fam_ids[0] if i < len(valid_families)}

        # 3️⃣ Leaf filtering with safety wall
        leaf_texts = []
        leaf_map = []

        for code, desc, fam, blk in leaf_meta:
            if fam not in chosen_families:
                continue
            if mode == "symptom" and not code.startswith("R"):
                continue
            if mode == "disease" and code.startswith("R"):
                continue

            leaf_texts.append(f"{desc}")
            leaf_map.append((code, desc))

        if not leaf_texts:
            return []

        leaf_vecs = embed(leaf_texts)
        temp_index = faiss.IndexFlatIP(leaf_vecs.shape[1])
        temp_index.add(leaf_vecs)

        scores, ids = temp_index.search(q, k)

        results = []

        for rank, i in enumerate(ids[0]):
            if i >= len(leaf_map):
                continue

            raw = float(scores[0][rank])
            confidence = calibrate(raw)

            # Reject weak matches
            if confidence == 0:
                continue

            code, desc = leaf_map[i]

            results.append({
                "code": code,
                "description": desc,
                "confidence": confidence,
                "raw_score": round(raw, 3),
                "matched_on": query,
                "mode": mode
            })

        return sorted(results, key=lambda x: x["confidence"], reverse=True)
