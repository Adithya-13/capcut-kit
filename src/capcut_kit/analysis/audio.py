import hashlib
import subprocess
from pathlib import Path

from ..media.probe import require_ffmpeg

VAD_SR = 16000
ANALYSIS_SR = 48000
CACHE_ROOT = Path.home() / ".capcut-kit/audio-cache"


class AnalysisUnavailable(RuntimeError):
    pass


def require_analysis_extras() -> None:
    try:
        import numpy  # noqa: F401
        import silero_vad  # noqa: F401
        import soundfile  # noqa: F401
        import torch  # noqa: F401
    except ImportError as exc:
        raise AnalysisUnavailable(
            "this needs the audio analysis extras. Install them with:\n"
            "  capcut setup --analysis"
        ) from exc


def _cache_key(source: Path, sample_rate: int) -> str:
    stat = source.stat()
    raw = f"{source.resolve()}|{stat.st_size}|{int(stat.st_mtime)}|{sample_rate}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def wav_for(source: Path, sample_rate: int = VAD_SR) -> Path:
    require_ffmpeg()
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    target = CACHE_ROOT / f"{source.stem}.{_cache_key(source, sample_rate)}.wav"
    if target.exists():
        return target
    partial = target.with_suffix(".partial.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(source), "-vn", "-ac", "1",
         "-ar", str(sample_rate), str(partial)],
        check=True,
    )
    partial.replace(target)
    return target


def read_window(source: Path, start_s: float, duration_s: float,
                sample_rate: int = VAD_SR):
    require_ffmpeg()
    import numpy as np

    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, start_s):.3f}",
         "-i", str(source), "-t", f"{max(0.0, duration_s):.3f}",
         "-vn", "-ac", "1", "-ar", str(sample_rate),
         "-f", "f32le", "-"],
        check=True, capture_output=True,
    )
    return np.frombuffer(result.stdout, dtype=np.float32)


def clear_cache() -> int:
    if not CACHE_ROOT.is_dir():
        return 0
    files = list(CACHE_ROOT.glob("*.wav"))
    for path in files:
        path.unlink()
    return len(files)
