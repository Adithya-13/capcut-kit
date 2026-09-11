from dataclasses import dataclass
from pathlib import Path

from .audio import VAD_SR, read_window, require_analysis_extras

ENV_HOP_S = 0.005
SEARCH_S = 10.0
MAX_PROBE_S = 60.0
MIN_PROBE_S = 3.0
MIN_CONFIDENCE = 5.0


@dataclass(frozen=True)
class Refinement:
    path: Path
    clock_offset_s: float
    offset_s: float
    confidence: float
    accepted: bool
    reason: str = ""

    @property
    def shift_s(self) -> float:
        return self.offset_s - self.clock_offset_s


def envelope(samples, sample_rate: int):
    import numpy as np

    hop = int(sample_rate * ENV_HOP_S)
    frames = len(samples) // hop
    if frames == 0:
        return np.zeros(0, dtype="float32")
    block = samples[: frames * hop].reshape(frames, hop)
    loudness = np.log10(np.sqrt((block ** 2).mean(axis=1)) + 1e-8)
    return (loudness - loudness.mean()) / (loudness.std() + 1e-8)


def best_offset(haystack, needle, sample_rate: int) -> tuple[float, float]:
    import numpy as np

    host = envelope(haystack, sample_rate)
    probe = envelope(needle, sample_rate)
    if len(probe) == 0 or len(host) <= len(probe):
        return 0.0, 0.0
    scores = np.correlate(host, probe, mode="valid")
    peak = int(np.argmax(scores))
    confidence = float((scores[peak] - scores.mean()) / (scores.std() + 1e-8))
    return peak * ENV_HOP_S, confidence


def refine_one(reference: Path, reference_start_s: float, clip: Path,
               clip_clock_offset_s: float, clip_duration_s: float, *,
               search_s: float = SEARCH_S,
               min_confidence: float = MIN_CONFIDENCE) -> Refinement:
    require_analysis_extras()
    probe_s = min(clip_duration_s, MAX_PROBE_S)
    if probe_s < MIN_PROBE_S:
        return Refinement(clip, clip_clock_offset_s, clip_clock_offset_s, 0.0, False,
                          "clip too short to match reliably")
    estimated_local_s = clip_clock_offset_s - reference_start_s
    window_start_s = max(0.0, estimated_local_s - search_s)
    window_length_s = probe_s + 2 * search_s
    haystack = read_window(reference, window_start_s, window_length_s, VAD_SR)
    needle = read_window(clip, 0.0, probe_s, VAD_SR)
    local_s, confidence = best_offset(haystack, needle, VAD_SR)
    if confidence < min_confidence:
        return Refinement(clip, clip_clock_offset_s, clip_clock_offset_s, confidence, False,
                          "no clear audio match, kept the camera clock")
    offset_s = reference_start_s + window_start_s + local_s
    return Refinement(clip, clip_clock_offset_s, offset_s, confidence, True)
