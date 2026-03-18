#!/usr/bin/env python3
"""Download ESA/Hubble images from a list of direct image URLs."""

from __future__ import annotations

import argparse
import concurrent.futures
import os
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DEFAULT_INPUT_FILE = "urls.txt"
DEFAULT_OUTPUT_DIR = "downloads"
DEFAULT_TIMEOUT = 120
DEFAULT_WORKERS = 4
CHUNK_SIZE = 1024 * 1024
USER_AGENT = "ESAHubbleBotDownloader/1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download ESA/Hubble images from direct CDN links.",
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="Direct image URLs to download. If omitted, --input is used.",
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_FILE,
        help=f"Path to a text file with one URL per line (default: {DEFAULT_INPUT_FILE}).",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Folder where images are saved (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Number of downloads to run in parallel (default: {DEFAULT_WORKERS}).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds per request (default: {DEFAULT_TIMEOUT}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if they already exist.",
    )
    return parser.parse_args()


def normalize_urls(raw_urls: Iterable[str]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for raw_url in raw_urls:
        url = raw_url.strip()
        if not url or url.startswith("#"):
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)

    return urls


def load_urls(args: argparse.Namespace) -> list[str]:
    if args.urls:
        return normalize_urls(args.urls)

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(
            f"No URLs were provided and input file '{input_path}' was not found.",
        )

    return normalize_urls(input_path.read_text(encoding="utf-8").splitlines())


def filename_from_url(url: str) -> str:
    path_name = Path(urlparse(url).path).name
    if not path_name:
        raise ValueError(f"Could not determine filename from URL: {url}")
    return path_name



def download_one(
    url: str,
    output_dir: Path,
    timeout: int,
    force: bool,
) -> tuple[str, str]:
    filename = filename_from_url(url)
    destination = output_dir / filename

    if destination.exists() and not force:
        return (filename, "skipped (already exists)")

    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status >= 400:
                raise HTTPError(url, status, "HTTP error", response.headers, None)

            tmp_destination = destination.with_suffix(destination.suffix + ".part")
            with tmp_destination.open("wb") as output_file:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    output_file.write(chunk)
            os.replace(tmp_destination, destination)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return (filename, f"failed ({exc})")

    file_size = destination.stat().st_size
    return (filename, f"downloaded ({file_size:,} bytes)")



def main() -> int:
    args = parse_args()

    try:
        urls = load_urls(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    if not urls:
        print("Error: no valid URLs were provided.")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    max_workers = max(1, args.workers)
    print(f"Downloading {len(urls)} image(s) into '{output_dir.resolve()}'...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_one, url, output_dir, args.timeout, args.force): url
            for url in urls
        }
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                filename, status = future.result()
            except Exception as exc:  # noqa: BLE001
                filename = filename_from_url(url)
                status = f"failed ({exc})"
            print(f"- {filename}: {status}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
