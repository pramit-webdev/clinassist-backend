from fastapi import FastAPI
from pydantic import BaseModel
from icd_rag import ICD10RAG
from llm import extract_facts, generate_documents

app = FastAPI()
rag = ICD10RAG(
    index_file="icd10.index",
    texts_file="icd10_texts.npy"
)

class DoctorNote(BaseModel):
    note: str

@app.post("/generate")
def generate(note: DoctorNote):
    # Step 1 — Extract clinical facts
    facts = extract_facts(note.note)

    # Step 2 — Build ICD query
    query = " ".join(facts.get("impression", []) + facts.get("symptoms", []))

    # Step 3 — Retrieve ICD-10
    icd_hits = rag.search(query, k=5)

    # Step 4 — Generate final docs
    output = generate_documents(facts, icd_hits)

    return {
        "extracted_facts": facts,
        "icd_matches": icd_hits,
        "documents": output
    }
