import unittest
from unittest.mock import Mock

from doi_hunter.fulltext import (
    arxiv_candidates,
    europe_pmc_candidates,
    openalex_candidates,
    publisher_candidates,
    unpaywall_candidates,
)


class FullTextTests(unittest.TestCase):
    def test_publisher_candidate_from_citation_metadata(self):
        response = Mock(status_code=200, url="https://publisher.test/article")
        response.headers = {"Content-Type": "text/html"}
        response.text = (
            '<meta name="citation_title" content="Paper">'
            '<meta name="citation_pdf_url" content="https://publisher.test/p.pdf">'
        )
        session = Mock()
        session.get.return_value = response

        candidates, diagnostic = publisher_candidates(session, "10.1/test", 10)

        self.assertEqual(diagnostic, "")
        self.assertEqual(candidates[0].url, "https://publisher.test/p.pdf")

    def test_unpaywall_requires_email(self):
        candidates, diagnostic = unpaywall_candidates(
            Mock(), "10.1/test", 10, email=None
        )

        self.assertEqual(candidates, [])
        self.assertIn("--email", diagnostic)

    def test_openalex_uses_pdf_locations(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "title": "Paper",
            "best_oa_location": {"pdf_url": "https://repo.test/paper.pdf"},
            "locations": [],
        }
        session = Mock()
        session.get.return_value = response

        candidates, diagnostic = openalex_candidates(session, "10.1/test", 10)

        self.assertEqual(diagnostic, "")
        self.assertEqual(candidates[0].source, "OpenAlex")

    def test_europe_pmc_requires_open_access_record(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "resultList": {
                "result": [
                    {
                        "pmcid": "PMC123",
                        "isOpenAccess": "Y",
                        "title": "Paper",
                    }
                ]
            }
        }
        session = Mock()
        session.get.return_value = response

        candidates, diagnostic = europe_pmc_candidates(session, "10.1/test", 10)

        self.assertEqual(diagnostic, "")
        self.assertEqual(
            candidates[0].url,
            "https://europepmc.org/articles/PMC123?pdf=render",
        )

    def test_arxiv_extracts_pdf_link(self):
        response = Mock(status_code=200)
        response.content = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>A Paper</title>
            <link title="pdf" href="https://arxiv.org/pdf/1234.5678"/>
          </entry>
        </feed>"""
        session = Mock()
        session.get.return_value = response

        candidates, diagnostic = arxiv_candidates(session, "10.1/test", 10)

        self.assertEqual(diagnostic, "")
        self.assertEqual(candidates[0].source, "arXiv")


if __name__ == "__main__":
    unittest.main()
