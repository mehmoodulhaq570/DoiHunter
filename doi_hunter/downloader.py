# paper_downloader/downloader.py
import os
import time
import requests
import logging
from .htmlparser import (
    extract_citation_metadata,
    extract_title,
    extract_scihub_embed_link,
)
from .netinfo import get_headers, waithIPchange
from .utils import (
    REQUEST_TIMEOUT,
    log_failed_downloads,
    download_file,
    get_doi_by_title,
)

logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def get_publisher_download(doi, title, download_folder):
    """Try an official PDF advertised by the DOI publisher."""
    try:
        response = requests.get(
            f"https://doi.org/{doi}",
            headers=get_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            return "failed"

        content_type = response.headers.get("Content-Type", "").lower()
        if "application/pdf" in content_type:
            return download_file(response.url, title or doi, download_folder)

        publisher_title, pdf_url = extract_citation_metadata(response.text)
        if pdf_url:
            return download_file(
                pdf_url, publisher_title or title or doi, download_folder
            )
    except requests.RequestException as error:
        logging.error("Error resolving DOI '%s' through its publisher: %s", doi, error)

    return "failed"


def download_paper(doi, title, download_folder):
    """Prefer an official publisher PDF, then use the legacy Sci-Hub path."""
    publisher_result = get_publisher_download(doi, title, download_folder)
    if publisher_result in {"success", "skipped"}:
        return publisher_result
    return get_scihub_original_url(doi, title, download_folder)


def get_scihub_original_url(doi, title, download_folder):
    base_url = "https://sci-hub.in/"
    sci_hub_url = base_url + doi
    try:
        response = requests.get(
            sci_hub_url,
            headers=get_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            html_content = response.text
            file_name = extract_title(html_content) or title
            original_url = extract_scihub_embed_link(html_content)

            # Fix for malformed URLs starting with '//'
            if original_url and original_url.startswith("//"):
                original_url = "https:" + original_url

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
            result = download_paper(identifier, None, download_folder)
            if result == "success":
                downloaded_count += 1
            elif result == "skipped":
                skipped_files.append(identifier)
            else:
                failed_downloads.append(identifier)
        else:  # Assume it's a title
            doi = get_doi_by_title(identifier)
            if doi:
                result = download_paper(doi, identifier, download_folder)
                if result == "success":
                    downloaded_count += 1
                elif result == "skipped":
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
    print(
        "This tool helps you download research papers from Sci-Hub using DOIs or titles."
    )
    print(
        "For more information and the source code, visit: https://github.com/mehmoodulhaq570\n"
    )

    print("[INFO] Starting the download process...\n")
    start_time = time.time()

    # Create a downloads folder if it doesn't exist
    download_folder = "downloads"
    os.makedirs(download_folder, exist_ok=True)

    # Path to the failed downloads file
    failed_file = "failed_downloads.txt"

    try:
        encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

        for enc in encodings_to_try:
            try:
                with open(file_path, "r", encoding=enc) as file:
                    lines = [
                        line.strip() for line in file if line.strip()
                    ]  # Remove empty lines and whitespace
                    total_count = len(lines)
                print(f"[INFO] Successfully read file using encoding: {enc}")
                break  # Exit loop if successful
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"[WARNING] Failed with encoding {enc}: {e}")
                continue
        else:
            raise UnicodeDecodeError(
                "utf-8", b"", 0, 1, "All attempted encodings failed to decode the file."
            )

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = lines[i : i + batch_size]
            downloaded_count += process_papers_in_batch(
                batch, failed_downloads, skipped_files, download_folder
            )

    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")
        print(f"[x] An error occurred during processing: {e}")

    finally:
        try:
            log_failed_downloads(failed_downloads, failed_file)
            if failed_downloads:
                print(f"\n[!] Failed downloads have been logged in '{failed_file}'.")
        except OSError as log_err:
            print(f"[x] Error writing failed downloads file: {log_err}")

    print("\n[SUMMARY]")
    print(f"Total papers in file: {total_count}")
    print(f"Total successfully downloaded: {downloaded_count}")
    print(f"Total skipped files: {len(skipped_files)}")
    print(f"Total failed downloads: {len(set(failed_downloads))}")
    if failed_downloads:
        print(f"\nFailed downloads have been logged in '{failed_file}':")
    # print(f"\n[INFO] Download process completed in {time.time() - start_time:.2f} seconds.")
    print("[INFO] Thank you for using DoiHunter!")
