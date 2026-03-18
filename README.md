# ESA Hubble image downloader

This repository contains a small Python script that downloads a list of ESA/Hubble image URLs into a local `downloads/` folder.

## Included files

- `download_hubble_images.py` - main downloader script.
- `urls.txt` - the current list of image URLs to download.
- `start.sh` - quick-start launcher for Linux.
- `start.command` - double-click launcher for macOS.
- `start.bat` - double-click launcher for Windows.

## Quick start

### Linux

```bash
./start.sh
```

### macOS

Double-click `start.command`.

### Windows

Double-click `start.bat`.

## Editing the download list

Open `urls.txt` and add or remove direct image URLs, one per line.

## Manual usage

```bash
python3 download_hubble_images.py --input urls.txt
```

Useful options:

- `--output-dir my-folder` to change the download folder.
- `--workers 8` to download more files in parallel.
- `--force` to re-download files that already exist.
