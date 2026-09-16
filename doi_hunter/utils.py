import logging
import os
import re

import requests

from .netinfo import get_headers, waithIPchange


REQUEST_TIMEOUT = 30


def _pdf_file_name(file_name):
    """Return a filesystem-safe PDF name."""
    cleaned_name = re.sub(r'[\\/*?:"<>|]', "", file_name or "paper").strip()
    if not cleaned_name.lower().endswith(".pdf"):
        cleaned_name += ".pdf"
    return cleaned_name


def download_file(url, file_name, download_folder):
    """Download a PDF, returning ``success``, ``skipped``, or ``failed``."""
    safe_file_name = _pdf_file_name(file_name)
    file_path = os.path.join(download_folder, safe_file_name)

    if os.path.exists(file_path):
        print("[v] File already exists. Skipping download.")
        return "skipped"

    try:
        print("  - Downloading the paper...")
        response = requests.get(
            url,
            headers=get_headers(),
            stream=True,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        file.write(chunk)
            print("[v] Paper downloaded successfully :)")
            return "success"

        if response.status_code == 429 and waithIPchange():
            return download_file(url, safe_file_name, download_folder)

        print(f"[x] Failed to download file :( Status code: {response.status_code}")
    except requests.RequestException as error:
        logging.error("Error downloading file from URL '%s': %s", url, error)
        print(f"[x] An error occurred while downloading: {error}")
    except OSError as error:
        logging.error("Error writing downloaded file '%s': %s", file_path, error)
        print(f"[x] An error occurred while saving the file: {error}")

    return "failed"


def get_doi_by_title(title):
    """Return the first DOI reported by Crossref for a paper title."""
    try:
        response = requests.get(
            "https://api.crossref.org/works",
            params={"query.bibliographic": title, "rows": 1},
            headers=get_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            items = response.json().get("message", {}).get("items", [])
            if items:
                return items[0].get("DOI")
    except (requests.RequestException, ValueError) as error:
        logging.error("Error fetching DOI by title '%s': %s", title, error)

    return None


def log_failed_downloads(failed_downloads, failed_file):
    """Write unique failed identifiers in their original order."""
    unique_failures = dict.fromkeys(failed_downloads)
    with open(failed_file, "w", encoding="utf-8") as file:
        for failed in unique_failures:
            file.write(f"{failed}\n")
