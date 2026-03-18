from __future__ import annotations

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

downloader = importlib.import_module("download_hubble_images")


def test_normalize_urls_removes_comments_and_duplicates() -> None:
    urls = downloader.normalize_urls(
        [
            "# comment",
            "",
            " https://cdn.esahubble.org/archives/images/large/potw1345a.jpg ",
            "https://cdn.esahubble.org/archives/images/large/potw1345a.jpg",
            "https://cdn.esahubble.org/archives/images/large/heic1608a.jpg",
        ],
    )

    assert urls == [
        "https://cdn.esahubble.org/archives/images/large/potw1345a.jpg",
        "https://cdn.esahubble.org/archives/images/large/heic1608a.jpg",
    ]


def test_filename_from_url_returns_path_leaf() -> None:
    filename = downloader.filename_from_url(
        "https://cdn.esahubble.org/archives/images/large/heic1608a.jpg",
    )

    assert filename == "heic1608a.jpg"


def test_load_urls_from_input_file(tmp_path: Path) -> None:
    input_file = tmp_path / "urls.txt"
    input_file.write_text(
        "https://cdn.esahubble.org/archives/images/large/potw1724a.jpg\n",
        encoding="utf-8",
    )

    args = downloader.argparse.Namespace(urls=[], input=str(input_file))

    urls = downloader.load_urls(args)

    assert urls == ["https://cdn.esahubble.org/archives/images/large/potw1724a.jpg"]
