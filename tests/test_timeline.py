from pathlib import Path

import pytest

from capcut_kit import timeline
from capcut_kit.analysis.activity import Window
from capcut_kit.analysis.speech import merge
from capcut_kit.draft.builder import Clip

CAM_A = Path("/tmp/a.mov")
CAM_B = Path("/tmp/b.mov")


def clip(path: Path, target: float, duration: float, track: int = 0,
         source: float = 0.0) -> Clip:
    return Clip(path=path, source_start_s=source, duration_s=duration,
                target_start_s=target, track=track)


def test_merge_joins_close_intervals():
    assert merge([(0, 1), (1.2, 2), (5, 6)], 0.5) == [(0, 2), (5, 6)]


def test_merge_leaves_distant_intervals_alone():
    assert merge([(0, 1), (5, 6)], 0.5) == [(0, 1), (5, 6)]


def test_restrict_keeps_only_the_windows():
    clips = [clip(CAM_A, 0.0, 100.0)]
    kept = timeline.restrict(clips, [Window(10, 20), Window(50, 55)])
    assert [(c.target_start_s, c.duration_s, c.source_start_s) for c in kept] == [
        (0.0, 10.0, 10.0),
        (10.0, 5.0, 50.0),
    ]


def test_restrict_closes_the_gaps():
    clips = [clip(CAM_A, 0.0, 100.0)]
    kept = timeline.restrict(clips, [Window(10, 20), Window(50, 55)])
    assert timeline.total_span_s(kept) == 15.0


def test_restrict_keeps_cameras_aligned():
    clips = [clip(CAM_A, 0.0, 100.0, track=0), clip(CAM_B, 40.0, 20.0, track=1)]
    kept = timeline.restrict(clips, [Window(10, 20), Window(45, 55)])
    on_a = [c for c in kept if c.path == CAM_A]
    on_b = [c for c in kept if c.path == CAM_B]
    assert len(on_b) == 1
    overlapping_a = next(c for c in on_a if c.source_start_s == 45.0)
    assert overlapping_a.target_start_s == on_b[0].target_start_s
    assert on_b[0].source_start_s == 5.0


def test_restrict_drops_slivers_below_the_floor():
    clips = [clip(CAM_A, 0.0, 100.0)]
    kept = timeline.restrict(clips, [Window(10, 10.05)], min_kept_s=0.1)
    assert kept == []


def test_restrict_without_windows_returns_nothing():
    assert timeline.restrict([clip(CAM_A, 0.0, 10.0)], []) == []


def test_placements_use_the_earliest_appearance_of_each_file():
    clips = [clip(CAM_A, 30.0, 5.0, source=10.0), clip(CAM_A, 5.0, 5.0, source=1.0)]
    assert dict(timeline.placements(clips)) == {CAM_A: 4.0}


def test_restrict_is_stable_when_a_window_precedes_every_clip():
    clips = [clip(CAM_A, 20.0, 10.0)]
    kept = timeline.restrict(clips, [Window(0, 5), Window(22, 25)])
    assert len(kept) == 1
    assert kept[0].target_start_s == 5.0
