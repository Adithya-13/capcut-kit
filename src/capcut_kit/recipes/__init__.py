import tomllib
from pathlib import Path

from ..analysis.events import EventProfile

BUILTIN_DIR = Path(__file__).parent
USER_DIR = Path.home() / ".capcut-kit/recipes"


def search_paths() -> list[Path]:
    return [USER_DIR, BUILTIN_DIR]


def available() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for directory in reversed(search_paths()):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.toml")):
            found[path.stem] = path
    return found


def load(name: str) -> EventProfile:
    known = available()
    path = Path(name).expanduser()
    if path.suffix == ".toml" and path.is_file():
        return _from_file(path)
    if name not in known:
        options = ", ".join(sorted(known)) or "none installed"
        raise LookupError(f"no recipe called '{name}'. Available: {options}")
    return _from_file(known[name])


def _from_file(path: Path) -> EventProfile:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    fields = {f: data[f] for f in EventProfile.__dataclass_fields__ if f in data}
    fields["name"] = data.get("name", path.stem)
    return EventProfile(**fields)
