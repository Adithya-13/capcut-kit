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


def test_generated_draft_carries_no_machine_identifiers():
    from capcut_kit.draft import template

    info = template.new_draft_info("x", 1080, 1920)
    for block in (info["platform"], info["last_modified_platform"]):
        assert block["device_id"] == ""
        assert block["hard_disk_id"] == ""
        assert block["mac_address"] == ""
        assert block["os_version"] == ""


def test_every_segment_gets_private_extra_materials():
    from capcut_kit.draft import template

    refs = []
    materials = {category: [] for category in template.MATERIAL_CATEGORIES}
    for _ in range(2):
        for category in template.EXTRA_CATEGORIES:
            extra = template.EXTRA_BUILDERS[category]()
            materials[category].append(extra)
            refs.append(extra["id"])
    assert len(refs) == len(set(refs)) == 12
    for category in template.EXTRA_CATEGORIES:
        assert len(materials[category]) == 2


def test_build_writes_an_openable_project(tmp_path, monkeypatch):
    from capcut_kit.draft import builder
    from capcut_kit.media.probe import MediaInfo

    root = tmp_path / "drafts"
    root.mkdir()
    clip_path = tmp_path / "a.mov"
    clip_path.write_bytes(b"")
    fake = MediaInfo(path=clip_path, width=1080, height=1920, duration_us=10 * US,
                     has_video=True, has_audio=True, created=None, device="Phone")
    monkeypatch.setattr(builder, "probe", lambda path: fake)

    result = builder.build("demo", [builder.Clip(path=clip_path, duration_s=4.0)], root)
    assert result.clip_count == 1
    assert result.duration_us == 4 * US

    draft = model.load(result.dir)
    assert validate.check(draft) == []
    assert draft.info["canvas_config"]["width"] == 1080
    panel = model.media_entries(draft)
    assert [entry["file_Path"] for entry in panel] == [str(clip_path)]


def test_build_refuses_to_clobber_an_existing_project(tmp_path, monkeypatch):
    from capcut_kit.draft import builder
    from capcut_kit.media.probe import MediaInfo

    root = tmp_path / "drafts"
    (root / "demo").mkdir(parents=True)
    clip_path = tmp_path / "a.mov"
    clip_path.write_bytes(b"")
    fake = MediaInfo(path=clip_path, width=1080, height=1920, duration_us=10 * US,
                     has_video=True, has_audio=True, created=None, device=None)
    monkeypatch.setattr(builder, "probe", lambda path: fake)
    with pytest.raises(builder.ProjectExists):
        builder.build("demo", [builder.Clip(path=clip_path)], root)


def test_build_skips_clips_trimmed_out_of_existence(tmp_path, monkeypatch):
    from capcut_kit.draft import builder
    from capcut_kit.media.probe import MediaInfo

    root = tmp_path / "drafts"
    root.mkdir()
    short = tmp_path / "short.mov"
    good = tmp_path / "good.mov"
    for path in (short, good):
        path.write_bytes(b"")
    sizes = {short: 1 * US, good: 10 * US}
    monkeypatch.setattr(builder, "probe", lambda path: MediaInfo(
        path=path, width=1080, height=1920, duration_us=sizes[path],
        has_video=True, has_audio=True, created=None, device=None))

    clips = [builder.Clip(path=short, source_start_s=5.0),
             builder.Clip(path=good, duration_s=3.0)]
    result = builder.build("demo", clips, root)
    assert result.clip_count == 1
    assert result.skipped == ["short.mov"]
