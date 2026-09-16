import logging
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import DoiMatch, DownloadResult
from .netinfo import get_headers


REQUEST_TIMEOUT = 30
LOGGER = logging.getLogger(__name__)
ARXIV_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


def create_session(retries=3):
    """Create a reusable HTTP session with bounded retry/backoff behavior."""
    retry_policy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_policy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def normalize_title(title):
    normalized = unicodedata.normalize("NFKD", title or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.findall(r"[a-z0-9]+", normalized))


def title_similarity(requested_title, candidate_title):
    requested = normalize_title(requested_title)
    candidate = normalize_title(candidate_title)
    if not requested or not candidate:
        return 0.0

    if requested == candidate:
        return 1.0

    requested_tokens = requested.split()
    candidate_tokens = candidate.split()
    sequence_score = SequenceMatcher(None, requested, candidate).ratio()
    word_order_score = SequenceMatcher(None, requested_tokens, candidate_tokens).ratio()
    requested_words = set(requested_tokens)
    candidate_words = set(candidate_tokens)
    token_score = len(requested_words & candidate_words) / len(
        requested_words | candidate_words
    )
    combined_score = (
        0.35 * sequence_score + 0.45 * word_order_score + 0.20 * token_score
    )
    if requested_tokens[0] != candidate_tokens[0]:
        combined_score *= 0.9
    return combined_score


def _crossref_matches(client, title, timeout):
    response = client.get(
        "https://api.crossref.org/works",
        params={"query.title": title, "rows": 20},
        headers=get_headers(),
        timeout=timeout,
    )
    if response.status_code != 200:
        print(f"[x] Crossref lookup returned HTTP {response.status_code}.")
        return []

    matches = []
    for item in response.json().get("message", {}).get("items", []):
        titles = item.get("title") or []
        doi = item.get("DOI")
        if titles and doi:
            date_parts = (
                item.get("published-print", {}).get("date-parts")
                or item.get("published-online", {}).get("date-parts")
                or item.get("created", {}).get("date-parts")
                or []
            )
            year = date_parts[0][0] if date_parts and date_parts[0] else 0
            matches.append(
                DoiMatch(
                    doi,
                    titles[0],
                    title_similarity(title, titles[0]),
                    "Crossref",
                    item.get("type") or "",
                    item.get("is-referenced-by-count") or 0,
                    year,
                )
            )
    return matches


def _openalex_title_matches(client, title, timeout):
    response = client.get(
        "https://api.openalex.org/works",
        params={"search": title, "per-page": 20},
        headers=get_headers(),
        timeout=timeout,
    )
    if response.status_code != 200:
        return []

    matches = []
    for item in response.json().get("results", []):
        candidate_title = item.get("title")
        doi_url = item.get("doi") or ""
        if candidate_title and doi_url.lower().startswith("https://doi.org/"):
            matches.append(
                DoiMatch(
                    doi_url[len("https://doi.org/") :],
                    candidate_title,
                    title_similarity(title, candidate_title),
                    "OpenAlex",
                    item.get("type") or "",
                    item.get("cited_by_count") or 0,
                    item.get("publication_year") or 0,
                )
            )
    return matches


def _arxiv_title_matches(client, title, timeout):
    response = client.get(
        "https://export.arxiv.org/api/query",
        params={"search_query": f'ti:"{title}"', "start": 0, "max_results": 10},
        headers=get_headers(),
        timeout=timeout,
    )
    if response.status_code != 200:
        return []

    root = ET.fromstring(response.content)
    matches = []
    for entry in root.findall("atom:entry", ARXIV_NAMESPACE):
        title_node = entry.find("atom:title", ARXIV_NAMESPACE)
        id_node = entry.find("atom:id", ARXIV_NAMESPACE)
        published_node = entry.find("atom:published", ARXIV_NAMESPACE)
        if title_node is None or id_node is None:
            continue
        candidate_title = " ".join((title_node.text or "").split())
        arxiv_id = (id_node.text or "").rstrip("/").rsplit("/", 1)[-1]
        arxiv_id = re.sub(r"v\d+$", "", arxiv_id)
        year_text = (published_node.text or "")[:4] if published_node is not None else ""
        year = int(year_text) if year_text.isdigit() else 0
        if arxiv_id:
            matches.append(
                DoiMatch(
                    f"10.48550/arXiv.{arxiv_id}",
                    candidate_title,
                    title_similarity(title, candidate_title),
                    "arXiv",
                    "preprint",
                    0,
                    year,
                )
            )
    return matches


def _type_priority(work_type):
    return {
        "journal-article": 5,
        "proceedings-article": 5,
        "article": 5,
        "book-chapter": 4,
        "book": 3,
        "posted-content": 2,
        "preprint": 2,
        "dataset": 0,
    }.get(work_type, 1)


def _select_best_match(matches):
    best_score = max(match.score for match in matches)
    score_pool = [match for match in matches if match.score >= best_score - 0.005]

    arxiv_matches = [
        match
        for match in score_pool
        if match.doi.lower().startswith("10.48550/arxiv.") and match.publication_year
    ]
    other_years = [
        match.publication_year
        for match in score_pool
        if not match.doi.lower().startswith("10.48550/arxiv.")
        and match.publication_year
    ]
    if arxiv_matches and other_years:
        earliest_arxiv = min(match.publication_year for match in arxiv_matches)
        if earliest_arxiv <= min(other_years) - 2:
            return max(arxiv_matches, key=lambda match: match.cited_by_count)

    return max(
        score_pool,
        key=lambda match: (match.cited_by_count, _type_priority(match.work_type)),
    )


