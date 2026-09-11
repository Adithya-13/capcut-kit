import json
from pathlib import Path

import pytest

from capcut_kit import compat, paths, safety
from capcut_kit.draft import model, validate

US = 1_000_000


def make_info(segments: list[dict], materials: dict | None = None) -> dict:
    return {
        "version": 360000,
        "name": "test",
        "duration": 0,
        "materials": materials or {"videos": [], "speeds": []},
        "tracks": [{"type": "video", "flag": 0, "segments": segments}],
    }


def segment(start_s: float, dur_s: float, material_id: str = "m1", src_s: float = 0.0) -> dict:
    return {
        "id": f"s{start_s}",
        "material_id": material_id,
        "extra_material_refs": [],
        "source_timerange": {"start": int(src_s * US), "duration": int(dur_s * US)},
        "target_timerange": {"start": int(start_s * US), "duration": int(dur_s * US)},
    }


def write_project(tmp_path: Path, info: dict, meta: dict | None = None) -> Path:
    project = tmp_path / "proj"
    project.mkdir()
    (project / paths.DRAFT_INFO).write_text(json.dumps(info))
    (project / paths.DRAFT_META).write_text(json.dumps(meta or {"draft_materials": []}))
    return project


def test_compat_flags_tested_version():
    assert compat.probe({"version": 360000}).tested


def test_compat_rejects_far_version():
    result = compat.probe({"version": 120000})
    assert not result.tested and not result.plausible
    with pytest.raises(compat.IncompatibleDraft):
        compat.require_writable(result)


def test_compat_force_allows_write():
    compat.require_writable(compat.probe({"version": 120000}), force=True)


def test_timeline_end_uses_last_segment(tmp_path):
    info = make_info([segment(0, 2), segment(2, 3)])
    draft = model.load(write_project(tmp_path, info))
    assert model.timeline_end_us(draft) == 5 * US


def test_validate_detects_overlap(tmp_path):
    info = make_info([segment(0, 5), segment(2, 3)])
    draft = model.load(write_project(tmp_path, info))
    codes = {i.code for i in validate.check(draft)}
    assert "overlap" in codes


def test_validate_detects_dangling_material(tmp_path):
    info = make_info([segment(0, 2, material_id="missing")])
    draft = model.load(write_project(tmp_path, info))
    codes = {i.code for i in validate.check(draft)}
    assert "dangling-material" in codes


def test_validate_accepts_clean_project(tmp_path, monkeypatch):
    media = tmp_path / "clip.mov"
    media.write_bytes(b"")
    materials = {
        "videos": [{"id": "m1", "path": str(media), "duration": 10 * US}],
        "speeds": [],
    }
    info = make_info([segment(0, 2), segment(2, 2)], materials)
    info["duration"] = 4 * US
    meta = {"draft_materials": [{"type": 0, "value": [{"file_Path": str(media)}]}]}
    draft = model.load(write_project(tmp_path, info, meta))
    assert validate.check(draft) == []


def test_placeholder_path_resolves_into_draft_dir(tmp_path):
    info = make_info([])
    draft = model.load(write_project(tmp_path, info))
    raw = "##_draftpath_placeholder_ABC_##/frame.jpg"
    assert model.resolve_media_path(draft, raw) == draft.dir / "frame.jpg"
    assert model.is_capcut_asset(raw)


def test_backup_and_restore_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(safety, "BACKUP_ROOT", tmp_path / "backups")
    project = write_project(tmp_path, make_info([segment(0, 2)]))
    made = safety.backup(project)
    (project / paths.DRAFT_INFO).write_text(json.dumps(make_info([])))
    assert safety.list_backups(project)[0].stamp == made.stamp
    safety.restore(project)
    restored = model.load(project)
    assert len(restored.tracks[0]["segments"]) == 1


def test_save_recomputes_duration(tmp_path):
    project = write_project(tmp_path, make_info([segment(0, 2), segment(2, 4)]))
    draft = model.load(project)
    model.save(draft)
    reloaded = model.load(project)
    assert reloaded.duration_us == 6 * US
    assert reloaded.meta["tm_duration"] == 6 * US


def test_resolve_project_matches_fragment(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    for name in ("Holiday Vlog", "Build Session"):
        project = root / name
        project.mkdir()
        (project / paths.DRAFT_INFO).write_text(json.dumps(make_info([])))
        (project / paths.DRAFT_META).write_text("{}")
    assert paths.resolve_project("holiday", root).name == "Holiday Vlog"
    with pytest.raises(LookupError):
        paths.resolve_project("nope", root)
