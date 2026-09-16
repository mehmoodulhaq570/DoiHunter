[![Version](https://img.shields.io/badge/version-1.1.1-blue)](https://github.com/mehmoodulhaq570/doi_hunter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Issues](https://img.shields.io/github/issues/mehmoodulhaq570/doi_hunter)](https://github.com/mehmoodulhaq570/doi_hunter/issues)

# DOI Hunter

DOI Hunter is a Python command-line tool that processes lists of research-paper
titles and DOIs and attempts to download their PDFs. Paper titles are resolved
to DOIs through Crossref, and downloaded files are stored with readable names.

Use the tool only for papers you are legally permitted to access and download.

## Features

- Accepts paper titles and DOI identifiers in the same input file.
- Resolves titles to DOIs through the Crossref API.
- Checks DOI publisher pages for an officially advertised PDF.
- Retains the project's legacy Sci-Hub lookup as a fallback.
- Processes large input files in configurable batches.
- Skips PDFs that already exist.
- Sanitizes filenames for Windows and other supported platforms.
- Records unsuccessful entries in `failed_downloads.txt`.
- Supports UTF-8, UTF-8 with BOM, Latin-1, and CP1252 input files.
- Applies network timeouts so unavailable services do not hang indefinitely.

## Requirements

- Python 3.7 or newer
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
python -m pip install -r requirements.txt
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

The included `paper_titles.txt` contains ten sample titles.

## Usage

From the repository directory, run:

```powershell
python -m doi_hunter paper_titles.txt --batch_size 5
```

If the package has been installed, the console command is also available:

```powershell
doi-hunter paper_titles.txt --batch_size 5
```

`--batch_size` defaults to `10`. Batches are processed sequentially; this
option does not enable parallel downloads.

## Download process

For each non-empty input line, DOI Hunter:

1. Uses the value directly when it begins with `10.`; otherwise it requests the
   first matching DOI from Crossref.
2. Resolves the DOI and checks the publisher page for `citation_pdf_url`
   metadata.
3. Downloads an accessible publisher PDF when one is advertised.
4. If that is unavailable, tries the legacy Sci-Hub HTML parsing path.
5. Saves a successful download in the `downloads` directory.
6. Records unsuccessful entries in `failed_downloads.txt`.

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
skipped, and failed entries.

## Development and tests

Run the test suite without making network requests:

```powershell
python -m unittest discover -s tests -v
```

See [CHANGELOG.md](CHANGELOG.md) for notable changes.

## License

DOI Hunter is distributed under the MIT License. See [LICENSE.txt](LICENSE.txt).

## Contributors

- [@Faisal-PCB](https://github.com/Faisal-PCB)
