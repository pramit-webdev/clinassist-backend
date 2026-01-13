import uuid
from datetime import datetime


def generate_fhir_bundle(visit):
    bundle_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Use real longitudinal patient ID
    patient_id = visit["patient_id"]
    encounter_id = visit["id"]

    facts = visit.get("extracted_facts") or {}
    icd_codes = visit.get("icd_codes") or []
    soap = visit.get("soap_text") or ""

    resources = []

    # -------------------------
    # Patient (ABDM-compatible)
    # -------------------------
    sex = facts.get("sex") or "unknown"

    resources.append({
        "resourceType": "Patient",
        "id": patient_id,
        "gender": sex.lower(),
        "birthDate": None,
        "identifier": [
            {
                "system": "https://ndhm.gov.in/abha",
                "value": patient_id
            }
        ]
    })

    # -------------------------
    # Encounter (OPD Visit)
    # -------------------------
    resources.append({
        "resourceType": "Encounter",
        "id": encounter_id,
        "status": "finished",
        "class": { "code": "AMB" },
        "subject": { "reference": f"Patient/{patient_id}" },
        "period": {
            "start": visit.get("created_at", now)
        }
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
    impression = facts.get("impression") or []
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
    # Composition (SOAP)
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
