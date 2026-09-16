import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from doi_hunter.htmlparser import extract_citation_metadata, extract_scihub_embed_link
from doi_hunter.models import DoiMatch
from doi_hunter.utils import (
    _select_best_match,
    download_file,
    find_doi_by_title,
    get_doi_by_title,
    log_failed_downloads,
    title_similarity,
)


class UtilsTests(unittest.TestCase):
    def test_matcher_prefers_much_earlier_canonical_arxiv_record(self):
        selected = _select_best_match(
            [
                DoiMatch(
                    "10.48550/arXiv.1706.03762",
                    "Attention Is All You Need",
                    1.0,
                    "arXiv",
                    "preprint",
                    0,
                    2017,
                ),
                DoiMatch(
                    "10.65215/example",
                    "Attention Is All You Need",
                    1.0,
                    "OpenAlex",
                    "preprint",
                    7000,
                    2025,
                ),
            ]
        )

        self.assertEqual(selected.doi, "10.48550/arXiv.1706.03762")

    def test_matcher_uses_citations_to_break_exact_title_collision(self):
        selected = _select_best_match(
            [
                DoiMatch(
                    "10.example/chapter",
                    "Random Forests",
                    1.0,
                    "Crossref",
                    "book-chapter",
                    19,
                    1997,
                ),
                DoiMatch(
                    "10.1023/a:1010933404324",
                    "Random Forests",
                    1.0,
                    "OpenAlex",
                    "article",
                    131918,
                    2001,
                ),
            ]
        )

        self.assertEqual(selected.doi, "10.1023/a:1010933404324")

    def test_extract_citation_metadata(self):
        html = """
            <meta name="citation_title" content="An Open Paper">
            <meta name="citation_pdf_url" content="https://example.test/paper.pdf">
        """

        title, url = extract_citation_metadata(html)

        self.assertEqual(title, "An Open Paper")
        self.assertEqual(url, "https://example.test/paper.pdf")

    def test_extract_scihub_embed_link_resolves_relative_urls(self):
        html = '<embed src="/uptodate/paper.pdf#view=FitH">'

        url = extract_scihub_embed_link(html)

        self.assertEqual(
            url,
            "https://sci-hub.se/uptodate/paper.pdf#view=FitH",
        )

    @patch("doi_hunter.utils.requests.get")
    def test_download_file_saves_pdf(self, mock_get):
        response = Mock(status_code=200)
        response.iter_content.return_value = [b"%PDF-test"]
        mock_get.return_value = response

        with tempfile.TemporaryDirectory() as folder:
            result = download_file("https://example.test/paper", "A: Paper", folder)
            output = Path(folder, "A Paper.pdf")

            self.assertEqual(result.status, "success")
            self.assertEqual(output.read_bytes(), b"%PDF-test")
            self.assertFalse(Path(folder, "A Paper.pdf.part").exists())

    @patch("doi_hunter.utils.requests.get")
    def test_download_file_skips_existing_file(self, mock_get):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "Paper.pdf").write_bytes(b"%PDF-existing")

            result = download_file("https://example.test/paper", "Paper", folder)

            self.assertEqual(result.status, "skipped")
            mock_get.assert_not_called()

    @patch("doi_hunter.utils.requests.get")
    def test_download_file_rejects_html(self, mock_get):
        response = Mock(status_code=200)
        response.headers = {"Content-Type": "text/html"}
        response.iter_content.return_value = [b"<html>not a PDF</html>"]
        mock_get.return_value = response

        with tempfile.TemporaryDirectory() as folder:
            result = download_file("https://example.test/paper", "Paper", folder)

            self.assertEqual(result.status, "failed")
            self.assertIn("not a valid PDF", result.reason)
            self.assertFalse(Path(folder, "Paper.pdf").exists())
            self.assertFalse(Path(folder, "Paper.pdf.part").exists())

    @patch("doi_hunter.utils.requests.get")
    def test_interrupted_download_removes_partial_file(self, mock_get):
        def interrupted_chunks():
            yield b"%PDF-partial"
            raise KeyboardInterrupt

        response = Mock(status_code=200)
        response.iter_content.return_value = interrupted_chunks()
        mock_get.return_value = response

        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(KeyboardInterrupt):
                download_file("https://example.test/paper", "Paper", folder)

            self.assertFalse(Path(folder, "Paper.pdf").exists())
            self.assertFalse(Path(folder, "Paper.pdf.part").exists())

    @patch("doi_hunter.utils.requests.get")
    def test_get_doi_by_title_uses_crossref_parameters(self, mock_get):
        crossref_response = Mock(status_code=200)
        crossref_response.json.return_value = {
            "message": {
                "items": [
                    {"DOI": "10.9999/wrong", "title": ["An unrelated paper"]},
                    {
                        "DOI": "10.1234/example",
                        "title": ["Wind and solar forecasting"],
                    },
                ]
            }
        }
        openalex_response = Mock(status_code=200)
        openalex_response.json.return_value = {"results": []}
        arxiv_response = Mock(status_code=200)
        arxiv_response.content = b'<feed xmlns="http://www.w3.org/2005/Atom" />'
        mock_get.side_effect = [
            crossref_response,
            openalex_response,
            arxiv_response,
        ]

        doi = get_doi_by_title("Wind & solar forecasting", minimum_score=0.8)

        self.assertEqual(doi, "10.1234/example")
        crossref_call = mock_get.call_args_list[0]
        self.assertEqual(
            crossref_call.kwargs["params"]["query.title"],
            "Wind & solar forecasting",
        )
        self.assertEqual(crossref_call.kwargs["params"]["rows"], 20)

    def test_title_similarity_normalizes_punctuation(self):
        score = title_similarity(
            "BERT: Pre-training of Deep Bidirectional Transformers",
            "BERT — Pre Training of Deep Bidirectional Transformers",
        )

        self.assertGreaterEqual(score, 0.95)

    def test_log_failed_downloads_removes_duplicates(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder, "failed.txt")

            log_failed_downloads(["first", "second", "first"], output)

            self.assertEqual(output.read_text(encoding="utf-8"), "first\nsecond\n")

    def test_log_failed_downloads_clears_stale_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder, "failed.txt")
            output.write_text("old failure\n", encoding="utf-8")

            log_failed_downloads([], output)

            self.assertEqual(output.read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
