import contextlib
import shutil
import tarfile
import tempfile
from pathlib import Path


class ArchiveTempDir:
    def __init__(
        self,
        tmpdir: Path,
        download_path: Path,
        *,
        keep_tmp: bool,
        tmpdir_obj: tempfile.TemporaryDirectory | None,
    ):
        self.tmpdir = tmpdir
        self.download_path = download_path
        self.keep_tmp = keep_tmp
        self._tmpdir_obj = tmpdir_obj

    def _make_filter(self, target_dir: Path):
        abs_target = target_dir.resolve()

        def tar_filter(member: tarfile.TarInfo) -> tarfile.TarInfo | None:
            member_name = member.name.lstrip("/")

            parts = Path(member_name).parts
            if any(p == ".." for p in parts):
                return None

            if not (member.isreg() or member.isdir()):
                return None

            member.name = member_name
            member.uid = 0
            member.gid = 0
            member.uname = ""
            member.gname = ""

            candidate = (abs_target / member.name).resolve(strict=False)
            try:
                if not str(candidate).startswith(str(abs_target)):
                    return None
            except Exception:  # noqa: BLE001
                return None

            return member

        return tar_filter
    
    def get_archive_tree(self) -> str:
        if not self.download_path.exists():
            msg = "Downloaded archive file does not exist"
            raise FileNotFoundError(msg)

        members: list[str] = []
        with tarfile.open(self.download_path, "r:*") as tar:
            tar_filter = self._make_filter(self.tmpdir)
            for member in tar.getmembers():
                safe_member = tar_filter(member)
                if safe_member is None:
                    continue

                name = safe_member.name

                if name == ".PKGINFO":
                    continue
                if name.startswith(".SIGN.RSA") and name.endswith(".rsa.pub"):
                    continue
                if Path(name).name == self.download_path.name:
                    continue

                members.append(name if not safe_member.isdir() else f"{name.rstrip('/')}/")

        members.sort()
        tree: dict = {}
        for path in members:
            parts = Path(path).parts
            d = tree
            for part in parts:
                d = d.setdefault(part, {})

        def format_tree(d: dict, prefix: str = "") -> list[str]:
            lines = []
            items = sorted(d.items())
            for i, (name, subtree) in enumerate(items):
                connector = "└── " if i == len(items) - 1 else "├── "
                lines.append(prefix + connector + name)
                if subtree:
                    extension = "    " if i == len(items) - 1 else "│   "
                    lines.extend(format_tree(subtree, prefix + extension))
            return lines

        return "\n".join(format_tree(tree))


    def unpack_archive(self, extract_to: Path | None = None) -> Path:
        if extract_to is None:
            extract_to = self.tmpdir
        else:
            extract_to = Path(extract_to)
            extract_to.mkdir(parents=True, exist_ok=True)

        with tarfile.open(self.download_path, "r:*") as tar:
            tar_filter = self._make_filter(extract_to)
            for member in tar.getmembers():
                safe_member = tar_filter(member)
                if safe_member is None:
                    continue

                target_path = (extract_to / safe_member.name).resolve(strict=False)

                if not str(target_path).startswith(str(extract_to.resolve())):
                    continue

                if safe_member.isdir():
                    target_path.mkdir(parents=True, exist_ok=True)
                elif safe_member.isreg():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    fileobj = tar.extractfile(member)
                    if fileobj is None:
                        continue
                    with target_path.open("wb") as f_out:
                        shutil.copyfileobj(fileobj, f_out)
                    with contextlib.suppress(Exception):
                        target_path.chmod(safe_member.mode & 0o777)
                else:
                    continue

        return extract_to
    
    # TODO: full filepaths
    def get_file_list(self, *, full=False) -> list[str]:
        if not self.download_path.exists():
            msg = "Downloaded archive file does not exist"
            raise FileNotFoundError(msg)

        files: list[str] = []
        with tarfile.open(self.download_path, "r:*") as tar:
            tar_filter = self._make_filter(self.tmpdir)
            for member in tar.getmembers():
                safe_member = tar_filter(member)
                if safe_member is None:
                    continue

                name = safe_member.name

                if name == ".PKGINFO":
                    continue
                if name.startswith(".SIGN.RSA") and name.endswith(".rsa.pub"):
                    continue
                if Path(name).name == self.download_path.name:
                    continue

                if safe_member.isreg():
                    if full:
                        files.append(str(self.tmpdir / Path(name)))
                    else:
                        files.append(name)

        return sorted(files)

    def remove(self) -> None:
        if isinstance(self._tmpdir_obj, tempfile.TemporaryDirectory):
            self._tmpdir_obj.cleanup()
            self._tmpdir_obj = None
        else:
            with contextlib.suppress(Exception):
                shutil.rmtree(self.tmpdir)
    
