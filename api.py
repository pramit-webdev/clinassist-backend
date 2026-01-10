from fastapi import FastAPI
from pydantic import BaseModel
from icd_rag import ICD10RAG
from llm import extract_facts, generate_documents
from crud import (
    create_opd_visit,
    get_opd_visit,
    list_patients,
    get_patient_visits
)
from fhir_generator import generate_fhir_bundle

app = FastAPI()
rag = ICD10RAG(index_file="icd10.index", texts_file="icd10_texts.npy")

class DoctorNote(BaseModel):
    note: str


@app.post("/opd/visit")
def create_visit(note: DoctorNote):
    facts = extract_facts(note.note)

    query = " ".join(facts.get("impression", []) + facts.get("symptoms", []))
    icd_hits = rag.search(query, k=5)

    documents = generate_documents(facts, icd_hits)

    record = create_opd_visit(
        doctor_text=note.note,
        extracted_facts=facts,
        icd_codes=icd_hits,
        soap_text=documents,
        claim_text=documents
    )

    return {
        "visit_id": record["id"],
        "patient_id": record["patient_id"],
        "icd_codes": icd_hits,
        "documents": documents
    }


@app.get("/opd/patients")
def patients():
    return list_patients()


@app.get("/opd/patient/{patient_id}/visits")
def patient_visits(patient_id: str):
    return get_patient_visits(patient_id)


@app.get("/opd/visit/{visit_id}")
def visit(visit_id: str):
    return get_opd_visit(visit_id)


@app.get("/opd/visit/{visit_id}/fhir")
def visit_fhir(visit_id: str):
    visit = get_opd_visit(visit_id)
    return generate_fhir_bundle(visit)


@app.get("/opd/visit/{visit_id}/download")
def visit_download(visit_id: str):
    visit = get_opd_visit(visit_id)

    return {
        "soap": visit["soap_text"],
        "icd_codes": visit["icd_codes"],
        "insurance_claim": visit["claim_text"]
    }
