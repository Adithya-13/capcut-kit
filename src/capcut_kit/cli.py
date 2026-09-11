import argparse
import json
import sys
from pathlib import Path

from . import (
    __version__, assemble, format as fmt, inspect as inspect_mod, paths, safety,
    setup_extras, timeline,
)
from .draft import builder, model
from .draft import validate as checks


def _load(name: str):
    return model.load(paths.resolve_project(name))


def cmd_projects(args: argparse.Namespace) -> int:
    found = paths.list_projects()
    if not found:
        print(f"no CapCut projects found in {paths.draft_root()}")
        return 1
    rows = []
    for project in found[: args.limit]:
        draft = model.load(project)
        rows.append([
            project.name,
            fmt.duration(model.timeline_end_us(draft)),
            str(len(draft.tracks)),
            "yes" if draft.compat.tested else "untested",
        ])
    print(fmt.table(rows, ["project", "length", "tracks", "format"]))
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    draft = _load(args.project)
    if args.json:
        print(json.dumps(inspect_mod.overview(draft), indent=2))
        return 0
    info = inspect_mod.overview(draft)
    print(f"{info['name']}  {fmt.duration(info['duration_us'])}  "
          f"draft version {info['draft_version']}")
    print(f"{info['dir']}\n")
    rows = [
        [str(t.index), t.kind, t.role, str(t.segment_count),
         fmt.duration(t.covered_us), fmt.duration(t.gap_us)]
        for t in inspect_mod.track_summaries(draft)
    ]
    print(fmt.table(rows, ["#", "type", "role", "clips", "content", "gaps"]))
    pace = inspect_mod.pacing(draft, args.track)
    if pace:
        print(f"\ntrack {args.track} pacing: {pace.clip_count} clips, "
              f"median {fmt.duration(pace.median_us)}, "
              f"range {fmt.duration(pace.shortest_us)} to {fmt.duration(pace.longest_us)}, "
              f"{pace.cuts_per_minute:.1f} cuts/min")
    if args.media:
        print()
        rows = [
            [Path(path).name, str(count), fmt.duration(used), "ok" if exists else "OFFLINE"]
            for path, count, used, exists in inspect_mod.media_usage(draft)
        ]
        print(fmt.table(rows, ["file", "clips", "used", "status"]))
    if args.timeline:
        print()
        rows = [
            [str(i), fmt.timecode(seg["target_timerange"]["start"]),
             fmt.duration(seg["target_timerange"]["duration"]),
             fmt.timecode(seg["source_timerange"]["start"]), label]
            for i, seg, label in inspect_mod.timeline_rows(draft, args.track)
        ]
        print(fmt.table(rows, ["#", "at", "length", "source in", "file"]))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    draft = _load(args.project)
    issues = checks.check(draft)
    if not issues:
        print(f"{draft.name}: no problems found")
        return 0
    rows = [
        [i.level, i.code, i.message if i.track is None else f"track {i.track}: {i.message}"]
        for i in issues
    ]
    print(fmt.table(rows, ["level", "code", "detail"]))
    return 1 if checks.errors(issues) else 0


def cmd_backup(args: argparse.Namespace) -> int:
    project = paths.resolve_project(args.project)
    made = safety.backup(project)
    print(f"backed up {project.name} to {made.path}")
    if args.keep:
        dropped = safety.prune_backups(project, args.keep)
        if dropped:
            print(f"pruned {len(dropped)} older backups")
    return 0


