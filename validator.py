import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VALIDATION_PROMPT = """
You are a clinical coding validator.

You are given:
- Extracted clinical facts from a doctor note
- A list of ICD-10 codes proposed by an AI system

Your job is to VALIDATE them.

Rules:
- Keep a code ONLY if it is logically supported by the extracted facts
- If a code is a disease (not R-code), keep it ONLY if the doctor explicitly diagnosed it
- Remove codes that are speculative, unsupported, or contradict the note
- You must not add new codes

Return JSON with:
{
  "approved": [
     {
       "code": "...",
       "description": "...",
       "score": number,
       "reason": "short justification"
     }
  ],
  "rejected": [
     {
       "code": "...",
       "description": "...",
       "score": number,
       "reason": "why this code is invalid"
     }
  ]
}
"""


def validate_icds(facts, icd_candidates):
    resp = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": VALIDATION_PROMPT},
            {
                "role": "user",
                "content": f"""
FACTS:
{json.dumps(facts, indent=2)}

ICD CANDIDATES:
{json.dumps(icd_candidates, indent=2)}
"""
            }
        ],
        temperature=0
    )

    return json.loads(resp.choices[0].message.content)