def find_doi_by_title(
    title,
    session=None,
    timeout=REQUEST_TIMEOUT,
    minimum_score=0.92,
):
    """Find the closest Crossref title match that meets the requested score."""
    client = session or requests
    try:
        matches = []
        resolvers = (
            ("Crossref", _crossref_matches),
            ("OpenAlex", _openalex_title_matches),
            ("arXiv", _arxiv_title_matches),
        )
        for resolver_name, resolver in resolvers:
            try:
                matches.extend(resolver(client, title, timeout))
            except (requests.RequestException, ValueError, ET.ParseError) as error:
                LOGGER.error(
                    "%s title lookup failed for '%s': %s",
                    resolver_name,
                    title,
                    error,
                )
                print(f"[!] {resolver_name} title lookup failed; trying other indexes.")

        if not matches:
            print("[x] No DOI candidates were returned by the title indexes.")
            return None

        unique_matches = {}
        for match in matches:
            key = match.doi.lower()
            existing = unique_matches.get(key)
            if existing is None or (match.score, match.cited_by_count) > (
                existing.score,
                existing.cited_by_count,
            ):
                unique_matches[key] = match

        best_match = _select_best_match(list(unique_matches.values()))
        if best_match.score < minimum_score:
            print(
                "[x] No sufficiently close Crossref title match "
                f"(best score: {best_match.score:.2f}, required: {minimum_score:.2f})."
            )
            return None
        return best_match
    except (ValueError, TypeError) as error:
        LOGGER.error("Could not rank DOI candidates for title '%s': %s", title, error)
        print(f"[x] Could not rank DOI candidates: {error}")
    return None


def get_doi_by_title(title, **kwargs):
    """Backward-compatible wrapper returning only a DOI string."""
    match = find_doi_by_title(title, **kwargs)
    return match.doi if match else None


def _pdf_file_name(file_name):
    cleaned_name = re.sub(r'[\\/*?:"<>|]', "", file_name or "paper").strip(" .")
    cleaned_name = cleaned_name or "paper"
    if not cleaned_name.lower().endswith(".pdf"):
        cleaned_name += ".pdf"
    return cleaned_name


def _remove_partial_file(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as error:
        LOGGER.warning("Could not remove partial file '%s': %s", path, error)


def is_pdf_file(path):
    try:
        with open(path, "rb") as file:
            return file.read(5) == b"%PDF-"
    except OSError:
        return False


def download_file(
    url,
    file_name,
    download_folder,
    session=None,
    timeout=REQUEST_TIMEOUT,
    source="direct URL",
):
    """Atomically download and validate a PDF."""
    safe_file_name = _pdf_file_name(file_name)
    file_path = os.path.join(download_folder, safe_file_name)
    partial_path = file_path + ".part"

    os.makedirs(download_folder, exist_ok=True)
    if os.path.exists(file_path) and is_pdf_file(file_path):
        print(f"[v] File already exists. Skipping download ({source}).")
        return DownloadResult("skipped", source=source, path=file_path)

    if os.path.exists(file_path):
        print("[!] Existing file is not a valid PDF; replacing it.")

    client = session or requests
    _remove_partial_file(partial_path)
    try:
        print(f"  - Trying {source}...")
        response = client.get(
            url,
            headers=get_headers(),
            stream=True,
            timeout=timeout,
        )
        if response.status_code != 200:
            if response.status_code in {401, 403}:
                reason = f"{source} requires authorization (HTTP {response.status_code})"
            elif response.status_code == 404:
                reason = f"{source} PDF was not found (HTTP 404)"
            elif response.status_code == 429:
                reason = f"{source} rate limit persisted after retries (HTTP 429)"
            else:
                reason = f"{source} returned HTTP {response.status_code}"
            print(f"[x] {reason}.")
            return DownloadResult("failed", reason, source)

        chunks = iter(response.iter_content(chunk_size=64 * 1024))
        buffered_chunks = []
        signature = b""
        while len(signature) < 5:
            chunk = next(chunks, b"")
            if not chunk:
                break
            buffered_chunks.append(chunk)
            signature += chunk

        if not signature.startswith(b"%PDF-"):
            content_type = response.headers.get("Content-Type", "unknown")
            reason = f"{source} returned {content_type}, not a valid PDF"
            print(f"[x] {reason}.")
            return DownloadResult("failed", reason, source)

        with open(partial_path, "wb") as file:
            for chunk in buffered_chunks:
                file.write(chunk)
            for chunk in chunks:
                if chunk:
                    file.write(chunk)

        os.replace(partial_path, file_path)
        print(f"[v] Paper downloaded successfully from {source}.")
        return DownloadResult("success", source=source, path=file_path)
    except requests.Timeout:
        reason = f"{source} timed out after {timeout} seconds"
        print(f"[x] {reason}.")
    except requests.RequestException as error:
        reason = f"{source} request failed: {error}"
        LOGGER.error("Download failed for URL '%s': %s", url, error)
        print(f"[x] {reason}")
    except OSError as error:
        reason = f"could not save PDF: {error}"
        LOGGER.error("Could not save downloaded file '%s': %s", file_path, error)
        print(f"[x] {reason}")
    finally:
        _remove_partial_file(partial_path)

    return DownloadResult("failed", reason, source)


def log_failed_downloads(failed_downloads, failed_file):
    unique_failures = dict.fromkeys(failed_downloads)
    with open(failed_file, "w", encoding="utf-8") as file:
        for failed in unique_failures:
            file.write(f"{failed}\n")
