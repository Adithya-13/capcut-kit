import os
from pathlib import Path

DEFAULT_DRAFT_ROOT = Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft"
DRAFT_INFO = "draft_info.json"
DRAFT_META = "draft_meta_info.json"


def draft_root() -> Path:
    override = os.environ.get("CAPCUT_DRAFT_ROOT")
    return Path(override).expanduser() if override else DEFAULT_DRAFT_ROOT


def is_project_dir(path: Path) -> bool:
    return (path / DRAFT_INFO).is_file() and (path / DRAFT_META).is_file()


def list_projects(root: Path | None = None) -> list[Path]:
    base = root or draft_root()
    if not base.is_dir():
        return []
    found = [p for p in base.iterdir() if not p.name.startswith(".") and is_project_dir(p)]
    return sorted(found, key=lambda p: (p / DRAFT_INFO).stat().st_mtime, reverse=True)


def resolve_project(name: str, root: Path | None = None) -> Path:
    base = root or draft_root()
    direct = Path(name).expanduser()
    if is_project_dir(direct):
        return direct
    candidate = base / name
    if is_project_dir(candidate):
        return candidate
    matches = [p for p in list_projects(base) if name.lower() in p.name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(p.name for p in matches[:8])
        raise LookupError(f"'{name}' matches several projects: {names}")
    raise LookupError(f"project not found: {name} (looked in {base})")
