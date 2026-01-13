from fastapi import FastAPI
from pydantic import BaseModel
from icd_engine import ICDVectorEngine
from llm import extract_facts, generate_documents
from validator import validate_icds
from crud import (
    create_opd_visit,
    get_opd_visit,
    list_patients,
    get_patient_visits
)
from fhir_generator import generate_fhir_bundle
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow browser + Postman access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = ICDVectorEngine()


class DoctorNote(BaseModel):
    note: str
    patient_id: str | None = None


def as_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


@app.post("/opd/visit")
def create_visit(note: DoctorNote):

    # -------------------------------------------------
    # 1) Extract clinically safe facts
    # -------------------------------------------------
    facts = extract_facts(note.note)

    symptoms = as_list(facts.get("symptoms"))
    diagnoses = as_list(facts.get("diagnoses"))

    raw_hits = []

    # -------------------------------------------------
    # 2) Symptoms → R-codes only
    # -------------------------------------------------
    if symptoms:
        query = " ".join(symptoms)
        raw_hits.extend(rag.search(query, k=8, mode="symptom"))

    # -------------------------------------------------
    # 3) Only CONFIRMED diagnoses → disease codes
    # -------------------------------------------------
    for d in diagnoses:
        if isinstance(d, dict) and d.get("status") == "confirmed":
            raw_hits.extend(rag.search(d["text"], k=8, mode="disease"))

    # -------------------------------------------------
    # 4) Deduplicate by ICD code (keep best score)
    # -------------------------------------------------
    dedup = {}
    for item in raw_hits:
        code = item["code"]
        if code not in dedup or item["score"] > dedup[code]["score"]:
            dedup[code] = item

    candidates = list(dedup.values())

    # -------------------------------------------------
    # 5) Clinical validation layer (LLM)
    # -------------------------------------------------
    validation = validate_icds(facts, candidates)
    icd_hits = validation["approved"]
    rejected = validation["rejected"]

    # -------------------------------------------------
    # 6) Generate clinical documents
    # -------------------------------------------------
    documents = generate_documents(facts, icd_hits)

    # -------------------------------------------------
    # 7) Persist visit (longitudinal-safe)
    # -------------------------------------------------
    record = create_opd_visit(
        doctor_text=note.note,
        extracted_facts=facts,
        icd_codes=icd_hits,
        soap_text=documents,
        claim_text=documents,
        patient_id=note.patient_id
    )

    return {
        "visit_id": record["id"],
        "patient_id": record["patient_id"],
        "icd_codes": icd_hits,
        "rejected_icds": rejected,
        "documents": documents
    }


# -------------------------------------------------
# Patient APIs
# -------------------------------------------------

@app.get("/opd/patients")
def patients():
    return list_patients()


@app.get("/opd/patient/{patient_id}/visits")
def patient_visits(patient_id: str):
    return get_patient_visits(patient_id)


@app.get("/opd/visit/{visit_id}")
def visit(visit_id: str):
    return get_opd_visit(visit_id)


# -------------------------------------------------
# FHIR & Export
# -------------------------------------------------

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


# -------------------------------------------------
# Health
# -------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "icd_engine": "loaded"
    }
