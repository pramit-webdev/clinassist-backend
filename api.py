from fastapi import FastAPI
from pydantic import BaseModel
from icd_rag import ICD10RAG
from llm import extract_facts, generate_documents
from crud import create_opd_visit

app = FastAPI()
rag = ICD10RAG(index_file="icd10.index", texts_file="icd10_texts.npy")

class DoctorNote(BaseModel):
    note: str

@app.post("/opd/visit")
def create_visit(note: DoctorNote):
    # 1. Extract structured facts
    facts = extract_facts(note.note)

    # 2. Build ICD query
    query = " ".join(facts.get("impression", []) + facts.get("symptoms", []))

    # 3. Retrieve ICD-10
    icd_hits = rag.search(query, k=5)

    # 4. Generate SOAP + claim
    documents = generate_documents(facts, icd_hits)

    # 5. Store in Supabase
    record = create_opd_visit(
        doctor_note=note.note,
        facts=facts,
        icd_codes=icd_hits,
        documents=documents
    )

    return {
        "visit_id": record["id"],
        "icd_codes": icd_hits,
        "documents": documents
    }
