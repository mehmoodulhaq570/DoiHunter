# Changelog

All notable changes to DOI Hunter are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and released versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Restored the missing `doi_hunter.utils` module required by the CLI.
- Added DOI publisher-page resolution and `citation_pdf_url` extraction.
- Added an official publisher PDF attempt before the legacy fallback.
- Added request timeouts for DOI lookup and PDF downloads.
- Added automated tests for downloads, existing-file detection, Crossref
  parameters, citation metadata, relative PDF URLs, and failure logging.
- Added ten sample research-paper titles to `paper_titles.txt`.

### Changed

- Crossref searches now pass titles as encoded request parameters and request
  only the first result.
- Relative PDF links are now resolved consistently, including `/uptodate/`
  paths and protocol-relative URLs.
- PDF filenames are sanitized and no longer gain a second `.pdf` suffix when a
  rate-limited request is retried.
- Duplicate failures retain their original order when written to disk.
- A successful run now clears stale entries from `failed_downloads.txt`.
- README instructions now describe source installation, CLI usage, output,
  download order, limitations, and test execution.

### Fixed

- Fixed the `ModuleNotFoundError: No module named 'doi_hunter.utils'` startup
  failure.
- Fixed stale failure-log notices appearing after successful runs.
- Fixed malformed relative download URLs that previously caused request errors.

## [1.1.1] - 2025-05-05

### Changed

- Updated package metadata and build files for the 1.1.1 release.
- Added handling for protocol-relative Sci-Hub URLs.
- Expanded input-file encoding handling.

## [1.1.0]

### Added

- Batch processing of DOI and title lists.
- Crossref title-to-DOI lookup.
- PDF filename generation and failed-download logging.
