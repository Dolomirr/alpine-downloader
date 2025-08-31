# alpine-downloader

Small CLI tool to automatically download and unpack Alpine Linux packages (NOT install!).

I wrote it for myself as exercise and because I like automating tasks that anyways takes only few seconds.

This tool does **not** install anything, it only parses links from `pkgs.alpinelinux.org`, resolve them to actual repository URL, downloads the archive, unpack it in /tmp and returns full filenames to valuable files (ignoring packaging info and other dist files.)

> TL;DR: give it one or more package archive URLs (or a file with URLs), it downloads and extracts them into a temporary folder and prints the paths. Nothing is installed on your system.


## Why I made this

I built this tool mainly so I could **easily download code completion files and similar helper files for different shells**. Also as small exercise.

## What it does

- Resolve `pkgs.alpinelinux.com` links to real repo URLs.
- Download package archives.
- Unpack archives into a temporary directory.
- Print full file paths of the unpacked files.


## Installation

Recommended way is with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install git+https://github.com/Dolomirr/alpine-downloader.git
```

Alternative:
```bash
# install
git clone https://github.com/Dolomirr/alpine-downloader.git
cd alpine-downloader
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .

# run
python -m alpine_downloader <args>
```


### Usage

---

```
usage: alpine-downloader [-h] [-f FILE] [-s] [-v] [-a {x86,x86_64,aarch64,armhf,armv7,ppc64le,s390x,riscv64}] [urls ...]

Process archives from URLs.

positional arguments:
  urls                  One or more archive URLs to process.

options:
  -h, --help            show this help message and exit
  -f, --file FILE       File containing URLs (one per line).
  -s, --silent          Only print sensible files, suppress other output.
  -v, --verbose         Show archive tree and ask for confirmation before unpacking(overrides -s/--silent).
  -a, --arch {x86,x86_64,aarch64,armhf,armv7,ppc64le,s390x,riscv64}
                        Specify Alpine Linux architecture (default: None, in this will use one from given URL).
```
