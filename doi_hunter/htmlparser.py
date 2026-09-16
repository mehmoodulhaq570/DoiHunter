# paper_downloader/html_parser.py
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin


SCIHUB_BASE_URL = "https://sci-hub.se/"

def extract_title(html):
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.text.strip()
        title = re.sub(r'^(Sci-Hub\s*-*\s*)', "", title, flags=re.IGNORECASE)
        title = ' '.join(title.split()[:15])
        title = re.sub(r'[\\/*?:"<>|]', "", title)
        return title
    return None


def extract_scihub_embed_link(html):
    soup = BeautifulSoup(html, "html.parser")
    embed_tag = soup.find("embed", src=True)
    if embed_tag:
        return urljoin(SCIHUB_BASE_URL, embed_tag.get("src"))
    return None


def extract_citation_metadata(html):
    """Extract a publisher-provided title and PDF URL from citation metadata."""
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("meta", attrs={"name": "citation_title"})
    pdf_tag = soup.find("meta", attrs={"name": "citation_pdf_url"})
    title = title_tag.get("content") if title_tag else None
    pdf_url = pdf_tag.get("content") if pdf_tag else None
    return title, pdf_url
