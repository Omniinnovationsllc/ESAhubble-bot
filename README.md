# ESA Hubble image downloader

This repository contains a small Python script that downloads ESA/Hubble image URLs into a local `downloads/` folder.

## Included files

- `download_hubble_images.py` - main downloader script.
- `urls.txt` - starter URLs that act as seeds for direct downloads or brute-force expansion.
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

The included start scripts automatically enable brute-force mode, which swaps the final character before `.jpg` with many possible alternatives.

## How brute-force mode works

If you seed the downloader with a URL like:

```text
https://cdn.esahubble.org/archives/images/large/potw1345a.jpg
```

then brute-force mode will automatically try variants such as:

- `potw1345a.jpg`
- `potw1345b.jpg`
- `potw1345c.jpg`
- ...through the rest of the configured charset.

By default the charset is all lowercase letters plus digits: `abcdefghijklmnopqrstuvwxyz0123456789`.

## Editing the download list

Open `urls.txt` and add or remove seed URLs, one per line.

## Manual usage

Direct download only:

```bash
python3 download_hubble_images.py --input urls.txt
```

Brute-force the last character before the extension:

```bash
python3 download_hubble_images.py --input urls.txt --bruteforce-last-char
```

Useful options:

- `--output-dir my-folder` to change the download folder.
- `--workers 8` to download more files in parallel.
- `--force` to re-download files that already exist.
- `--suffix-charset abcdefghijklmnopqrstuvwxyz` to control which suffixes are tried.
