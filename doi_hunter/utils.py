# paper_downloader/utils.py
import requests
import os
import re
import logging
from .netinfo import get_headers
from .proxy import waithIPchange


def download_file(url, file_name, download_folder):
    try:
        file_name = re.sub(r'[\\/*?:"<>|]', "", file_name) + ".pdf"
        file_path = os.path.join(download_folder, file_name)

        if os.path.exists(file_path):
            print("[v] File already exists. Skipping download.")
            return 'skipped'  # Indicate that the file was skipped

        print("  - Downloading the paper...")
        response = requests.get(url, headers=get_headers(), stream=True)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        file.write(chunk)
            print("[v] Paper downloaded successfully :)")
            return 'success'  # Indicate successful download
        elif response.status_code == 429:  # Too many requests or blocked
            if waithIPchange():
                return download_file(url, file_name, download_folder)
            else:
                return 'failed'  # Indicate failure
        else:
            print(f"[x] Failed to download file :( Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error downloading file from URL '{url}': {e}")
        print(f"[x] An error occurred while downloading: {e}")
    return 'failed'  # Indicate failure

def get_doi_by_title(title):
    search_url = f"https://api.crossref.org/works?query.bibliographic={title}"
    try:
        response = requests.get(search_url, headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            if data['message']['items']:
                doi = data['message']['items'][0]['DOI']
                return doi
    except Exception as e:
        logging.error(f"Error fetching DOI by title '{title}': {e}")
    return None

def log_failed_downloads(failed_downloads, failed_file):
    if failed_downloads:
        with open(failed_file, 'w') as file:
            for failed in set(failed_downloads):  # Use set to avoid duplicates
                file.write(f"{failed}\n")



