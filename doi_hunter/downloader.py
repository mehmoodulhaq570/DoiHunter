# paper_downloader/downloader.py
import os
import time
import requests
import logging
from .htmlparser import extract_title, extract_scihub_embed_link
from .netinfo import get_headers, waithIPchange
from .utils import log_failed_downloads, download_file, get_doi_by_title

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def get_scihub_original_url(doi, title, download_folder):
    base_url = "https://sci-hub.se/"
    sci_hub_url = base_url + doi
    try:
        response = requests.get(sci_hub_url, headers=get_headers())
        if response.status_code == 200:
            html_content = response.text
            file_name = extract_title(html_content) or title
            original_url = extract_scihub_embed_link(html_content)
            if original_url:
                return download_file(original_url, file_name, download_folder)
        elif response.status_code == 429:
            if waithIPchange():
                return get_scihub_original_url(doi, title, download_folder)
    except Exception as e:
        logging.error(f"Error accessing Sci-Hub URL '{sci_hub_url}': {e}")
        print(f"[x] An error occurred while accessing Sci-Hub: {e}")
    print("[x] Failed to download file :(")
    return False


def process_papers_in_batch(batch, failed_downloads, skipped_files, download_folder):
    downloaded_count = 0
    total_count = len(batch)

    for idx, identifier in enumerate(batch, start=1):
        print(f"Processing [{idx}/{total_count}]: {identifier}")

        if identifier.startswith("10."):  # Likely a DOI
            result = get_scihub_original_url(identifier, None, download_folder)
            if result == 'success':
                downloaded_count += 1
            elif result == 'skipped':
                skipped_files.append(identifier)
            else:
                failed_downloads.append(identifier)
        else:  # Assume it's a title
            doi = get_doi_by_title(identifier)
            if doi:
                result = get_scihub_original_url(doi, identifier, download_folder)
                if result == 'success':
                    downloaded_count += 1
                elif result == 'skipped':
                    skipped_files.append(identifier)
                else:
                    failed_downloads.append(identifier)
            else:
                failed_downloads.append(identifier)  # Add title if DOI not found

    return downloaded_count

def process_papers(file_path, batch_size):
    failed_downloads = []
    skipped_files = []
    total_count = 0
    downloaded_count = 0

    print("\n[INFO] Welcome to DoiHunter!")
    print("This tool helps you download research papers from Sci-Hub using DOIs or titles.")
    print("For more information and the source code, visit: https://github.com/mehmoodulhaq570\n")

    print("[INFO] Starting the download process...\n")
    start_time = time.time()

    # Create a downloads folder if it doesn't exist
    download_folder = "downloads"
    os.makedirs(download_folder, exist_ok=True)

    # Path to the failed downloads file
    failed_file = "failed_downloads.txt"

    try:
        with open(file_path, 'r') as file:
            lines = [line.strip() for line in file if line.strip()]  # Remove empty lines and whitespace
            total_count = len(lines)

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = lines[i:i + batch_size]
            downloaded_count += process_papers_in_batch(batch, failed_downloads, skipped_files, download_folder)

    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")
        print(f"[x] An error occurred during processing: {e}")
        # Log failed downloads even if an exception occurs
        log_failed_downloads(failed_downloads, failed_file)
        # Print the content of failed_downloads.txt
        if os.path.exists(failed_file):
            print(f"\nFailed downloads have been logged in '{failed_file}':")
            with open(failed_file, 'r') as file:
                print(file.read())
        return

    print("\n[SUMMARY]")
    print(f"Total papers in file: {total_count}")
    print(f"Total successfully downloaded: {downloaded_count}")
    print(f"Total skipped files: {len(skipped_files)}")
    print(f"Total failed downloads: {len(set(failed_downloads))}")
    log_failed_downloads(failed_downloads, failed_file)
