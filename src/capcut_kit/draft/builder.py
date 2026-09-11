import json
from dataclasses import dataclass, field
from pathlib import Path

from ..media.probe import MediaInfo, probe
from ..safety import atomic_write
from . import template
from .template import US

MIN_CLIP_US = 1000
ROUNDING_SLACK_US = 1000


@dataclass(frozen=True)
class Clip:
    path: Path
    source_start_s: float = 0.0
    duration_s: float | None = None
    target_start_s: float | None = None
    volume: float = 1.0
    track: int = 0


@dataclass
class BuildResult:
    dir: Path
    name: str
    clip_count: int
    duration_us: int
    tracks: int
    skipped: list[str] = field(default_factory=list)


class ProjectExists(FileExistsError):
    pass


def _canvas_size(infos: list[MediaInfo]) -> tuple[int, int]:
    sized = [i for i in infos if i.width and i.height]
    if not sized:
        return 1080, 1920
    counts: dict[tuple[int, int], int] = {}
    for info in sized:
        key = (info.width, info.height)
        counts[key] = counts.get(key, 0) + 1
    return max(counts, key=lambda k: counts[k])


def _clip_ranges(clip: Clip, info: MediaInfo) -> tuple[int, int] | None:
    source_start = round(clip.source_start_s * US)
    if source_start >= info.duration_us:
        return None
    requested = info.duration_us - source_start
    if clip.duration_s is not None:
        requested = min(requested, round(clip.duration_s * US))
    if requested < MIN_CLIP_US:
        return None
    return source_start, requested


def build(name: str, clips: list[Clip], root: Path, *, fps: float = 30.0,
          width: int | None = None, height: int | None = None,
          overwrite: bool = False) -> BuildResult:
    if not clips:
        raise ValueError("no clips to build from")
    out_dir = root / name
    if out_dir.exists() and not overwrite:
        raise ProjectExists(
            f"a project named '{name}' already exists. Pick another name, or pass --overwrite."
        )

    infos = {path: probe(path) for path in dict.fromkeys(c.path for c in clips)}
    canvas_width, canvas_height = _canvas_size(list(infos.values()))
    draft = template.new_draft_info(name, width or canvas_width, height or canvas_height, fps)
    materials = draft["materials"]

    skipped: list[str] = []
    by_track: dict[int, list[Clip]] = {}
    for clip in clips:
        by_track.setdefault(clip.track, []).append(clip)

    timeline_end = 0
    for render_index, track_number in enumerate(sorted(by_track)):
        segments = []
        cursor = 0
        for clip in by_track[track_number]:
            info = infos[clip.path]
            ranges = _clip_ranges(clip, info)
            if ranges is None:
                skipped.append(clip.path.name)
                continue
            source_start, duration = ranges
            target_start = (cursor if clip.target_start_s is None
                            else round(clip.target_start_s * US))
            behind = cursor - target_start
            if 0 < behind <= ROUNDING_SLACK_US:
                target_start = cursor
            material = template.video_material(
                str(clip.path), clip.path.name, info.duration_us,
                info.width, info.height, info.has_audio,
            )
            materials["videos"].append(material)
            extra_refs = []
            for category in template.EXTRA_CATEGORIES:
                extra = template.EXTRA_BUILDERS[category]()
                materials[category].append(extra)
                extra_refs.append(extra["id"])
            segments.append(template.video_segment(
                material["id"], extra_refs, source_start, duration,
                target_start, render_index, clip.volume,
            ))
            cursor = target_start + duration
            timeline_end = max(timeline_end, cursor)
        if segments:
            draft["tracks"].append(template.video_track(segments, main=render_index == 0))

    if not draft["tracks"]:
        raise ValueError("every clip was unusable; nothing to build")

    draft["duration"] = timeline_end
    meta = template.new_draft_meta(draft["id"], name, str(out_dir), str(root))
    meta["tm_duration"] = timeline_end
    panel = [
        template.media_panel_entry(str(path), path.name, info.duration_us,
                                   info.width, info.height)
        for path, info in infos.items()
    ]
    for group in meta["draft_materials"]:
        if group["type"] == 0:
            group["value"] = panel

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "Resources").mkdir(exist_ok=True)
    atomic_write(out_dir / "draft_info.json", json.dumps(draft, ensure_ascii=False))
    atomic_write(out_dir / "draft_meta_info.json", json.dumps(meta, ensure_ascii=False))

    return BuildResult(
        dir=out_dir, name=name, clip_count=sum(len(t["segments"]) for t in draft["tracks"]),
        duration_us=timeline_end, tracks=len(draft["tracks"]), skipped=skipped,
    )
