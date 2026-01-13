import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===========================
# FACT EXTRACTION (SAFE)
# ===========================

EXTRACTION_PROMPT = """
You are a clinical documentation extractor.

You DO NOT diagnose.
You DO NOT suggest treatment.

Your job is to extract exactly what the doctor wrote.

Return a JSON object with these fields:

age
sex
symptoms: list of patient-reported symptoms
findings: list of physical exam or lab findings

diagnoses: list of objects:
- text: the exact diagnosis phrase the doctor used
- status: one of ["confirmed", "suspected", "ruled_out"]

impression: short free-text clinical summary
care_setting

RULES:
- Only include something in diagnoses if the doctor explicitly stated it.
- If doctor says "possible", "likely", "?", "rule out" → status = suspected
- If doctor says "no", "not", "ruled out" → status = ruled_out
- Never invent diseases.
"""

# ===========================
# DOCUMENT GENERATION
# ===========================

GENERATION_PROMPT = """
You are a clinical documentation generator.

You must ONLY use:
- The extracted facts
- The ICD-10 codes provided

You must NOT invent diagnoses or treatments.

Produce:
1. SOAP Note
2. ICD-10 Codes list
3. Insurance claim justification
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
                "content": f"Facts:\n{json.dumps(facts, indent=2)}\n\nICD Codes:\n{icd_codes}"
            }
        ],
        temperature=0
    )

    return resp.choices[0].message.content.strip()
