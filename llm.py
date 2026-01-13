import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===========================
# FACT EXTRACTION (CLINICALLY SAFE)
# ===========================

EXTRACTION_PROMPT = """
You are a clinical information extraction system.

You DO NOT diagnose.
You DO NOT infer diseases.
You DO NOT suggest treatments.

You only extract what the doctor explicitly stated.

Return a JSON object with these fields:

age
sex

symptoms: list of patient-reported symptoms
findings: list of observed clinical findings

diagnoses: list of objects with:
- text: the exact disease phrase written by the doctor
- status: one of ["confirmed", "suspected", "ruled_out"]

impression: short summary of the visit WITHOUT adding diagnoses
care_setting

STRICT RULES:
- Only include something in diagnoses if the doctor explicitly named a disease.
- If doctor uses words like "possible", "likely", "?", "rule out" → status = suspected
- If doctor says "no", "not", "ruled out" → status = ruled_out
- Symptoms (pain, fever, cough, diarrhea, etc) must NEVER go into diagnoses.
- If no diagnosis is stated, diagnoses MUST be an empty list.
"""

# ===========================
# DOCUMENT GENERATION (ICD LOCKED)
# ===========================

GENERATION_PROMPT = """
You are a medical documentation generator.

The ICD-10 codes provided are FINAL.
They were produced by a certified coding engine.

You MUST:
- Use ONLY those ICD codes
- Never add new ICDs
- Never remove ICDs
- Never change their meaning

You must NOT invent:
- diseases
- diagnoses
- treatments

You must NOT convert symptoms into diseases.

If no disease ICDs are present, you must treat the visit as symptom-based only.

Produce:
1. SOAP Note
2. ICD-10 Codes list (copy exactly)
3. Insurance claim justification

You must reflect uncertainty when diagnoses are suspected.
"""

def extract_facts(note):
    resp = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": note}
        ],
        temperature=0
    )

    return json.loads(resp.choices[0].message.content)


def generate_documents(facts, icd_codes):
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": GENERATION_PROMPT},
            {
                "role": "user",
                "content": f"""
FACTS:
{json.dumps(facts, indent=2)}

ICD CODES (locked):
{json.dumps(icd_codes, indent=2)}
"""
            }
        ],
        temperature=0
    )

    return resp.choices[0].message.content.strip()
