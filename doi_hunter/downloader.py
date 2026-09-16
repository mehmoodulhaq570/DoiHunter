import logging
import os
import time

import requests

from .fulltext import iter_open_candidate_groups
from .htmlparser import extract_scihub_embed_link, extract_title
from .models import DownloadResult
from .netinfo import get_headers
from .utils import (
    REQUEST_TIMEOUT,
    create_session,
    download_file,
    find_doi_by_title,
    log_failed_downloads,
)

LOGGER = logging.getLogger(__name__)
LEGACY_SCIHUB_BASE_URL = "https://sci-hub.in/"


def get_scihub_original_url(
    doi,
    title,
    download_folder,
    session=None,
    timeout=REQUEST_TIMEOUT,
):
    """Use the project's legacy direct-embed lookup without result-page selection."""
    client = session or requests
    sci_hub_url = LEGACY_SCIHUB_BASE_URL + doi
    try:
        response = client.get(
            sci_hub_url,
            headers=get_headers(),
            timeout=timeout,
        )
        if response.status_code != 200:
            reason = f"legacy fallback returned HTTP {response.status_code}"
            return DownloadResult("failed", reason, "legacy fallback")

        file_name = extract_title(response.text) or title or doi
        original_url = extract_scihub_embed_link(response.text, response.url)
        if not original_url:
            reason = "legacy fallback page did not contain a direct PDF embed"
            return DownloadResult("failed", reason, "legacy fallback")

        return download_file(
            original_url,
            file_name,
            download_folder,
            session=client,
            timeout=timeout,
            source="legacy fallback",
        )
    except requests.Timeout:
        reason = f"legacy fallback timed out after {timeout} seconds"
    except requests.RequestException as error:
        reason = f"legacy fallback request failed: {error}"
        LOGGER.error("Legacy lookup failed for DOI '%s': %s", doi, error)
    return DownloadResult("failed", reason, "legacy fallback")


def download_paper(
    doi,
    title,
    download_folder,
    session,
    timeout=REQUEST_TIMEOUT,
    email=None,
    use_legacy_fallback=True,
):
    diagnostics = []
    seen_urls = set()

    for _, candidates, diagnostic in iter_open_candidate_groups(
        session, doi, timeout, email
    ):
        if diagnostic:
            diagnostics.append(diagnostic)
        for candidate in candidates:
            if not candidate.url or candidate.url in seen_urls:
                continue
            seen_urls.add(candidate.url)
            result = download_file(
                candidate.url,
                candidate.title or title or doi,
                download_folder,
                session=session,
                timeout=timeout,
                source=candidate.source,
            )
            if result.succeeded:
                return result
            diagnostics.append(result.reason)

    if use_legacy_fallback:
        legacy_result = get_scihub_original_url(
            doi,
            title,
            download_folder,
            session=session,
            timeout=timeout,
        )
        if legacy_result.succeeded:
            return legacy_result
        diagnostics.append(legacy_result.reason)

    useful_diagnostics = list(dict.fromkeys(item for item in diagnostics if item))
    reason = "; ".join(useful_diagnostics) or "no PDF source was found"
    return DownloadResult("failed", reason)


def process_papers_in_batch(
    batch,
    start_index,
    overall_total,
    failed_downloads,
    failure_details,
    skipped_files,
    download_folder,
    session,
    timeout,
    minimum_title_score,
    email,
    use_legacy_fallback,
):
    downloaded_count = 0

    for batch_index, identifier in enumerate(batch):
        overall_index = start_index + batch_index + 1
        print(f"\nProcessing [{overall_index}/{overall_total}]: {identifier}")

        doi = identifier if identifier.lower().startswith("10.") else None
        title = None if doi else identifier
        if not doi:
            match = find_doi_by_title(
                identifier,
                session=session,
                timeout=timeout,
                minimum_score=minimum_title_score,
            )
            if not match:
                reason = "no sufficiently close DOI match was found"
                failed_downloads.append(identifier)
                failure_details.append((identifier, reason))
                print(f"[x] Failed: {reason}.")
                continue
            doi = match.doi
            print(
                f"[i] Matched DOI {doi} via {match.provider} — "
                f"{match.matched_title} (title score {match.score:.2f})"
            )

        result = download_paper(
            doi,
            title,
            download_folder,
            session,
            timeout,
            email,
            use_legacy_fallback,
        )
        if result.status == "success":
            downloaded_count += 1
        elif result.status == "skipped":
            skipped_files.append(identifier)
        else:
            failed_downloads.append(identifier)
            failure_details.append((identifier, result.reason))
            print(f"[x] Failed: {result.reason}")

    return downloaded_count


