from dataclasses import dataclass
from pathlib import Path

from .draft.model import (
    US, Draft, material_index, media_entries, segment_label, segments_of, timeline_end_us,
)


@dataclass(frozen=True)
class TrackSummary:
    index: int
    kind: str
    role: str
    segment_count: int
    covered_us: int
    gap_us: int


@dataclass(frozen=True)
class Pacing:
    clip_count: int
    total_us: int
    shortest_us: int
    longest_us: int
    median_us: int
    cuts_per_minute: float


def track_summaries(draft: Draft) -> list[TrackSummary]:
    summaries = []
    for i, track in enumerate(draft.tracks):
        segs = segments_of(track)
        covered = sum(s["target_timerange"]["duration"] for s in segs)
        span = 0
        if segs:
            first = segs[0]["target_timerange"]["start"]
            last = segs[-1]["target_timerange"]["start"] + segs[-1]["target_timerange"]["duration"]
            span = last - first
        summaries.append(TrackSummary(
            index=i,
            kind=track.get("type", "?"),
            role="main" if track.get("flag") == 0 else "overlay",
            segment_count=len(segs),
            covered_us=covered,
            gap_us=max(0, span - covered),
        ))
    return summaries


def pacing(draft: Draft, track_index: int = 0) -> Pacing | None:
    if track_index >= len(draft.tracks):
        return None
    segs = segments_of(draft.tracks[track_index])
    if not segs:
        return None
    durations = sorted(s["target_timerange"]["duration"] for s in segs)
    total = sum(durations)
    minutes = total / US / 60
    return Pacing(
        clip_count=len(segs),
        total_us=total,
        shortest_us=durations[0],
        longest_us=durations[-1],
        median_us=durations[len(durations) // 2],
        cuts_per_minute=len(segs) / minutes if minutes else 0.0,
    )


def media_usage(draft: Draft) -> list[tuple[str, int, int, bool]]:
    index = material_index(draft)
    counts: dict[str, list] = {}
    for track in draft.tracks:
        for seg in segments_of(track):
            entry = index.get(seg.get("material_id", ""))
            if entry is None:
                continue
            path = entry[1].get("path")
            if not path:
                continue
            bucket = counts.setdefault(path, [0, 0])
            bucket[0] += 1
            bucket[1] += seg["target_timerange"]["duration"]
    return sorted(
        ((path, used[0], used[1], Path(path).exists()) for path, used in counts.items()),
        key=lambda row: row[2], reverse=True,
    )


def timeline_rows(draft: Draft, track_index: int) -> list[tuple[int, dict, str]]:
    index = material_index(draft)
    if track_index >= len(draft.tracks):
        return []
    return [
        (i, seg, segment_label(draft, seg, index))
        for i, seg in enumerate(segments_of(draft.tracks[track_index]))
    ]


def overview(draft: Draft) -> dict:
    return {
        "name": draft.name,
        "dir": str(draft.dir),
        "duration_us": timeline_end_us(draft),
        "tracks": len(draft.tracks),
        "media_panel_items": len(media_entries(draft)),
        "draft_version": draft.compat.draft_version,
        "format_tested": draft.compat.tested,
    }
