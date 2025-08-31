#!/usr/bin/env python3
import re
import sys
from typing import cast

import niquests
from bs4 import BeautifulSoup
from bs4.element import Tag


def convert_alpine_package_url(package_url: str, arch_override: str | None = None) -> str:  # noqa: PLR0915
    match = re.match(
        r"https://pkgs\.alpinelinux\.org/package/([^/]+)/([^/]+)/([^/]+)/([^/]+)",
        package_url,
    )
    if not match:
        msg = (
            "Invalid Alpine Package URL format. Expected format: "
            "https://pkgs.alpinelinux.org/package/branch/repository/architecture/package-name"
        )
        raise ValueError(msg)

    branch, repository, architecture, package_name = match.groups()

    if arch_override:
        architecture = arch_override

    try:
        response = niquests.get(package_url, timeout=10)
        response.raise_for_status()
    except niquests.exceptions.RequestException as e:
        msg = f"Failed to fetch package page: {e}"
        raise ValueError(msg) from e

    if response.text is not None:
        html_text = response.text
    else:
        html_text = cast("bytes", response.content).decode("utf-8", errors="replace")
    soup = BeautifulSoup(html_text, "html.parser")

    version: str | None = None

    package_table = soup.find("table", class_="package-details")
    if package_table is None:
        for table in soup.find_all("table"):
            if isinstance(table, Tag) and table.find(string=re.compile(r"Version", re.IGNORECASE)):
                package_table = table
                break

    if isinstance(package_table, Tag):
        for row in package_table.find_all("tr"):
            if not isinstance(row, Tag):
                continue
            headers = [h for h in row.find_all("th") if isinstance(h, Tag)]
            cells = [c for c in row.find_all("td") if isinstance(c, Tag)]

            if headers and len(headers) > 0:
                header_text = headers[0].get_text(strip=True)
                if re.search(r"version", header_text, re.IGNORECASE) and cells and len(cells) > 0:
                    version = cells[0].get_text(strip=True)
                    break

    if not version:
        version_tag = soup.find(string=re.compile(r"Version\s*[:|=]\s*\d+\.\d+", re.IGNORECASE))
        if version_tag is not None:
            version_str = str(version_tag)
            version_match = re.search(r"(\d+\.\d+(\.\d+(-\w+)?)?)", version_str)
            if version_match:
                version = version_match.group(1)

    if not version:
        script_tags = soup.find_all("script", type="application/ld+json")
        for script in script_tags:
            if isinstance(script, Tag) and script.string:
                script_text = script.string
                if "version" in script_text.lower():
                    version_match = re.search(r'"version"\s*:\s*"([^"]+)"', script_text, re.IGNORECASE)
                    if version_match:
                        version = version_match.group(1)
                        break

    if not version:
        msg = "Could not find version on the package page. The page structure might have changed."
        raise ValueError(msg)

    version = re.sub(r"\s+", " ", version).strip()

    return f"http://dl-cdn.alpinelinux.org/alpine/{branch}/{repository}/{architecture}/{package_name}-{version}.apk"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: alpine-url-converter.py <package_url> [arch_override]")
        print(
            "Example: alpine-url-converter.py https://pkgs.alpinelinux.org/package/edge/community/x86/navi-zsh-plugin x86_64",
        )
        sys.exit(1)

    package_url = sys.argv[1]
    arch_override = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        download_url = convert_alpine_package_url(package_url, arch_override)
        print(download_url)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
