import shutil
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from alpine_downloader.archive import ArchiveTempDir


def download_archive_to_tempdir(  # noqa: PLR0915
    url: str,
    timeout: int = 30,
    *,
    keep_tmp: bool = False,
    allowed_schemes: tuple = ("http", "https"),
) -> ArchiveTempDir:
    """
    Download archive into a temp dir under /tmp and return an ArchiveTempDir object that
    manages the tempdir and the downloaded file.

    :param url: what to download.
    :param timeout: timeout for urllib
    """
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme.lower() not in allowed_schemes:
        msg = f"URL scheme '{parsed_url.scheme}' not allowed. Allowed: {allowed_schemes}"
        raise ValueError(msg)

    if keep_tmp:
        tmpdir = Path(tempfile.mkdtemp(dir="/tmp"))
        tmpdir_obj = None
    else:
        tmpdir_obj = tempfile.TemporaryDirectory(dir="/tmp")
        tmpdir = Path(tmpdir_obj.name)

    p = urllib.parse.urlparse(url)
    if p.scheme.lower() not in ("http", "https"):
        msg = "scheme not allowed"
        raise ValueError(msg)

    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib/3"})  # noqa: S310
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        final_url = resp.geturl()
        parsed = urllib.parse.urlparse(final_url)
        filename = Path(parsed.path).name or "downloaded"
        out_path = tmpdir / filename

        with out_path.open("wb") as out_f:
            shutil.copyfileobj(resp, out_f)

    return ArchiveTempDir(tmpdir=tmpdir, download_path=out_path, keep_tmp=keep_tmp, tmpdir_obj=tmpdir_obj)
