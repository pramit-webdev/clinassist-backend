import uuid
from datetime import datetime
from supabase_client import supabase


def require_supabase():
    if supabase is None:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY."
        )


def create_opd_visit(
    doctor_text,
    extracted_facts,
    icd_codes,
    soap_text,
    claim_text,
    patient_id=None
):
    require_supabase()

    # Patient identity MUST come from API, never from LLM
    if not patient_id:
        patient_id = str(uuid.uuid4())

    visit_id = str(uuid.uuid4())

    record = {
        "id": visit_id,
        "patient_id": patient_id,
        "doctor_text": doctor_text,
        "extracted_facts": extracted_facts,
        "icd_codes": icd_codes,
        "soap_text": soap_text,
        "claim_text": claim_text,
        "created_at": datetime.utcnow().isoformat()
    }

    resp = supabase.table("opd_visits").insert(record).execute()

    if not resp.data:
        raise RuntimeError(f"Insert failed: {resp}")

    return resp.data[0]


def get_opd_visit(visit_id):
    require_supabase()

    resp = (
        supabase.table("opd_visits")
        .select("*")
        .eq("id", visit_id)
        .single()
        .execute()
    )

    if not resp.data:
        raise KeyError(f"Visit not found: {visit_id}")

    return resp.data


def list_patients():
    require_supabase()

    resp = supabase.table("opd_visits").select("patient_id").execute()

    if not resp.data:
        return []

    return list({r["patient_id"] for r in resp.data})


def get_patient_visits(patient_id):
    require_supabase()

    resp = (
        supabase.table("opd_visits")
        .select("*")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )

    return resp.data or []
