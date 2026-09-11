from pathlib import Path

from .audio import VAD_SR, require_analysis_extras, wav_for

DEFAULT_PAD_S = 0.25
DEFAULT_MERGE_GAP_S = 0.6
MIN_SILENCE_MS = 200

_model = None


def _load_model():
    global _model
    if _model is None:
        from silero_vad import load_silero_vad

        _model = load_silero_vad(onnx=True)
    return _model


def merge(intervals: list[tuple[float, float]], gap_s: float) -> list[tuple[float, float]]:
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if merged and start - merged[-1][1] <= gap_s:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def detect(source: Path, *, pad_s: float = DEFAULT_PAD_S,
           merge_gap_s: float = DEFAULT_MERGE_GAP_S) -> list[tuple[float, float]]:
    require_analysis_extras()
    import soundfile as sf
    import torch
    from silero_vad import get_speech_timestamps

    samples, _ = sf.read(str(wav_for(source, VAD_SR)), dtype="float32")
    duration_s = len(samples) / VAD_SR
    raw = get_speech_timestamps(
        torch.from_numpy(samples), _load_model(), sampling_rate=VAD_SR,
        return_seconds=True, min_silence_duration_ms=MIN_SILENCE_MS,
    )
    padded = [
        (max(0.0, seg["start"] - pad_s), min(duration_s, seg["end"] + pad_s))
        for seg in raw
    ]
    return merge(padded, merge_gap_s)


def spoken_seconds(intervals: list[tuple[float, float]]) -> float:
    return sum(end - start for start, end in intervals)
