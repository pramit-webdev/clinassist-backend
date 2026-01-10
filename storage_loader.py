# storage_loader.py
import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

def download_from_supabase(filename):
    os.makedirs("data", exist_ok=True)
    local_path = os.path.join("data", filename)

    url = f"{SUPABASE_URL}/storage/v1/object/public/icd/{filename}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    print(f"Downloading {filename} from Supabase Storage...")

    r = requests.get(url, headers=headers, timeout=120)

    if r.status_code != 200:
        raise RuntimeError(f"Download failed: {r.status_code} {r.text}")

    with open(local_path, "wb") as f:
        f.write(r.content)

    print(f"{filename} downloaded successfully")
    return local_path
