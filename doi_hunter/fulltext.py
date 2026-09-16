import logging
import xml.etree.ElementTree as ET

import requests

from .htmlparser import extract_citation_metadata
from .models import PdfCandidate
from .netinfo import get_headers


LOGGER = logging.getLogger(__name__)
ARXIV_ATOM_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


def _get_json(session, url, timeout, **kwargs):
    try:
        response = session.get(url, headers=get_headers(), timeout=timeout, **kwargs)
    except requests.RequestException as error:
        return None, f"request failed: {error}"
    if response.status_code != 200:
        return None, f"HTTP {response.status_code}"
    try:
        return response.json(), ""
    except ValueError:
        return None, "invalid JSON response"


def publisher_candidates(session, doi, timeout):
    try:
        response = session.get(
            f"https://doi.org/{doi}",
            headers=get_headers(),
            timeout=timeout,
        )
        if response.status_code != 200:
            return [], f"publisher returned HTTP {response.status_code}"

        content_type = response.headers.get("Content-Type", "").lower()
        if "application/pdf" in content_type:
            return [PdfCandidate(response.url, "publisher")], ""

        title, pdf_url = extract_citation_metadata(response.text)
        if pdf_url:
            return [PdfCandidate(pdf_url, "publisher", title)], ""
        return [], "publisher page has no PDF metadata"
    except requests.RequestException as error:
        LOGGER.error("Publisher lookup failed for DOI '%s': %s", doi, error)
        return [], f"publisher request failed: {error}"


def unpaywall_candidates(session, doi, timeout, email=None):
    if not email:
        return [], "Unpaywall skipped (provide --email to enable it)"

    data, error = _get_json(
        session,
        f"https://api.unpaywall.org/v2/{doi}",
        timeout,
        params={"email": email},
    )
    if data is None:
        return [], f"Unpaywall {error}"

    locations = []
    best = data.get("best_oa_location")
    if best:
        locations.append(best)
    locations.extend(data.get("oa_locations") or [])

    candidates = []
    for location in locations:
        pdf_url = location.get("url_for_pdf")
        if pdf_url:
            candidates.append(PdfCandidate(pdf_url, "Unpaywall", data.get("title")))
    return candidates, "" if candidates else "Unpaywall found no open PDF"


def openalex_candidates(session, doi, timeout, email=None):
    params = {"mailto": email} if email else None
    data, error = _get_json(
        session,
        f"https://api.openalex.org/works/https://doi.org/{doi}",
        timeout,
        params=params,
    )
    if data is None:
        return [], f"OpenAlex {error}"

    locations = []
    best = data.get("best_oa_location")
    if best:
        locations.append(best)
    locations.extend(data.get("locations") or [])

    candidates = []
    for location in locations:
        pdf_url = location.get("pdf_url")
        if pdf_url:
            candidates.append(PdfCandidate(pdf_url, "OpenAlex", data.get("title")))
    return candidates, "" if candidates else "OpenAlex found no open PDF"


def europe_pmc_candidates(session, doi, timeout):
    data, error = _get_json(
        session,
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        timeout,
        params={"query": f'DOI:"{doi}"', "format": "json", "pageSize": 5},
    )
    if data is None:
        return [], f"Europe PMC {error}"

    candidates = []
    results = data.get("resultList", {}).get("result", [])
    for item in results:
        pmcid = item.get("pmcid")
        if pmcid and item.get("isOpenAccess") == "Y":
            candidates.append(
                PdfCandidate(
                    f"https://europepmc.org/articles/{pmcid}?pdf=render",
                    "Europe PMC",
                    item.get("title"),
                )
            )
    return candidates, "" if candidates else "Europe PMC found no open PDF"


def arxiv_candidates(session, doi, timeout):
    arxiv_prefix = "10.48550/arxiv."
    if doi.lower().startswith(arxiv_prefix):
        arxiv_id = doi[len(arxiv_prefix) :]
        return [
            PdfCandidate(
                f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                "arXiv",
            )
        ], ""

    try:
        response = session.get(
            "https://export.arxiv.org/api/query",
            params={"search_query": f'doi:"{doi}"', "max_results": 5},
            headers=get_headers(),
            timeout=timeout,
        )
        if response.status_code != 200:
            return [], f"arXiv returned HTTP {response.status_code}"

        root = ET.fromstring(response.content)
        candidates = []
        for entry in root.findall("atom:entry", ARXIV_ATOM_NAMESPACE):
            title_node = entry.find("atom:title", ARXIV_ATOM_NAMESPACE)
            title = " ".join(title_node.text.split()) if title_node is not None else None
            for link in entry.findall("atom:link", ARXIV_ATOM_NAMESPACE):
                if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                    candidates.append(PdfCandidate(link.get("href"), "arXiv", title))
        return candidates, "" if candidates else "arXiv found no matching PDF"
    except (requests.RequestException, ET.ParseError) as error:
        LOGGER.error("arXiv lookup failed for DOI '%s': %s", doi, error)
        return [], f"arXiv request failed: {error}"


def iter_open_candidate_groups(session, doi, timeout, email=None):
    """Yield each resolver's candidates and diagnostic in preferred order."""
    resolvers = (
        ("publisher", lambda: publisher_candidates(session, doi, timeout)),
        ("Unpaywall", lambda: unpaywall_candidates(session, doi, timeout, email)),
        ("OpenAlex", lambda: openalex_candidates(session, doi, timeout, email)),
        ("Europe PMC", lambda: europe_pmc_candidates(session, doi, timeout)),
        ("arXiv", lambda: arxiv_candidates(session, doi, timeout)),
    )

    for source, resolve in resolvers:
        resolved, diagnostic = resolve()
        yield source, resolved, diagnostic


def discover_open_candidates(session, doi, timeout, email=None):
    """Return de-duplicated open PDF candidates and resolver diagnostics."""
    candidates = []
    diagnostics = []
    seen_urls = set()
    for _, resolved, diagnostic in iter_open_candidate_groups(
        session, doi, timeout, email
    ):
        if diagnostic:
            diagnostics.append(diagnostic)
        for candidate in resolved:
            if candidate.url and candidate.url not in seen_urls:
                seen_urls.add(candidate.url)
                candidates.append(candidate)

    return candidates, diagnostics
