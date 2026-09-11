from dataclasses import dataclass
from pathlib import Path

from .audio import ANALYSIS_SR, require_analysis_extras, wav_for

ENVELOPE_HOP_S = 0.002


@dataclass(frozen=True)
class EventProfile:
    name: str
    band_low_hz: float = 3000.0
    band_high_hz: float = 14000.0
    min_prominence_db: float = 15.0
    min_isolation_db: float = 15.0
    min_decay_db: float = 11.0
    max_width_ms: float = 70.0
    min_gap_s: float = 0.12
    lead_s: float = 0.04
    clip_s: float = 0.133
    exclude_speech: bool = True
    description: str = ""


@dataclass(frozen=True)
class Event:
    source: Path
    at_s: float
    prominence_db: float
    isolation_db: float
    width_ms: float


def _envelope_db(samples, sample_rate: int, hop_s: float):
    import numpy as np

    hop = int(sample_rate * hop_s)
    frames = len(samples) // hop
    block = samples[: frames * hop].reshape(frames, hop)
    rms = np.sqrt((block ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(rms), hop / sample_rate


def _noise_floor(envelope, frame_s: float, window_s: float = 1.0):
    import numpy as np

    block = max(1, int(0.1 / frame_s))
    blocks = len(envelope) // block
    medians = np.median(envelope[: blocks * block].reshape(blocks, block), axis=1)
    half = max(1, int(window_s / 0.1))
    smoothed = np.array([
        np.median(medians[max(0, i - half): i + half + 1]) for i in range(blocks)
    ])
    floor = np.repeat(smoothed, block)
    return np.pad(floor, (0, len(envelope) - len(floor)), mode="edge")


def _isolation_db(envelope, peak: int, frame_s: float) -> float:
    before = envelope[max(0, peak - int(0.25 / frame_s)): peak - int(0.03 / frame_s)]
    after = envelope[peak + int(0.05 / frame_s): peak + int(0.30 / frame_s)]
    if len(before) == 0 or len(after) == 0:
        return 0.0
    return float(min(envelope[peak] - before.max(), envelope[peak] - after.max()))


def _width_ms(envelope, peak: int, frame_s: float, drop_db: float = 12.0) -> float:
    threshold = envelope[peak] - drop_db
    left = peak
    while left > 0 and envelope[left - 1] > threshold:
        left -= 1
    right = peak
    while right < len(envelope) - 1 and envelope[right + 1] > threshold:
        right += 1
    return (right - left + 1) * frame_s * 1000


def detect(source: Path, profile: EventProfile,
           speech: list[tuple[float, float]] | None = None) -> list[Event]:
    require_analysis_extras()
    import numpy as np
    import soundfile as sf
    from scipy.signal import butter, sosfiltfilt

    samples, sample_rate = sf.read(str(wav_for(source, ANALYSIS_SR)), dtype="float32")
    sos = butter(4, (profile.band_low_hz, profile.band_high_hz),
                 btype="bandpass", fs=sample_rate, output="sos")
    band = sosfiltfilt(sos, samples)
    envelope, frame_s = _envelope_db(band, sample_rate, ENVELOPE_HOP_S)
    prominence = envelope - _noise_floor(envelope, frame_s)

    gap_frames = max(1, int(profile.min_gap_s / frame_s))
    decay_frames = max(1, int(0.040 / frame_s))
    spoken = speech or []

    events: list[Event] = []
    index = 1
    while index < len(envelope) - decay_frames:
        if prominence[index] < profile.min_prominence_db or envelope[index] < envelope[index - 1]:
            index += 1
            continue
        peak = index + int(np.argmax(envelope[index: index + gap_frames]))
        at_s = peak * frame_s
        isolation = _isolation_db(envelope, peak, frame_s)
        decay = float(envelope[peak] - envelope[min(peak + decay_frames, len(envelope) - 1)])
        width = _width_ms(envelope, peak, frame_s)
        in_speech = any(start <= at_s <= end for start, end in spoken)
        if (isolation >= profile.min_isolation_db
                and decay >= profile.min_decay_db
                and width <= profile.max_width_ms
                and not (profile.exclude_speech and in_speech)):
            events.append(Event(source, round(at_s, 3), round(float(prominence[peak]), 1),
                                round(isolation, 1), round(width, 1)))
        index = peak + gap_frames
    return events


def stride_sample(items: list, wanted: int) -> list:
    if wanted <= 0 or len(items) <= wanted:
        return items
    step = len(items) / wanted
    return [items[int(i * step)] for i in range(wanted)]