def _read_input_lines(file_path):
    encodings_to_try = ("utf-8", "utf-8-sig", "latin-1", "cp1252")
    last_error = None
    for encoding in encodings_to_try:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                lines = [line.strip() for line in file if line.strip()]
            return lines, encoding
        except UnicodeDecodeError as error:
            last_error = error
    if last_error:
        raise last_error
    raise OSError(f"Unable to read input file: {file_path}")


def print_summary(
    total_count,
    downloaded_count,
    skipped_count,
    failure_details,
    failed_file,
    elapsed_seconds,
    verbose=False,
    interrupted=False,
):
    print("\n[SUMMARY]")
    print(f"Total papers in file: {total_count}")
    print(f"Total successfully downloaded: {downloaded_count}")
    print(f"Total skipped files: {skipped_count}")
    print(f"Total failed downloads: {len(failure_details)}")
    print(f"Elapsed time: {elapsed_seconds:.2f} seconds")

    if failure_details:
        print(f"\nFailed downloads have been logged in '{failed_file}':")
        if verbose:
            print("\nFailure details:")
            for identifier, reason in failure_details:
                print(f"  - {identifier}: {reason}")
    if interrupted:
        print("\n[INFO] DOI Hunter has stopped safely at the user's request.")
    else:
        print("[INFO] Thank you for using DoiHunter!")


def process_papers(
    file_path,
    batch_size=10,
    download_folder="downloads",
    retries=3,
    timeout=REQUEST_TIMEOUT,
    minimum_title_score=0.92,
    email=None,
    use_legacy_fallback=True,
    verbose=False,
):
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if retries < 0:
        raise ValueError("retries cannot be negative")
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    if not 0 <= minimum_title_score <= 1:
        raise ValueError("minimum_title_score must be between 0 and 1")

    failed_downloads = []
    failure_details = []
    skipped_files = []
    downloaded_count = 0
    interrupted = False
    total_count = 0
    failed_file = "failed_downloads.txt"
    start_time = time.time()

    print("\n[INFO] Welcome to DOI Hunter!")
    print("[INFO] Resolving titles and searching available PDF sources.")
    print("[INFO] Starting the download process...\n")

    os.makedirs(download_folder, exist_ok=True)
    session = create_session(retries)
    try:
        lines, encoding = _read_input_lines(file_path)
        total_count = len(lines)
        print(f"[INFO] Read {total_count} entries using {encoding}.")

        for start_index in range(0, total_count, batch_size):
            batch = lines[start_index : start_index + batch_size]
            downloaded_count += process_papers_in_batch(
                batch,
                start_index,
                total_count,
                failed_downloads,
                failure_details,
                skipped_files,
                download_folder,
                session,
                timeout,
                minimum_title_score,
                email,
                use_legacy_fallback,
            )
    except KeyboardInterrupt:
        interrupted = True
        print("\n[INFO] Stop requested. Finishing safely...")
    except (OSError, UnicodeError, ValueError) as error:
        total_count = 0
        LOGGER.error("Processing failed: %s", error)
        print(f"[x] Processing failed: {error}")
    finally:
        session.close()
        try:
            log_failed_downloads(failed_downloads, failed_file)
        except OSError as error:
            LOGGER.error("Could not write failure log: %s", error)
            print(f"[x] Could not write '{failed_file}': {error}")

    print_summary(
        total_count,
        downloaded_count,
        len(skipped_files),
        failure_details,
        failed_file,
        time.time() - start_time,
        verbose,
        interrupted,
    )

    return {
        "total": total_count,
        "downloaded": downloaded_count,
        "skipped": len(skipped_files),
        "failed": len(failed_downloads),
        "failures": failure_details,
        "interrupted": interrupted,
    }
