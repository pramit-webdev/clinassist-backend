from fastapi import FastAPI
from db import SessionLocal
from models import OPDDocument
from rag import get_relevant_icd
from llm import generate_documents

app = FastAPI()

@app.post("/process")
def process_opd(doctor_text: str):
    icd_candidates = get_relevant_icd(doctor_text)
    result = generate_documents(doctor_text, icd_candidates)

    db = SessionLocal()
    doc = OPDDocument(
        doctor_text=doctor_text,
        soap=result["soap"],
        icd_codes=result["codes"],
        claim_text=result["claim_text"]
    )
    db.add(doc)
    db.commit()
    db.close()

    return result
