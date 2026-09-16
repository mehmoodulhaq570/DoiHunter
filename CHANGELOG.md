# Changelog

All notable changes to DOI Hunter are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and released versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.2.0] - 2026-09-16

### Changed

- Moved the sample title list to `examples/paper_titles.txt`.
- Centralized the package version in `doi_hunter.__version__`.
- Raised the supported Python version to 3.10 and added CI coverage through
  Python 3.14.
- Replaced the inactive Travis configuration with GitHub Actions.
- Updated the security reporting policy and removed generated/runtime files
  from version control.

### Added

- Restored the missing `doi_hunter.utils` module required by the CLI.
- Added DOI publisher-page resolution and `citation_pdf_url` extraction.
- Added discovery through publisher metadata, Unpaywall, OpenAlex, Europe PMC,
  and arXiv before the legacy fallback.
- Added persistent sessions, configurable retries, request timeouts, backoff,
  temporary downloads, and atomic file replacement.
- Added `%PDF-` signature validation to reject HTML and other invalid content.
- Added CLI options for output directory, retries, timeout, title threshold,
  Unpaywall email, and disabling the legacy fallback.
- Added source-specific failure reasons and overall progress numbering.
- Simplified the default final summary and added `--verbose` for repeating all
  failure reasons at the end of a run.
- Added graceful Ctrl+C handling with session shutdown, partial-file cleanup,
  a final summary, and a clear stopped-by-user message.
- Added automated tests for downloads, existing-file detection, Crossref
  parameters, citation metadata, relative PDF URLs, and failure logging.
- Added ten sample research-paper titles to `examples/paper_titles.txt`.

### Changed

- Title searches now combine Crossref, OpenAlex, and arXiv candidates, account
  for word order and exact-title collisions, and reject matches below a
  configurable similarity threshold.
- Relative PDF links are now resolved consistently, including `/uptodate/`
  paths and protocol-relative URLs.
- PDF filenames are sanitized and no longer gain a second `.pdf` suffix when a
  rate-limited request is retried.
- Duplicate failures retain their original order when written to disk.
- A successful run now clears stale entries from `failed_downloads.txt`.
- Consolidated package metadata in `setup.cfg`, corrected the misspelled
  configuration filename, synchronized the package version, and removed
  tracked bytecode caches.
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
