# fhir_generator.py
import uuid
from datetime import datetime

def generate_fhir_bundle(visit):
    bundle_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    patient_id = str(uuid.uuid4())
    encounter_id = str(uuid.uuid4())

    resources = []

    # Patient
    resources.append({
        "resourceType": "Patient",
        "id": patient_id,
        "gender": visit["facts"].get("sex", "unknown"),
        "birthDate": None
    })

    # Encounter
    resources.append({
        "resourceType": "Encounter",
        "id": encounter_id,
        "status": "finished",
        "class": { "code": "AMB" },
        "subject": { "reference": f"Patient/{patient_id}" }
    })

    # Conditions (ICD-10)
    for code in visit["icd_codes"]:
        icd, desc = code.split(" - ", 1)
        resources.append({
            "resourceType": "Condition",
            "id": str(uuid.uuid4()),
            "subject": { "reference": f"Patient/{patient_id}" },
            "code": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": icd,
                    "display": desc
                }]
            }
        })

    # Clinical Impression
    resources.append({
        "resourceType": "ClinicalImpression",
        "status": "completed",
        "subject": { "reference": f"Patient/{patient_id}" },
        "summary": ", ".join(visit["facts"].get("impression", []))
    })

    # Composition (SOAP)
    resources.append({
        "resourceType": "Composition",
        "status": "final",
        "type": { "text": "OPD Visit" },
        "date": now,
        "subject": { "reference": f"Patient/{patient_id}" },
        "section": [
            {
                "title": "SOAP Note",
                "text": { "status": "generated", "div": visit["soap"] }
            }
        ]
    })

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "id": bundle_id,
        "entry": [{"resource": r} for r in resources]
    }
