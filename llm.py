import os
import json
from openai import OpenAI
from prompts import SYSTEM_PROMPT

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_documents(doctor_text, icd_candidates):
    icd_block = "\n".join(icd_candidates)

    prompt = f"""
Doctor note:
{doctor_text}

ICD-10 candidates:
{icd_block}

Return JSON:
{{
  "soap": "...",
  "codes": [{{"code": "", "description": ""}}],
  "claim_text": "..."
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
