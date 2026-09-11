from dataclasses import replace

from .analysis.activity import Window
from .draft.builder import Clip

MIN_KEPT_S = 0.1


def _clip_span(clip: Clip) -> tuple[float, float]:
    start = clip.target_start_s or 0.0
    return start, start + (clip.duration_s or 0.0)


def placements(clips: list[Clip]) -> list[tuple]:
    seen: dict[tuple, float] = {}
    for clip in clips:
        key = clip.path
        start = (clip.target_start_s or 0.0) - clip.source_start_s
        if key not in seen or start < seen[key]:
            seen[key] = start
    return [(path, offset) for path, offset in seen.items()]


def restrict(clips: list[Clip], windows: list[Window], *,
             min_kept_s: float = MIN_KEPT_S) -> list[Clip]:
    if not windows:
        return []
    ordered = sorted(windows, key=lambda w: w.start_s)
    kept: list[Clip] = []
    elapsed = 0.0
    for window in ordered:
        for clip in clips:
            clip_start, clip_end = _clip_span(clip)
            overlap_start = max(clip_start, window.start_s)
            overlap_end = min(clip_end, window.end_s)
            length = overlap_end - overlap_start
            if length < min_kept_s:
                continue
            kept.append(replace(
                clip,
                source_start_s=clip.source_start_s + (overlap_start - clip_start),
                duration_s=length,
                target_start_s=elapsed + (overlap_start - window.start_s),
            ))
        elapsed += window.duration_s
    return kept


def total_span_s(clips: list[Clip]) -> float:
    if not clips:
        return 0.0
    return max((c.target_start_s or 0.0) + (c.duration_s or 0.0) for c in clips)
