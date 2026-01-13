from fastapi import FastAPI
from pydantic import BaseModel
from icd_engine import ICDVectorEngine
from llm import extract_facts, generate_documents
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


def to_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    return [str(x)]


@app.post("/opd/visit")
def create_visit(note: DoctorNote):
    # ---------------------------
    # 1️⃣ Extract facts from doctor note
    # ---------------------------
    facts = extract_facts(note.note)

    symptoms = to_list(facts.get("symptoms"))
    diagnoses = facts.get("diagnoses", [])

    icd_hits = []

    # ---------------------------
    # 2️⃣ Symptoms → R-codes only
    # ---------------------------
    if symptoms:
        symptom_query = " ".join(symptoms)
        icd_hits.extend(
            rag.search(symptom_query, k=5, mode="symptom")
        )

    # ---------------------------
    # 3️⃣ Only CONFIRMED diagnoses → disease codes
    # ---------------------------
    for d in diagnoses:
        if d.get("status") == "confirmed":
            icd_hits.extend(
                rag.search(d["text"], k=5, mode="disease")
            )

    # Remove duplicates while preserving order
    icd_hits = list(dict.fromkeys(icd_hits))

    # ---------------------------
    # 4️⃣ Generate clinical documents
    # ---------------------------
    documents = generate_documents(facts, icd_hits)

    # ---------------------------
    # 5️⃣ Store visit (longitudinal-safe)
    # ---------------------------
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
        "documents": documents
    }


# ---------------------------
# Patient & Visit APIs
# ---------------------------

@app.get("/opd/patients")
def patients():
    return list_patients()


@app.get("/opd/patient/{patient_id}/visits")
def patient_visits(patient_id: str):
    return get_patient_visits(patient_id)


@app.get("/opd/visit/{visit_id}")
def visit(visit_id: str):
    return get_opd_visit(visit_id)


# ---------------------------
# FHIR & Export
# ---------------------------

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


# ---------------------------
# Health
# ---------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "icd_engine": "loaded"
    }
