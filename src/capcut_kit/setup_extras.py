import shutil
import subprocess
import sys
from pathlib import Path

ANALYSIS_EXTRA = "analysis"


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def install(extra: str) -> int:
    root = package_root()
    if not (root / "pyproject.toml").exists():
        print(f"error: cannot find the package source at {root}", file=sys.stderr)
        return 2
    target = f"{root}[{extra}]"
    uv = shutil.which("uv")
    if uv:
        command = [uv, "pip", "install", "--python", sys.executable, "-e", target]
    else:
        command = [sys.executable, "-m", "pip", "install", "-e", target]
    print(f"installing the {extra} extras, this takes a minute the first time...")
    return subprocess.run(command).returncode


def analysis_ready() -> bool:
    try:
        import silero_vad  # noqa: F401
        import soundfile  # noqa: F401
    except ImportError:
        return False
    return True
