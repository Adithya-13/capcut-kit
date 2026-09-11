from dataclasses import dataclass
from pathlib import Path

from . import speech


@dataclass(frozen=True)
class Window:
    start_s: float
    end_s: float

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


def windows_from(placements: list[tuple[Path, float]], *, pad_s: float = 0.25,
                 merge_gap_s: float = 0.6,
                 min_window_s: float = 0.0) -> list[Window]:
    global_intervals: list[tuple[float, float]] = []
    for source, offset_s in placements:
        for start, end in speech.detect(source, pad_s=pad_s, merge_gap_s=merge_gap_s):
            global_intervals.append((offset_s + start, offset_s + end))
    merged = speech.merge(global_intervals, merge_gap_s)
    windows = [Window(start, end) for start, end in merged]
    if min_window_s > 0:
        windows = [w for w in windows if w.duration_s >= min_window_s]
    return windows
