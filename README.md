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

The included start scripts automatically:

- increment the numeric portion of each seed filename,
- try every suffix letter for each number,
- and use 12 download workers in parallel.

## How numeric brute-force mode works

If you seed the downloader with a URL like:

```text
https://cdn.esahubble.org/archives/images/large/heic0715a.jpg
```

then numeric brute-force mode tries URLs in this order:

- `heic0715a.jpg`, `heic0715b.jpg`, `heic0715c.jpg`, ...
- `heic0716a.jpg`, `heic0716b.jpg`, `heic0716c.jpg`, ...
- `heic0717a.jpg`, `heic0717b.jpg`, `heic0717c.jpg`, ...

The default suffix charset is lowercase letters only: `abcdefghijklmnopqrstuvwxyz`.

The default number range is 25 consecutive values starting from the seed number. For example, `heic0715a.jpg` with `--number-steps 25` tries from `0715` through `0739`.

## Editing the download list

Open `urls.txt` and add or remove seed URLs, one per line.

## Manual usage

Direct download only:

```bash
python3 download_hubble_images.py --input urls.txt
```

Suffix-only brute force on a fixed number:

```bash
python3 download_hubble_images.py --input urls.txt --bruteforce-last-char
```

Increment the number and try every suffix letter for each number:

```bash
python3 download_hubble_images.py --input urls.txt --increment-numbers --number-steps 25 --workers 12
```

Useful options:

- `--output-dir my-folder` to change the download folder.
- `--workers 12` to control how many downloads run in parallel.
- `--force` to re-download files that already exist.
- `--number-steps 100` to check more consecutive number combinations.
- `--suffix-charset abcdefghijklmnopqrstuvwxyz` to control which suffix letters are tried.
