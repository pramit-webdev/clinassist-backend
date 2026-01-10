from supabase_client import supabase

def create_opd_visit(doctor_note, facts, icd_codes, documents):
    data = {
        "doctor_note": doctor_note,
        "extracted_facts": facts,
        "icd_codes": icd_codes,
        "soap_note": documents,
    }

    response = supabase.table("opd_visits").insert(data).execute()

    if not response.data:
        raise Exception("Failed to insert OPD visit")

    return response.data[0]
