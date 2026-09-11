from pathlib import Path

import pytest

from capcut_kit import recipes
from capcut_kit.analysis.events import EventProfile, stride_sample
from capcut_kit.draft import builder, model
from capcut_kit.draft import validate as checks
from capcut_kit.media.probe import MediaInfo

US = 1_000_000


def test_builtin_recipes_load():
    names = set(recipes.available())
    assert {"lego", "keyboard", "impact"} <= names
    for name in names:
        assert isinstance(recipes.load(name), EventProfile)


def test_lego_recipe_listens_in_the_click_band():
    profile = recipes.load("lego")
    assert profile.band_low_hz >= 2000
    assert profile.max_width_ms <= 100
    assert profile.exclude_speech


def test_unknown_recipe_names_the_alternatives():
    with pytest.raises(LookupError) as exc:
        recipes.load("does-not-exist")
    assert "lego" in str(exc.value)


def test_a_recipe_file_can_be_loaded_by_path(tmp_path):
    path = tmp_path / "custom.toml"
    path.write_text('name = "custom"\nmin_prominence_db = 22.0\nclip_s = 0.5\n')
    profile = recipes.load(str(path))
    assert profile.name == "custom"
    assert profile.min_prominence_db == 22.0


def test_stride_sample_spreads_across_the_whole_run():
    items = list(range(100))
    picked = stride_sample(items, 5)
    assert len(picked) == 5
    assert picked[0] == 0
    assert picked[-1] >= 75


def test_stride_sample_keeps_everything_when_it_fits():
    assert stride_sample([1, 2, 3], 10) == [1, 2, 3]


def test_back_to_back_clips_never_overlap(tmp_path, monkeypatch):
    source = tmp_path / "take.mov"
    source.write_bytes(b"")
    monkeypatch.setattr(builder, "probe", lambda path: MediaInfo(
        path=path, width=1080, height=1920, duration_us=600 * US, has_video=True,
        has_audio=True, created=None, device=None))

    clip_s = 0.133
    clips = []
    cursor = 0.0
    for index in range(400):
        clips.append(builder.Clip(path=source, source_start_s=index * 1.1,
                                  duration_s=clip_s, target_start_s=cursor))
        cursor += clip_s

    result = builder.build("montage", clips, tmp_path / "drafts")
    draft = model.load(result.dir)
    assert [i for i in checks.check(draft) if i.code == "overlap"] == []