def cmd_backups(args: argparse.Namespace) -> int:
    project = paths.resolve_project(args.project)
    found = safety.list_backups(project)
    if not found:
        print(f"no backups for {project.name}")
        return 1
    print(fmt.table([[b.stamp, str(b.path)] for b in found], ["stamp", "path"]))
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    project = paths.resolve_project(args.project)
    if safety.capcut_running() and not args.force:
        print("CapCut is running. Quit it first, or pass --force to quit it automatically.")
        return 2
    with safety.capcut_closed(reopen=not args.no_reopen):
        used = safety.restore(project, args.stamp)
    print(f"restored {project.name} from backup {used.stamp}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    folder = Path(args.folder).expanduser()
    if not folder.is_dir():
        print(f"error: not a folder: {folder}", file=sys.stderr)
        return 2
    sources = assemble.order(assemble.gather(folder), args.order)
    name = args.name or folder.name
    if args.layout == assemble.LAYOUT_SYNC:
        clips = assemble.align(sources)
        groups = assemble.group_by_device(sources)
        order = assemble.device_track_order(groups)
        print(f"aligned {len(order)} camera(s) on a shared timeline: "
              f"{', '.join(f'{d} ({len(groups[d])} clips)' for d in order)}")
        span, gap = assemble.coverage(clips)
        print(f"  spans {fmt.duration(int(span * 1_000_000))}, "
              f"{fmt.duration(int(gap * 1_000_000))} of it with nothing on the main track")
    else:
        clips = assemble.to_clips(
            sources, trim_start_s=args.trim_start, trim_end_s=args.trim_end,
            max_clip_s=args.max_clip)
    if args.cut_silence:
        from .analysis import activity

        print("listening for speech (first run downloads a small model)...")
        windows = activity.windows_from(
            timeline.placements(clips), pad_s=args.pad,
            merge_gap_s=args.merge_gap, min_window_s=args.min_window)
        before = timeline.total_span_s(clips)
        clips = timeline.restrict(clips, windows)
        after = timeline.total_span_s(clips)
        saved = before - after
        print(f"kept {len(windows)} talking windows: "
              f"{fmt.duration(int(after * 1_000_000))} of "
              f"{fmt.duration(int(before * 1_000_000))}, "
              f"cut {fmt.duration(int(saved * 1_000_000))} of dead air")
        if not clips:
            print("error: no speech found, so nothing would be left", file=sys.stderr)
            return 2

    result = builder.build(name, clips, paths.draft_root(), fps=args.fps,
                           overwrite=args.overwrite)
    print(f"built '{result.name}': {result.clip_count} clips, "
          f"{fmt.duration(result.duration_us)}, {result.tracks} track(s)")
    print(f"  {result.dir}")
    if result.skipped:
        print(f"  skipped {len(result.skipped)} unusable files: "
              f"{', '.join(result.skipped[:5])}")
    if safety.capcut_running():
        print("  CapCut is running. Restart it for the new project to appear.")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    if not args.analysis:
        ready = setup_extras.analysis_ready()
        print(f"audio analysis extras: {'installed' if ready else 'not installed'}")
        if not ready:
            print("install them with: capcut setup --analysis")
        return 0
    if setup_extras.analysis_ready() and not args.force:
        print("audio analysis extras are already installed")
        return 0
    return setup_extras.install(setup_extras.ANALYSIS_EXTRA)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="capcut", description="CapCut project toolkit")
    parser.add_argument("--version", action="version", version=f"capcut-kit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("projects", help="list CapCut projects")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(func=cmd_projects)

    p = sub.add_parser("inspect", help="show a project's structure")
    p.add_argument("project")
    p.add_argument("--track", type=int, default=0)
    p.add_argument("--timeline", action="store_true", help="list every clip on the track")
    p.add_argument("--media", action="store_true", help="list media usage")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("setup", help="check or install optional extras")
    p.add_argument("--analysis", action="store_true",
                   help="install what silence cutting needs")
    p.add_argument("--force", action="store_true", help="reinstall even if present")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("build", help="create a project from a folder of footage")
    p.add_argument("folder")
    p.add_argument("--name", default=None, help="project name, defaults to the folder name")
    p.add_argument("--order", choices=[assemble.ORDER_TIME, assemble.ORDER_NAME],
                   default=assemble.ORDER_TIME, help="clip order on the timeline")
    p.add_argument("--layout", choices=[assemble.LAYOUT_SEQUENCE, assemble.LAYOUT_SYNC],
                   default=assemble.LAYOUT_SEQUENCE,
                   help="sequence: every clip end to end. "
                        "sync: each camera on its own track, every clip at the real moment "
                        "it was recorded, so the same moment lines up vertically")
    p.add_argument("--trim-start", type=float, default=0.0, help="seconds to cut off each head")
    p.add_argument("--trim-end", type=float, default=0.0, help="seconds to cut off each tail")
    p.add_argument("--max-clip", type=float, default=None, help="cap each clip at N seconds")
    p.add_argument("--cut-silence", action="store_true",
                   help="drop stretches where nobody is talking, closing the gaps and "
                        "keeping every camera in sync")
    p.add_argument("--pad", type=float, default=0.25,
                   help="seconds of air kept around each talking stretch")
    p.add_argument("--merge-gap", type=float, default=0.6,
                   help="pauses shorter than this stay in, rather than becoming a cut")
    p.add_argument("--min-window", type=float, default=0.0,
                   help="drop kept stretches shorter than this")
    p.add_argument("--fps", type=float, default=30.0)
    p.add_argument("--overwrite", action="store_true", help="replace an existing project")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("doctor", help="check a project for problems")
    p.add_argument("project")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("backup", help="snapshot a project's draft files")
    p.add_argument("project")
    p.add_argument("--keep", type=int, default=0, help="prune to this many backups")
    p.set_defaults(func=cmd_backup)

    p = sub.add_parser("backups", help="list snapshots for a project")
    p.add_argument("project")
    p.set_defaults(func=cmd_backups)

    p = sub.add_parser("restore", help="restore a project from a snapshot")
    p.add_argument("project")
    p.add_argument("stamp", nargs="?", default=None, help="defaults to the newest")
    p.add_argument("--force", action="store_true", help="quit CapCut if it is running")
    p.add_argument("--no-reopen", action="store_true")
    p.set_defaults(func=cmd_restore)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (LookupError, FileNotFoundError, FileExistsError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
