import os
import shutil
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .paths import DRAFT_INFO, DRAFT_META

BACKUP_ROOT = Path.home() / ".capcut-kit/backups"
QUIT_TIMEOUT_S = 30.0
POLL_S = 0.25
BACKED_UP_FILES = (DRAFT_INFO, DRAFT_META)


class CapCutBusy(RuntimeError):
    pass


def capcut_running() -> bool:
    return subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0


def quit_capcut(timeout_s: float = QUIT_TIMEOUT_S) -> bool:
    if not capcut_running():
        return False
    subprocess.run(["osascript", "-e", 'quit app "CapCut"'], capture_output=True)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not capcut_running():
            return True
        time.sleep(POLL_S)
    raise CapCutBusy(
        "CapCut did not quit within "
        f"{timeout_s:.0f}s. It is probably exporting or showing a dialog. "
        "Finish that, quit CapCut manually, then re-run."
    )


def open_capcut() -> None:
    subprocess.run(["open", "-a", "CapCut"], capture_output=True)


@contextmanager
def capcut_closed(reopen: bool = True):
    was_running = quit_capcut()
    try:
        yield
    finally:
        if was_running and reopen:
            open_capcut()


def backup_dir(project: Path) -> Path:
    return BACKUP_ROOT / project.name


@dataclass(frozen=True)
class Backup:
    stamp: str
    path: Path
    created: float

    @property
    def age_s(self) -> float:
        return time.time() - self.created


def backup(project: Path) -> Backup:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = backup_dir(project) / stamp
    dest.mkdir(parents=True, exist_ok=True)
    for name in BACKED_UP_FILES:
        src = project / name
        if src.exists():
            shutil.copy2(src, dest / name)
    return Backup(stamp, dest, time.time())


def list_backups(project: Path) -> list[Backup]:
    base = backup_dir(project)
    if not base.is_dir():
        return []
    found = [
        Backup(p.name, p, p.stat().st_mtime)
        for p in base.iterdir()
        if p.is_dir() and (p / DRAFT_INFO).exists()
    ]
    return sorted(found, key=lambda b: b.stamp, reverse=True)


def restore(project: Path, stamp: str | None = None) -> Backup:
    backups = list_backups(project)
    if not backups:
        raise FileNotFoundError(f"no backups for {project.name} in {backup_dir(project)}")
    if stamp is None:
        chosen = backups[0]
    else:
        chosen = next((b for b in backups if b.stamp == stamp), None)
        if chosen is None:
            raise FileNotFoundError(f"no backup {stamp} for {project.name}")
    for name in BACKED_UP_FILES:
        src = chosen.path / name
        if src.exists():
            shutil.copy2(src, project / name)
    return chosen


def prune_backups(project: Path, keep: int) -> list[Backup]:
    backups = list_backups(project)
    dropped = backups[keep:]
    for b in dropped:
        shutil.rmtree(b.path, ignore_errors=True)
    return dropped


def atomic_write(path: Path, data: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    os.replace(tmp, path)
