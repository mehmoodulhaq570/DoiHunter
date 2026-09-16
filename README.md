[![Tests](https://github.com/mehmoodulhaq570/DoiHunter/actions/workflows/tests.yml/badge.svg)](https://github.com/mehmoodulhaq570/DoiHunter/actions/workflows/tests.yml)
[![Version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/mehmoodulhaq570/DoiHunter)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Issues](https://img.shields.io/github/issues/mehmoodulhaq570/DoiHunter)](https://github.com/mehmoodulhaq570/DoiHunter/issues)

# DOI Hunter

DOI Hunter is a Python command-line tool that processes lists of research-paper
titles and DOIs and attempts to download their PDFs. Paper titles are resolved
to DOIs through Crossref, and downloaded files are stored with readable names.

Use the tool only for papers you are legally permitted to access and download.

## Quick start

```powershell
python -m pip install doi_hunter
doi-hunter papers.txt --batch-size 5
```

Create `papers.txt` with one DOI or paper title per line. PDFs are written to
`downloads/`, and entries that could not be downloaded are recorded in
`failed_downloads.txt`.

## Features

- Accepts paper titles and DOI identifiers in the same input file.
- Combines and ranks title candidates from Crossref, OpenAlex, and arXiv while
  rejecting weak or misleading matches.
- Checks publisher metadata, Unpaywall, OpenAlex, Europe PMC, and arXiv for
  available PDFs.
- Retains the project's legacy Sci-Hub lookup as a fallback.
- Processes large input files in configurable batches.
- Skips PDFs that already exist.
- Sanitizes filenames for Windows and other supported platforms.
- Records unsuccessful entries in `failed_downloads.txt`.
- Supports UTF-8, UTF-8 with BOM, Latin-1, and CP1252 input files.
- Validates the `%PDF-` signature instead of saving HTML error pages as PDFs.
- Uses persistent HTTP sessions, bounded retries, timeouts, temporary files,
  and atomic replacement.
- Handles Ctrl+C gracefully, removes partial downloads, and prints a stopped
  status without a Python traceback.
- Reports the specific reason for every failed entry.

## Requirements

- Python 3.10 or newer
- `requests`
- `beautifulsoup4`

## Installation

Install the published package:

```powershell
python -m pip install doi_hunter
```

To run the current source checkout instead:

```powershell
cd D:\Projects\DoiHunter
python -m pip install -e .
```

## Input file

Create a text file containing one title or DOI per line. Blank lines are
ignored. An entry beginning with `10.` is treated as a DOI; other entries are
treated as titles.

Example:

```text
Attention Is All You Need
10.1371/journal.pmed.0020124
Long Short-Term Memory
```

The included `examples/paper_titles.txt` contains ten sample titles.

## Usage

From the repository directory, run:

```powershell
python -m doi_hunter examples/paper_titles.txt --batch-size 5
```

If the package has been installed, the console command is also available:

```powershell
doi-hunter examples/paper_titles.txt --batch-size 5
```

The older `--batch_size` spelling remains available for compatibility. Batches
are processed sequentially; this option does not enable parallel downloads.

Useful options:

```text
--output DIRECTORY             PDF destination (default: downloads)
--retries NUMBER               retries for temporary errors (default: 3)
--timeout SECONDS              request timeout (default: 30)
--minimum-title-score SCORE    title-match threshold from 0 to 1 (default: 0.92)
--email ADDRESS                enables the Unpaywall API
--no-legacy-fallback           disables the legacy fallback source
--verbose                      repeats failure details after the summary
```

Unpaywall requires an email address. Supply it with `--email` or set the
`DOI_HUNTER_EMAIL` environment variable:

```powershell
$env:DOI_HUNTER_EMAIL = "researcher@example.com"
python -m doi_hunter examples/paper_titles.txt --output downloads --retries 3
```

## Download process

For each non-empty input line, DOI Hunter:

1. Uses the value directly when it begins with `10.`. For a title, it combines
   candidates from Crossref, OpenAlex, and arXiv and accepts only a sufficiently
   similar, well-supported match.
2. Checks the publisher page, Unpaywall (when configured), OpenAlex, Europe
   PMC, and arXiv in that order.
3. Tries unique candidate PDF URLs until one returns a valid PDF.
4. Optionally tries the project's legacy direct-embed fallback last.
5. Writes data to a `.part` file, validates its PDF signature, and atomically
   moves it into the selected output directory.
6. Records unsuccessful identifiers in `failed_downloads.txt` and prints a
   source-specific explanation.

Publisher downloads normally work only when the PDF is openly accessible or
the current environment is already authorized to access it. External sites may
be unavailable, blocked, or change their HTML without notice.

## Output

Downloaded papers are written to:

```text
downloads/
```

Failures are written to:

```text
failed_downloads.txt
```

The failure file is cleared after a run with no failures. Operational errors
are written to `error.log`, and each run ends with counts for downloaded,
skipped, and failed entries. Progress uses the overall input count even when
multiple batches are processed. Failure reasons appear while each entry is
processed; pass `--verbose` to repeat all reasons after the summary. The run
ends with the failed-download log location and a completion message.

## Development and tests

Install the source checkout with development tools:

```powershell
git clone https://github.com/mehmoodulhaq570/DoiHunter.git
cd DoiHunter
python -m pip install -e ".[dev]"
```

Run the test suite without making live network requests:

```powershell
python -m unittest discover -s tests -v
```

The [GitHub Actions workflow](.github/workflows/tests.yml) runs the same tests
on Python 3.10 through 3.14 for every push and pull request. On Python 3.14 it
also builds and validates the wheel and source archive. CI does not publish a
package or download research papers.

## Repository layout

```text
DoiHunter/
├── .github/workflows/tests.yml   Automated tests and package validation
├── doi_hunter/                   Application source code
├── examples/paper_titles.txt     Sample input list
├── tests/                        Offline automated tests
├── CHANGELOG.md                  Release history
├── README.md                     Usage and development documentation
├── SECURITY.md                   Private vulnerability-reporting process
├── pyproject.toml                Build-system configuration
├── setup.cfg                     Package metadata and dependencies
└── setup.py                      Compatibility build entry point
```

Generated build output, downloaded PDFs, caches, and runtime logs are excluded
from version control.

See [CHANGELOG.md](CHANGELOG.md) for notable changes.

Security issues should be reported privately as described in
[SECURITY.md](SECURITY.md).

## License

DOI Hunter is distributed under the MIT License. See [LICENSE.txt](LICENSE.txt).

## Contributors

- [@Faisal-PCB](https://github.com/Faisal-PCB)
