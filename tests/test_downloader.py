import io
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from doi_hunter import __main__ as cli
from doi_hunter.downloader import (
    print_summary,
    process_papers,
    process_papers_in_batch,
)
from doi_hunter.models import DownloadResult


class DownloaderTests(unittest.TestCase):
    @patch("doi_hunter.downloader.log_failed_downloads")
    @patch(
        "doi_hunter.downloader.process_papers_in_batch",
        side_effect=KeyboardInterrupt,
    )
    @patch("doi_hunter.downloader._read_input_lines")
    @patch("doi_hunter.downloader.create_session")
    def test_keyboard_interrupt_stops_without_traceback(
        self,
        mock_create_session,
        mock_read,
        _mock_batch,
        _mock_log,
    ):
        session = Mock()
        mock_create_session.return_value = session
        mock_read.return_value = (["10.1/test"], "utf-8")
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as folder, redirect_stdout(output):
            result = process_papers("papers.txt", download_folder=folder)

        self.assertTrue(result["interrupted"])
        self.assertIn("DOI Hunter has stopped safely", output.getvalue())
        session.close.assert_called_once_with()

    @patch("doi_hunter.__main__.process_papers")
    @patch("sys.argv", ["doi-hunter", "papers.txt", "--verbose"])
    def test_cli_passes_verbose_to_process_papers(self, mock_process):
        cli.main()

        self.assertTrue(mock_process.call_args.kwargs["verbose"])

    def test_default_summary_does_not_repeat_failure_details(self):
        output = io.StringIO()
        with redirect_stdout(output):
            print_summary(
                2,
                1,
                0,
                [("Paper title", "long failure reason")],
                "failed_downloads.txt",
                1.25,
            )

        rendered = output.getvalue()
        self.assertIn("Total failed downloads: 1", rendered)
        self.assertIn(
            "Failed downloads have been logged in 'failed_downloads.txt':",
            rendered,
        )
        self.assertNotIn("long failure reason", rendered)
        self.assertTrue(rendered.rstrip().endswith("Thank you for using DoiHunter!"))

    def test_verbose_summary_repeats_failure_details(self):
        output = io.StringIO()
        with redirect_stdout(output):
            print_summary(
                1,
                0,
                0,
                [("Paper title", "long failure reason")],
                "failed_downloads.txt",
                1.0,
                verbose=True,
            )

        self.assertIn("Paper title: long failure reason", output.getvalue())

    @patch("doi_hunter.downloader.download_paper")
    def test_batch_progress_uses_overall_position(self, mock_download):
        mock_download.side_effect = [
            DownloadResult("success", source="test"),
            DownloadResult("failed", reason="no PDF"),
        ]
        failures = []
        details = []
        skipped = []
        output = io.StringIO()

        with redirect_stdout(output):
            downloaded = process_papers_in_batch(
                ["10.1/first", "10.1/second"],
                start_index=5,
                overall_total=10,
                failed_downloads=failures,
                failure_details=details,
                skipped_files=skipped,
                download_folder="downloads",
                session=Mock(),
                timeout=10,
                minimum_title_score=0.85,
                email=None,
                use_legacy_fallback=False,
            )

        self.assertEqual(downloaded, 1)
        self.assertIn("Processing [6/10]", output.getvalue())
        self.assertIn("Processing [7/10]", output.getvalue())
        self.assertEqual(failures, ["10.1/second"])
        self.assertEqual(details[0][1], "no PDF")


if __name__ == "__main__":
    unittest.main()
