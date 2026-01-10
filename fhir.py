# fhir.py
import uuid
from datetime import datetime

def build_patient(facts):
    return {
        "resourceType": "Patient",
        "id": str(uuid.uuid4()),
        "gender": facts.get("sex", "unknown").lower(),
        "birthDate": None,   # we only have age
        "extension": [
            {
                "url": "https://nrces.in/ndhm/fhir/r4/StructureDefinition/age",
                "valueInteger": facts.get("age")
            }
        ]
    }
