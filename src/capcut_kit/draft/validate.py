from dataclasses import dataclass
from pathlib import Path

from .model import (
    Draft, is_capcut_asset, material_index, media_entries, resolve_media_path,
    segments_of, timeline_end_us,
)

USER_MEDIA_CATEGORIES = ("videos", "audios")

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    message: str
    track: int | None = None
    segment: str | None = None


def _dangling_refs(draft: Draft, index: dict) -> list[Issue]:
    issues = []
    for t, track in enumerate(draft.tracks):
        for seg in segments_of(track):
            if seg.get("material_id") and seg["material_id"] not in index:
                issues.append(Issue(ERROR, "dangling-material",
                                    "segment points at a material that does not exist",
                                    t, seg.get("id")))
            missing = [r for r in seg.get("extra_material_refs", []) if r not in index]
            if missing:
                issues.append(Issue(ERROR, "dangling-extra-ref",
                                    f"{len(missing)} extra_material_refs do not resolve",
                                    t, seg.get("id")))
    return issues


def _timerange_problems(draft: Draft, index: dict) -> list[Issue]:
    issues = []
    for t, track in enumerate(draft.tracks):
        previous_end = None
        previous_id = None
        for seg in segments_of(track):
            target = seg.get("target_timerange", {})
            source = seg.get("source_timerange", {})
            start = target.get("start", 0)
            duration = target.get("duration", 0)
            if duration <= 0:
                issues.append(Issue(ERROR, "empty-segment",
                                    "segment has zero or negative duration", t, seg.get("id")))
            if previous_end is not None and start < previous_end:
                issues.append(Issue(ERROR, "overlap",
                                    f"segment starts before {previous_id} ends", t, seg.get("id")))
            previous_end = start + duration
            previous_id = seg.get("id")
            entry = index.get(seg.get("material_id", ""))
            if entry is None:
                continue
            material_duration = entry[1].get("duration")
            if isinstance(material_duration, int) and material_duration > 0 and source:
                source_end = source.get("start", 0) + source.get("duration", 0)
                if source_end > material_duration + 1000:
                    issues.append(Issue(ERROR, "source-out-of-range",
                                        "segment reads past the end of its source file",
                                        t, seg.get("id")))
    return issues


def _offline_media(draft: Draft, index: dict) -> list[Issue]:
    issues = []
    seen: set[str] = set()
    for _, material in index.values():
        raw = material.get("path")
        if not raw or raw in seen:
            continue
        seen.add(raw)
        if not resolve_media_path(draft, raw).exists():
            issues.append(Issue(ERROR, "offline-media", f"media file is missing: {raw}"))
    return issues


def _panel_gaps(draft: Draft, index: dict) -> list[Issue]:
    on_timeline = {
        material["path"]
        for category, material in index.values()
        if category in USER_MEDIA_CATEGORIES
        and material.get("path")
        and not is_capcut_asset(material["path"])
    }
    in_panel = {entry.get("file_Path") for entry in media_entries(draft)}
    missing = {p for p in on_timeline if p and p not in in_panel}
    if missing:
        return [Issue(WARNING, "not-in-media-panel",
                      f"{len(missing)} timeline files are absent from the media panel")]
    return []


def _duration_drift(draft: Draft, index: dict) -> list[Issue]:
    end = timeline_end_us(draft)
    if abs(draft.duration_us - end) > 1000:
        return [Issue(WARNING, "duration-drift",
                      "stored project duration disagrees with the timeline contents")]
    return []


def _orphan_materials(draft: Draft, index: dict) -> list[Issue]:
    referenced: set[str] = set()
    for track in draft.tracks:
        for seg in track.get("segments", []):
            if seg.get("material_id"):
                referenced.add(seg["material_id"])
            referenced.update(seg.get("extra_material_refs", []))
    orphans = [mid for mid, (category, _) in index.items()
               if mid not in referenced and category in USER_MEDIA_CATEGORIES]
    if orphans:
        return [Issue(WARNING, "orphan-material",
                      f"{len(orphans)} video/audio materials are not used by any segment")]
    return []


CHECKS = (
    _dangling_refs,
    _timerange_problems,
    _offline_media,
    _panel_gaps,
    _duration_drift,
    _orphan_materials,
)


def check(draft: Draft) -> list[Issue]:
    index = material_index(draft)
    issues: list[Issue] = []
    for check in CHECKS:
        issues.extend(check(draft, index))
    if not draft.compat.plausible:
        issues.append(Issue(WARNING, "untested-format", draft.compat.message))
    return issues


def errors(issues: list[Issue]) -> list[Issue]:
    return [i for i in issues if i.level == ERROR]
