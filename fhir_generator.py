import uuid
from datetime import datetime

def generate_fhir_bundle(visit):
    bundle_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    patient_id = str(uuid.uuid4())
    encounter_id = str(uuid.uuid4())

    facts = visit["extracted_facts"]
    icd_codes = visit["icd_codes"]
    soap = visit["soap_text"]

    resources = []

    # Patient
    resources.append({
        "resourceType": "Patient",
        "id": patient_id,
        "gender": facts.get("sex", "unknown"),
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
            "code": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": icd.strip(),
                    "display": desc.strip()
                }]
            }
        })

    # Clinical Impression
    impression = facts.get("impression", [])
    if not isinstance(impression, list):
        impression = [impression]

    resources.append({
        "resourceType": "ClinicalImpression",
        "status": "completed",
        "subject": { "reference": f"Patient/{patient_id}" },
        "summary": ", ".join(impression)
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
                "text": {
                    "status": "generated",
                    "div": soap
                }
            }
        ]
    })

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "id": bundle_id,
        "entry": [{"resource": r} for r in resources]
    }
