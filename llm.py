import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EXTRACTION_PROMPT = """
You are a medical documentation assistant.
You DO NOT diagnose or suggest treatment.

Extract structured clinical facts from this doctor note.

Return a JSON object with keys:
age, sex, symptoms, findings, impression, care_setting
"""

GENERATION_PROMPT = """
You are a clinical documentation generator.
You must ONLY use the facts and ICD codes provided.
Do not invent diagnoses or treatments.

Produce:
1. SOAP Note
2. ICD-10 Codes list
3. Insurance claim justification
"""


def extract_facts(note):
    resp = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},  # forces valid JSON
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": note}
        ],
        temperature=0
    )

    # In OpenAI SDK v2, JSON is in .content
    return json.loads(resp.choices[0].message.content)


def generate_documents(facts, icd_codes):
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": GENERATION_PROMPT},
            {
                "role": "user",
                "content": f"Facts:\n{facts}\n\nICD Codes:\n{icd_codes}"
            }
        ],
        temperature=0
    )

    return resp.choices[0].message.content.strip()
