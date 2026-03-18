#!/usr/bin/env python3
"""Download ESA/Hubble images from direct or brute-forced CDN image URLs."""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import string
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

DEFAULT_INPUT_FILE = "urls.txt"
DEFAULT_OUTPUT_DIR = "downloads"
DEFAULT_TIMEOUT = 120
DEFAULT_WORKERS = 4
DEFAULT_SUFFIX_CHARSET = string.ascii_lowercase + string.digits
CHUNK_SIZE = 1024 * 1024
USER_AGENT = "ESAHubbleBotDownloader/1.1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download ESA/Hubble images from direct or brute-forced CDN links.",
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
    parser.add_argument(
        "--bruteforce-last-char",
        action="store_true",
        help=(
            "For each URL, replace the final character before the file extension with "
            "every character in --suffix-charset and try those URLs too."
        ),
    )
    parser.add_argument(
        "--suffix-charset",
        default=DEFAULT_SUFFIX_CHARSET,
        help=(
            "Characters to try when --bruteforce-last-char is enabled "
            f"(default: {DEFAULT_SUFFIX_CHARSET})."
        ),
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


def expand_url_last_char(url: str, charset: str) -> list[str]:
    parsed = urlparse(url)
    path = Path(parsed.path)
    stem = path.stem
    suffix = path.suffix

    if len(stem) < 2:
        return [url]

    base_stem = stem[:-1]
    expanded_urls: list[str] = [url]
    seen: set[str] = {url}

    for char in charset:
        candidate_name = f"{base_stem}{char}{suffix}"
        candidate_path = str(path.with_name(candidate_name))
        candidate_url = urlunparse(parsed._replace(path=candidate_path))
        if candidate_url in seen:
            continue
        seen.add(candidate_url)
        expanded_urls.append(candidate_url)

    return expanded_urls


def expand_urls(urls: Iterable[str], bruteforce_last_char: bool, charset: str) -> list[str]:
    normalized_charset = "".join(dict.fromkeys(charset))
    if bruteforce_last_char and not normalized_charset:
        raise ValueError("--suffix-charset must contain at least one character.")

    expanded_urls: list[str] = []
    seen: set[str] = set()

    for url in urls:
        candidates = [url]
        if bruteforce_last_char:
            candidates = expand_url_last_char(url, normalized_charset)

        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            expanded_urls.append(candidate)

    return expanded_urls


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
        urls = expand_urls(urls, args.bruteforce_last_char, args.suffix_charset)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    if not urls:
        print("Error: no valid URLs were provided.")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    max_workers = max(1, args.workers)
    mode = "brute-force mode" if args.bruteforce_last_char else "direct mode"
    print(
        f"Downloading {len(urls)} image(s) into '{output_dir.resolve()}' using {mode}...",
    )

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
