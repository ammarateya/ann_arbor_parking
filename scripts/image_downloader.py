import os
import pathlib
from typing import List, Tuple
import requests


def ensure_dir(path: str) -> None:
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def download_images(image_urls: List[str], citation_number: str, base_dir: str = "images") -> List[Tuple[str, str]]:
    """Download images to images/{citation_number}/ and return list[(source_url, local_path)]."""
    results: List[Tuple[str, str]] = []
    if not image_urls:
        return results
    dest_dir = os.path.join(base_dir, str(citation_number))
    ensure_dir(dest_dir)
    session = requests.Session()
    for idx, url in enumerate(image_urls):
        name = f"img_{idx+1}.jpg"
        local_path = os.path.join(dest_dir, name)
        try:
            with session.get(url, timeout=60, stream=True) as r:
                r.raise_for_status()
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            results.append((url, local_path))
        except Exception:
            continue
    return results


