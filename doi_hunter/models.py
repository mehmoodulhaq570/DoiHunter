from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DoiMatch:
    doi: str
    matched_title: str
    score: float
    provider: str = "Crossref"
    work_type: str = ""
    cited_by_count: int = 0
    publication_year: int = 0


@dataclass(frozen=True)
class PdfCandidate:
    url: str
    source: str
    title: Optional[str] = None


@dataclass(frozen=True)
class DownloadResult:
    status: str
    reason: str = ""
    source: Optional[str] = None
    path: Optional[str] = None

    @property
    def succeeded(self):
        return self.status in {"success", "skipped"}
