# paper_downloader/html_parser.py
from bs4 import BeautifulSoup
import re

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
        link = embed_tag.get("src")
        if link.startswith('/downloads'):
            link = "https://sci-hub.se" + link
        return link
    return None
