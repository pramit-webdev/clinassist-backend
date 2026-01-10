import os
import requests

HF_BASE_URL = os.getenv("HF_BASE_URL")

def download_from_hf(filename):
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", filename)

    if os.path.exists(path):
        return path

    url = f"{HF_BASE_URL}/{filename}"
    print("Downloading", url)

    r = requests.get(url, timeout=300)
    r.raise_for_status()

    with open(path, "wb") as f:
        f.write(r.content)

    return path
