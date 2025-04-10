<<<<<<< HEAD
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/mehmoodulhaq570/doi_hunter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Issues](https://img.shields.io/github/issues/mehmoodulhaq570/doi_hunter)](https://github.com/mehmoodulhaq570/doi_hunter/issues)
[![Size](https://img.shields.io/github/repo-size/mehmoodulhaq570/doi_hunter.svg)](https://github.com/mehmooulhaq570/doi_hunter)
[![Downloads](https://img.shields.io/github/downloads/mehmoodulhaq570/doi_hunter/total.svg)](https://github.com/mehmoodulhaq570/doi_hunter/releases)

# DoiHunter

**DoiHunter** is a Python package that can helps researchers download research papers using DOIs (unique identification of researcher paper) or paper titles through Crossref and Sci-Hub. Whether you're conducting research or need specific papers quickly, DoiHunter simplifies the process by automating downloads.

## Features

- **Batch Download**: Download multiple research papers in one go using a list of DOIs or titles.
- **Title to DOI**: Retrieves DOIs using paper titles through the CrossRef API and downloads the corresponding papers.
- **Custom File Naming**: Automatically names files based on paper titles for easy identification.
- **Error Handling**: Logs failed downloads and provides detailed summaries after processing.

## Installation

1. First, ensure you have Python installed on your system.
2. Install the `doi_hunter` package using pip:

```bash
pip install doi_hunter
````

## Setup & Usage

### Step 1: Create a Directory and Paper Title List
- Create a directory with any name.
- Inside that directory, create a .txt file  form example paper_titles.txt.
- This file should contain a list of paper titles or DOIs, each on a new line.

**Example content for paper_titles.txt:**
- AI Ethics: Balancing Innovation with Privacy and Security in the Digital Age
- 10.1002/er.6529
- Prediction of daily global solar radiation using different machine learning algorithms: Evaluation and comparison

### Step 2: Run the Downloader
Navigate to your created directory, then run the following command:

```bash
python -m doi_hunter paper_titles.txt --batch_size=5
````
## Output
Once the download starts, you'll see the following output:

```bash
[INFO] Welcome to DoiHunter!
This tool helps you download research papers from Sci-Hub using DOIs or titles.
For more information and the source code, visit: https://github.com/mehmoodulhaq570

[INFO] Starting the download process...

Processing [1/3]: AI Ethics: Balancing Innovation with Privacy and Security in the Digital Age
[v] File downloaded successfully :)
Processing [2/3]: 10.1002/er.6529
[v] File already exists. Skipping download.

[SUMMARY]
Total papers in file: 2
Total successfully downloaded: 1
Total skipped files: 1
Total failed downloads: 0
````
**Summary of Logs**
At the end of the process, a summary is displayed showing the total number of papers processed, successfully downloaded, skipped (if they already exist), and failed downloads.

## Notes
The ```--batch_size``` option allows you to control how many papers are processed at once, useful for large datasets.
The doi of the research paper must start like this **10.1016/j.rser.2016.05.022**
Failed downloads are logged and can be retried later.

## Contributors
- [@Faisal-PCB](https://github.com/Faisal-PCB)


=======
[![Version](https://img.shields.io/badge/version-0.1.1-blue)](https://github.com/mehmoodulhaq570/doi_hunter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Issues](https://img.shields.io/github/issues/mehmoodulhaq570/doi_hunter)](https://github.com/mehmoodulhaq570/doi_hunter/issues)
[![Size](https://img.shields.io/github/repo-size/mehmoodulhaq570/doi_hunter.svg)](https://github.com/mehmooulhaq570/doi_hunter)
[![Downloads](https://img.shields.io/github/downloads/mehmoodulhaq570/doi_hunter/total.svg)](https://github.com/mehmoodulhaq570/doi_hunter/releases)

# DoiHunter

**DoiHunter** is a Python package that can helps researchers download research papers using DOIs (unique identification of researcher paper) or paper titles through Crossref and Sci-Hub. Whether you're conducting research or need specific papers quickly, DoiHunter simplifies the process by automating downloads.

## Features

- **Batch Download**: Download multiple research papers in one go using a list of DOIs or titles.
- **Title to DOI**: Retrieves DOIs using paper titles through the CrossRef API and downloads the corresponding papers.
- **Custom File Naming**: Automatically names files based on paper titles for easy identification.
- **Error Handling**: Logs failed downloads and provides detailed summaries after processing.

## Installation

1. First, ensure you have Python installed on your system.
2. Install the `doi_hunter` package using pip:

```bash
pip install doi_hunter
````

## Setup & Usage

### Step 1: Create a Directory and Paper Title List
- Create a directory with any name.
- Inside that directory, create a .txt file  form example paper_titles.txt.
- This file should contain a list of paper titles or DOIs, each on a new line.

**Example content for paper_titles.txt:**
- AI Ethics: Balancing Innovation with Privacy and Security in the Digital Age
- 10.1002/er.6529
- Prediction of daily global solar radiation using different machine learning algorithms: Evaluation and comparison

### Step 2: Run the Downloader
Navigate to your created directory, then run the following command:

```bash
python -m doi_hunter paper_titles.txt --batch_size=5
````
## Output
Once the download starts, you'll see the following output:

```bash
[INFO] Welcome to DoiHunter!
This tool helps you download research papers from Sci-Hub using DOIs or titles.
For more information and the source code, visit: https://github.com/mehmoodulhaq570

[INFO] Starting the download process...

Processing [1/3]: AI Ethics: Balancing Innovation with Privacy and Security in the Digital Age
[v] File downloaded successfully :)
Processing [2/3]: 10.1002/er.6529
[v] File already exists. Skipping download.

[SUMMARY]
Total papers in file: 2
Total successfully downloaded: 1
Total skipped files: 1
Total failed downloads: 0
````
**Summary of Logs**
At the end of the process, a summary is displayed showing the total number of papers processed, successfully downloaded, skipped (if they already exist), and failed downloads.

## Notes
The ```--batch_size``` option allows you to control how many papers are processed at once, useful for large datasets.
The doi of the research paper must start like this **10.1016/j.rser.2016.05.022**
Failed downloads are logged and can be retried later.

## Contributors
- [@Faisal-PCB](https://github.com/Faisal-PCB)


>>>>>>> 23ac95e (Updated the version to the)
