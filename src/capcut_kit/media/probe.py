import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

US = 1_000_000
VIDEO_SUFFIXES = {".mov", ".mp4", ".m4v", ".avi", ".mkv"}
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


class FFmpegMissing(RuntimeError):
    pass


def require_ffmpeg() -> None:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        raise FFmpegMissing(
            f"{' and '.join(missing)} not found on PATH. Install with: brew install ffmpeg"
        )


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    width: int
    height: int
    duration_us: int
    has_video: bool
    has_audio: bool
    created: datetime | None
    device: str | None

    @property
    def duration_s(self) -> float:
        return self.duration_us / US


def _run_ffprobe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def _parse_created(tags: dict) -> datetime | None:
    raw = tags.get("creation_time")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def probe(path: Path) -> MediaInfo:
    require_ffmpeg()
    data = _run_ffprobe(path)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    width = int(video.get("width", 0)) if video else 0
    height = int(video.get("height", 0)) if video else 0
    rotation = 0
    for side in (video or {}).get("side_data_list", []):
        if "rotation" in side:
            rotation = int(side["rotation"])
    if abs(rotation) % 180 == 90:
        width, height = height, width
    fmt = data.get("format", {})
    duration = float(fmt.get("duration", 0.0) or 0.0)
    tags = fmt.get("tags", {})
    return MediaInfo(
        path=path,
        width=width,
        height=height,
        duration_us=int(duration * US),
        has_video=video is not None,
        has_audio=audio is not None,
        created=_parse_created(tags),
        device=tags.get("com.apple.quicktime.model") or tags.get("encoder"),
    )


def probe_many(paths: list[Path]) -> dict[Path, MediaInfo]:
    return {p: probe(p) for p in paths}


def media_files(folder: Path, suffixes: set[str] | None = None) -> list[Path]:
    allowed = suffixes or (VIDEO_SUFFIXES | AUDIO_SUFFIXES)
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in allowed)
