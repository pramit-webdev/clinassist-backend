import uuid
from datetime import datetime


def generate_fhir_bundle(visit):
    bundle_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # CRITICAL: Use real patient_id from database
    patient_id = visit["patient_id"]
    encounter_id = visit["id"]   # visit id is the encounter

    facts = visit["extracted_facts"]
    icd_codes = visit["icd_codes"]
    soap = visit["soap_text"]

    resources = []

    # -------------------------
    # Patient
    # -------------------------
    resources.append({
        "resourceType": "Patient",
        "id": patient_id,
        "gender": facts.get("sex", "unknown").lower(),
        "birthDate": None
    })

    # -------------------------
    # Encounter (OPD Visit)
    # -------------------------
    resources.append({
        "resourceType": "Encounter",
        "id": encounter_id,
        "status": "finished",
        "class": { "code": "AMB" },
        "subject": { "reference": f"Patient/{patient_id}" }
    })

    # -------------------------
    # Conditions (ICD-10)
    # -------------------------
    for entry in icd_codes:
        if "–" in entry:
            icd, desc = entry.split("–", 1)
        elif "-" in entry:
            icd, desc = entry.split("-", 1)
        else:
            icd = entry
            desc = ""

        resources.append({
            "resourceType": "Condition",
            "id": str(uuid.uuid4()),
            "subject": { "reference": f"Patient/{patient_id}" },
            "encounter": { "reference": f"Encounter/{encounter_id}" },
            "code": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": icd.strip(),
                    "display": desc.strip()
                }]
            }
        })

    # -------------------------
    # Clinical Impression
    # -------------------------
    impression = facts.get("impression", [])
    if not isinstance(impression, list):
        impression = [impression]

    resources.append({
        "resourceType": "ClinicalImpression",
        "id": str(uuid.uuid4()),
        "status": "completed",
        "subject": { "reference": f"Patient/{patient_id}" },
        "encounter": { "reference": f"Encounter/{encounter_id}" },
        "summary": ", ".join(impression)
    })

    # -------------------------
    # Composition (SOAP Note)
    # -------------------------
    resources.append({
        "resourceType": "Composition",
        "id": str(uuid.uuid4()),
        "status": "final",
        "type": { "text": "OPD Visit" },
        "date": now,
        "subject": { "reference": f"Patient/{patient_id}" },
        "encounter": { "reference": f"Encounter/{encounter_id}" },
        "section": [
            {
                "title": "SOAP Note",
                "text": {
                    "status": "generated",
                    "div": soap
                }
            }
        ]
    })

    # -------------------------
    # FHIR Bundle
    # -------------------------
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "id": bundle_id,
        "entry": [{"resource": r} for r in resources]
    }
