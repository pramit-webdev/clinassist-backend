import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

BUCKET = "icd"

def download_from_supabase(filename):
    url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}"

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }

    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()

    with open(filename, "wb") as f:
        f.write(r.content)

    print("Downloaded", filename)
