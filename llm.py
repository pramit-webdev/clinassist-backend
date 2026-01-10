import os
from openai import OpenAI
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EXTRACTION_PROMPT = """
You are a medical documentation assistant.
You DO NOT diagnose or suggest treatment.

Extract structured clinical facts from this doctor note.

Return ONLY valid JSON with keys:
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
        messages=[
            {"role":"system","content":EXTRACTION_PROMPT},
            {"role":"user","content":note}
        ]
    )
    return json.loads(resp.choices[0].message.content)

def generate_documents(facts, icd_codes):
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":GENERATION_PROMPT},
            {"role":"user","content":f"Facts:\n{facts}\n\nICD Codes:\n{icd_codes}"}
        ]
    )
    return resp.choices[0].message.content
