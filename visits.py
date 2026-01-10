from supabase_client import supabase
import uuid

def create_visit(patient_id, doctor_note, soap, icd_codes, claim):
    visit_id = str(uuid.uuid4())

    supabase.table("opd_visits").insert({
        "id": visit_id,
        "patient_id": patient_id,
        "doctor_note": doctor_note,
        "soap": soap,
        "icd_codes": icd_codes,
        "insurance_claim": claim
    }).execute()

    return visit_id


def get_visit(visit_id):
    return supabase.table("opd_visits").select("*").eq("id", visit_id).execute().data[0]


def get_patient_visits(patient_id):
    return supabase.table("opd_visits").select("*").eq("patient_id", patient_id).execute().data
