from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from capcut_kit import assemble, timeline
from capcut_kit.media.probe import MediaInfo

BASE = datetime(2026, 9, 11, 9, 0, tzinfo=timezone.utc)


def source(name: str, offset_s: float, duration_s: float, device: str = "Cam A",
           dated: bool = True) -> assemble.Source:
    path = Path(f"/tmp/{name}.mov")
    info = MediaInfo(path=path, width=1080, height=1920,
                     duration_us=int(duration_s * 1_000_000), has_video=True,
                     has_audio=True,
                     created=BASE + timedelta(seconds=offset_s) if dated else None,
                     device=device)
    return assemble.Source(path=path, info=info)


def test_align_places_each_clip_at_its_recording_moment():
    clips, notes = assemble.align([source("a", 0, 10), source("b", 60, 5)])
    assert notes == []
    assert sorted(c.target_start_s for c in clips) == [0.0, 60.0]


def test_align_puts_each_camera_on_its_own_track():
    clips, _ = assemble.align([
        source("a", 0, 100, device="Cam A"),
        source("b", 30, 10, device="Cam B"),
    ])
    by_path = {c.path.name: c for c in clips}
    assert by_path["a.mov"].track != by_path["b.mov"].track


def test_the_camera_with_most_footage_takes_the_main_track():
    clips, _ = assemble.align([
        source("short", 0, 5, device="Cam B"),
        source("long", 0, 500, device="Cam A"),
    ])
    main = next(c for c in clips if c.track == 0)
    assert main.path.name == "long.mov"


def test_overlapping_clips_from_one_camera_get_separate_tracks():
    clips, notes = assemble.align([
        source("original", 0, 30),
        source("duplicate", 0, 30),
        source("later", 100, 10),
    ])
    assert len(notes) == 1
    assert "overlap" in notes[0]
    tracks = {c.path.name: c.track for c in clips}
    assert tracks["original.mov"] != tracks["duplicate.mov"]
    assert tracks["later.mov"] == tracks["original.mov"]


def test_align_refuses_footage_without_recording_times():
    with pytest.raises(assemble.NoTimestamps):
        assemble.align([source("a", 0, 10), source("b", 5, 10, dated=False)])


def test_sequence_clips_carry_explicit_positions():
    clips = assemble.to_clips([source("a", 0, 10), source("b", 60, 5)])
    assert [c.target_start_s for c in clips] == [0.0, 10.0]


def test_sequence_positions_survive_silence_cutting():
    from capcut_kit.analysis.activity import Window

    clips = assemble.to_clips([source("a", 0, 10), source("b", 60, 10)])
    kept = timeline.restrict(clips, [Window(2, 4), Window(12, 16)])
    spans = sorted((c.target_start_s, c.target_start_s + c.duration_s) for c in kept)
    for (_, earlier_end), (later_start, _) in zip(spans, spans[1:]):
        assert later_start >= earlier_end


def test_trimming_shifts_source_and_shortens_the_clip():
    clips = assemble.to_clips([source("a", 0, 10)], trim_start_s=2.0, trim_end_s=1.0)
    assert clips[0].source_start_s == 2.0
    assert clips[0].duration_s == 7.0


def test_clips_trimmed_to_nothing_are_dropped():
    assert assemble.to_clips([source("a", 0, 3)], trim_start_s=2.0, trim_end_s=2.0) == []
