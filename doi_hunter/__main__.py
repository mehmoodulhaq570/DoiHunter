<<<<<<< HEAD
# paper_downloader/__main__.py
import argparse
from .downloader import process_papers

def main():
    parser = argparse.ArgumentParser(description="DoiHunter CLI")
    parser.add_argument("file_path", help="Path to the input file with DOIs or titles")
    parser.add_argument("--batch_size", type=int, default=10, help="Number of papers to process per batch")
    args = parser.parse_args()

    process_papers(args.file_path, args.batch_size)

if __name__ == "__main__":
    main()
=======
# paper_downloader/__main__.py
import argparse
from .downloader import process_papers

def main():
    parser = argparse.ArgumentParser(description="DoiHunter CLI")
    parser.add_argument("file_path", help="Path to the input file with DOIs or titles")
    parser.add_argument("--batch_size", type=int, default=10, help="Number of papers to process per batch")
    args = parser.parse_args()

    process_papers(args.file_path, args.batch_size)

if __name__ == "__main__":
    main()
>>>>>>> 23ac95e (Updated the version to the)
