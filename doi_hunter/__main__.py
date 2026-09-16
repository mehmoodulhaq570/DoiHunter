import argparse
import logging
import os

from .downloader import process_papers


def score(value):
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def positive_int(value):
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def nonnegative_int(value):
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("cannot be negative")
    return parsed


def build_parser():
    parser = argparse.ArgumentParser(description="DOI Hunter paper downloader")
    parser.add_argument("file_path", help="text file containing DOIs or paper titles")
    parser.add_argument(
        "--batch-size",
        "--batch_size",
        dest="batch_size",
        type=positive_int,
        default=10,
        help="entries per sequential batch (default: 10)",
    )
    parser.add_argument(
        "--output",
        default="downloads",
        help="directory for downloaded PDFs (default: downloads)",
    )
    parser.add_argument(
        "--retries",
        type=nonnegative_int,
        default=3,
        help="network retries for temporary errors (default: 3)",
    )
    parser.add_argument(
        "--timeout",
        type=positive_int,
        default=30,
        help="request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--minimum-title-score",
        type=score,
        default=0.92,
        help="minimum title similarity from 0 to 1 (default: 0.92)",
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("DOI_HUNTER_EMAIL"),
        help="email required by Unpaywall (or set DOI_HUNTER_EMAIL)",
    )
    parser.add_argument(
        "--no-legacy-fallback",
        action="store_true",
        help="disable the project's legacy fallback source",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="repeat detailed failure reasons after the summary",
    )
    return parser


def main():
    args = build_parser().parse_args()
    logging.basicConfig(
        filename="error.log",
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    process_papers(
        args.file_path,
        batch_size=args.batch_size,
        download_folder=args.output,
        retries=args.retries,
        timeout=args.timeout,
        minimum_title_score=args.minimum_title_score,
        email=args.email,
        use_legacy_fallback=not args.no_legacy_fallback,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
