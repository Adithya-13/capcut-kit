import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..compat import Compat, probe as probe_compat
from ..paths import DRAFT_INFO, DRAFT_META
from ..safety import atomic_write

US = 1_000_000
MEDIA_MATERIAL_TYPE = 0
DRAFT_PATH_PREFIX = "##_draftpath_placeholder_"
CAPCUT_CACHE_MARKER = "Library/Containers/com.lemon.lvoverseas"


@dataclass
class Draft:
    dir: Path
    info: dict
    meta: dict
    compat: Compat = field(repr=False)

    @property
    def name(self) -> str:
        return self.info.get("name") or self.dir.name

    @property
    def tracks(self) -> list[dict]:
        return self.info.get("tracks", [])

    @property
    def duration_us(self) -> int:
        return int(self.info.get("duration", 0))


def load(project: Path) -> Draft:
    info = json.loads((project / DRAFT_INFO).read_text(encoding="utf-8"))
    meta = json.loads((project / DRAFT_META).read_text(encoding="utf-8"))
    return Draft(dir=project, info=info, meta=meta, compat=probe_compat(info))


def material_index(draft: Draft) -> dict[str, tuple[str, dict]]:
    index: dict[str, tuple[str, dict]] = {}
    for category, items in draft.info.get("materials", {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and "id" in item:
                index[item["id"]] = (category, item)
    return index


def segments_of(track: dict) -> list[dict]:
    return sorted(track.get("segments", []), key=lambda s: s["target_timerange"]["start"])


def all_segments(draft: Draft) -> list[tuple[dict, dict]]:
    return [(track, seg) for track in draft.tracks for seg in segments_of(track)]


def segment_source(draft: Draft, seg: dict, index: dict | None = None) -> Path | None:
    idx = index if index is not None else material_index(draft)
    entry = idx.get(seg.get("material_id", ""))
    if entry is None:
        return None
    path = entry[1].get("path")
    return Path(path) if path else None


def resolve_media_path(draft: Draft, raw: str) -> Path:
    if raw.startswith(DRAFT_PATH_PREFIX):
        return draft.dir / raw.split("##/", 1)[-1]
    return Path(raw)


def is_capcut_asset(raw: str) -> bool:
    return raw.startswith(DRAFT_PATH_PREFIX) or CAPCUT_CACHE_MARKER in raw


def segment_label(draft: Draft, seg: dict, index: dict | None = None) -> str:
    idx = index if index is not None else material_index(draft)
    entry = idx.get(seg.get("material_id", ""))
    if entry is None:
        return "<missing material>"
    category, material = entry
    path = material.get("path")
    if path:
        return Path(path).name
    return material.get("material_name") or material.get("name") or f"<{category}>"


def timeline_end_us(draft: Draft) -> int:
    ends = [
        seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
        for track in draft.tracks
        for seg in track.get("segments", [])
    ]
    return max(ends) if ends else 0


def media_entries(draft: Draft) -> list[dict]:
    return [
        value
        for group in draft.meta.get("draft_materials", [])
        if group.get("type") == MEDIA_MATERIAL_TYPE
        for value in group.get("value", [])
    ]


def save(draft: Draft, *, touch_times: bool = True) -> None:
    end = timeline_end_us(draft)
    draft.info["duration"] = end
    if touch_times:
        draft.info["update_time"] = int(time.time())
        draft.meta["tm_draft_modified"] = int(time.time() * US)
    draft.meta["tm_duration"] = end
    atomic_write(draft.dir / DRAFT_INFO, json.dumps(draft.info, ensure_ascii=False))
    atomic_write(draft.dir / DRAFT_META, json.dumps(draft.meta, ensure_ascii=False))
