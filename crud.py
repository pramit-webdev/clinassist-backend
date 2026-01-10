import uuid
from supabase_client import supabase

def create_opd_visit(doctor_text, extracted_facts, icd_codes, soap_text, claim_text):
    patient_id = extracted_facts.get("patient_id") or str(uuid.uuid4())

    record = {
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "doctor_text": doctor_text,
        "extracted_facts": extracted_facts,
        "icd_codes": icd_codes,
        "soap_text": soap_text,
        "claim_text": claim_text
    }

    resp = supabase.table("opd_visits").insert(record).execute()
    return resp.data[0]


def get_opd_visit(visit_id):
    return supabase.table("opd_visits").select("*").eq("id", visit_id).single().execute().data


def list_patients():
    resp = supabase.table("opd_visits") \
        .select("patient_id") \
        .execute()

    # Unique patient IDs
    return list({r["patient_id"] for r in resp.data})


def get_patient_visits(patient_id):
    return supabase.table("opd_visits") \
        .select("*") \
        .eq("patient_id", patient_id) \
        .order("created_at", desc=True) \
        .execute().data
