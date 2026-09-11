from dataclasses import dataclass
from pathlib import Path

from .draft.builder import Clip
from .media.probe import MediaInfo, VIDEO_SUFFIXES, probe

ORDER_TIME = "time"
ORDER_NAME = "name"
LAYOUT_SEQUENCE = "sequence"
LAYOUT_SYNC = "sync"


@dataclass(frozen=True)
class Source:
    path: Path
    info: MediaInfo


def gather(folder: Path, suffixes: set[str] | None = None) -> list[Source]:
    allowed = suffixes or VIDEO_SUFFIXES
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in allowed)
    if not files:
        raise FileNotFoundError(f"no video files in {folder}")
    return [Source(path=p, info=probe(p)) for p in files]


def order(sources: list[Source], by: str = ORDER_TIME) -> list[Source]:
    if by == ORDER_NAME:
        return sorted(sources, key=lambda s: s.path.name)
    dated = [s for s in sources if s.info.created]
    if len(dated) != len(sources):
        return sorted(sources, key=lambda s: s.path.name)
    return sorted(sources, key=lambda s: s.info.created)


def group_by_device(sources: list[Source]) -> dict[str, list[Source]]:
    groups: dict[str, list[Source]] = {}
    for source in sources:
        groups.setdefault(source.info.device or "unknown", []).append(source)
    return groups


def primary_device(groups: dict[str, list[Source]]) -> str:
    return max(groups, key=lambda name: sum(s.info.duration_s for s in groups[name]))


def device_track_order(groups: dict[str, list[Source]]) -> list[str]:
    primary = primary_device(groups)
    others = sorted(name for name in groups if name != primary)
    return [primary, *others]


class NoTimestamps(ValueError):
    pass


def lanes_for(sources: list[Source]) -> list[list[Source]]:
    lanes: list[list[Source]] = []
    lane_ends: list[float] = []
    for source in sorted(sources, key=lambda s: s.info.created):
        start = source.info.created.timestamp()
        end = start + source.info.duration_s
        for index, lane_end in enumerate(lane_ends):
            if lane_end <= start:
                lanes[index].append(source)
                lane_ends[index] = end
                break
        else:
            lanes.append([source])
            lane_ends.append(end)
    return lanes


def align(sources: list[Source]) -> tuple[list[Clip], list[str]]:
    undated = [s.path.name for s in sources if s.info.created is None]
    if undated:
        raise NoTimestamps(
            f"{len(undated)} files have no recording time, so they cannot be placed on a "
            f"shared timeline: {', '.join(undated[:4])}. Use --layout sequence instead."
        )
    groups = group_by_device(sources)
    origin = min(s.info.created for s in sources)
    clips: list[Clip] = []
    notes: list[str] = []
    track = 0
    for device in device_track_order(groups):
        lanes = lanes_for(groups[device])
        if len(lanes) > 1:
            notes.append(
                f"{device} has clips that overlap in time, so it needed "
                f"{len(lanes)} tracks. Duplicate or re-exported files are the usual cause."
            )
        for lane in lanes:
            for source in lane:
                offset = (source.info.created - origin).total_seconds()
                clips.append(Clip(path=source.path, source_start_s=0.0,
                                  duration_s=source.info.duration_s,
                                  target_start_s=offset, track=track))
            track += 1
    return clips, notes


def coverage(clips: list[Clip]) -> tuple[float, float]:
    if not clips:
        return 0.0, 0.0
    span = max((c.target_start_s or 0.0) + (c.duration_s or 0.0) for c in clips)
    by_track: dict[int, list[Clip]] = {}
    for clip in clips:
        by_track.setdefault(clip.track, []).append(clip)
    filled = 0.0
    for track_clips in by_track.values():
        filled = max(filled, sum(c.duration_s or 0.0 for c in track_clips))
    return span, span - filled


def to_clips(sources: list[Source], *, trim_start_s: float = 0.0,
             trim_end_s: float = 0.0, max_clip_s: float | None = None,
             track: int = 0) -> list[Clip]:
    clips = []
    cursor = 0.0
    for source in sources:
        available = source.info.duration_s - trim_start_s - trim_end_s
        if available <= 0:
            continue
        duration = min(available, max_clip_s) if max_clip_s else available
        clips.append(Clip(path=source.path, source_start_s=trim_start_s,
                          duration_s=duration, target_start_s=cursor, track=track))
        cursor += duration
    return clips
