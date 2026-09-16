import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from doi_hunter.htmlparser import extract_citation_metadata, extract_scihub_embed_link
from doi_hunter.utils import download_file, get_doi_by_title, log_failed_downloads


class UtilsTests(unittest.TestCase):
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

            self.assertEqual(result, "success")
            self.assertEqual(output.read_bytes(), b"%PDF-test")

    @patch("doi_hunter.utils.requests.get")
    def test_download_file_skips_existing_file(self, mock_get):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "Paper.pdf").write_bytes(b"existing")

            result = download_file("https://example.test/paper", "Paper", folder)

            self.assertEqual(result, "skipped")
            mock_get.assert_not_called()

    @patch("doi_hunter.utils.requests.get")
    def test_get_doi_by_title_uses_crossref_parameters(self, mock_get):
        response = Mock(status_code=200)
        response.json.return_value = {
            "message": {"items": [{"DOI": "10.1234/example"}]}
        }
        mock_get.return_value = response

        doi = get_doi_by_title("Wind & solar forecasting")

        self.assertEqual(doi, "10.1234/example")
        self.assertEqual(
            mock_get.call_args.kwargs["params"]["query.bibliographic"],
            "Wind & solar forecasting",
        )

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
