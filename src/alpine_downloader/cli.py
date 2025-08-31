import argparse
import sys
from pathlib import Path

from alpine_downloader.downloader import download_archive_to_tempdir
from alpine_downloader.link_parser import convert_alpine_package_url

ARCHES_OVERWRITE = ["x86", "x86_64", "aarch64", "armhf", "armv7", "ppc64le", "s390x", "riscv64"]


def process(
    url: str,
    *,
    silent: bool,
    verbose: bool,
    arch_override: str | None,
) -> list[str]:
    """
    Download + unpack one archive and return list of sensible files (relative paths).
    Does NOT print the list of sensible files; caller is responsible for final output.
    """
    package_url = convert_alpine_package_url(url, arch_override=arch_override)
    archive = download_archive_to_tempdir(package_url, keep_tmp=False)

    if verbose:
        print(f"\n[Processing] {url}")
        print("\n[Archive tree]")
        tree = archive.get_archive_tree()
        print(tree)

        confirm = input("\nProceed with unpacking? (Y/n): ").strip().lower()
        if confirm not in ("", "y", "yes"):
            print("[!] Skipping unpacking.")
            return []

    if not silent:
        print("\n[Unpacking archive...]")

    archive.unpack_archive()

    return archive.get_file_list(full=True)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Process archives from URLs.")
    parser.add_argument("urls", nargs="*", help="One or more archive URLs to process.")
    parser.add_argument("-f", "--file", type=Path, help="File containing URLs (one per line).")
    parser.add_argument("-s", "--silent", action="store_true", help="Only print sensible files, suppress other output.")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show archive tree and ask for confirmation before unpacking (overrides -s/--silent).",
    )
    parser.add_argument(
        "-a",
        "--arch",
        choices=ARCHES_OVERWRITE,
        help="Specify Alpine Linux architecture (default: None, in this will use one from given URL).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    urls = list(args.urls)
    if args.file:
        try:
            with args.file.open("r", encoding="utf-8") as f:
                urls.extend(line.strip() for line in f if line.strip())
        except OSError as e:
            print(f"[!] Could not read file: {e}")
            sys.exit(1)

    if not urls:
        parse_args(["-h"])
        sys.exit(1)

    all_files: list[str] = []
    for url in urls:
        try:
            files = process(url, silent=args.silent, verbose=args.verbose, arch_override=args.arch)
            all_files.extend(files)
        except Exception as e:  # noqa: BLE001
            print(f"[!] Error processing {url}: {e}", file=sys.stderr)

    # Deduplicate while preserving order
    seen = set()
    unique_files: list[str] = []
    for f in all_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    if not unique_files:
        print("[!] no sensible files found.")
        sys.exit(1)

    if not args.silent:
        print("\n[Downloaded sensible files:]")
    for file in unique_files:
        print(file)


if __name__ == "__main__":
    # print(convert_alpine_package_url("https://pkgs.alpinelinux.org/package/edge/community/x86/eza-fish-completion"))
    main()
