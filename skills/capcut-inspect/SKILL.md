---
name: capcut-inspect
description: Inspect, diagnose, and back up CapCut desktop projects on macOS - list projects, read a timeline clip by clip, report pacing, find broken media links and damaged references, snapshot and roll back. Use when the user wants to know what is inside a CapCut project, why a project looks wrong or shows offline media, how long or how fast-cut an edit is, or wants a safety snapshot before editing. Triggers - "what's in my capcut project", "check my capcut project", "why is my media offline", "how many cuts", "back up my project", "undo what you did to my project".
---

# Inspecting CapCut projects

Read-only commands are safe at any time, including while CapCut is open. Only `restore`
writes, and it quits CapCut first.

Run everything through the plugin's wrapper: `${CLAUDE_PLUGIN_ROOT}/bin/capcut`. The first
run builds its own environment and prints what it is doing.

## Finding the project

```
capcut projects
```

Names are matched loosely, so a fragment is enough. If a fragment matches several projects the
command lists them and stops. Ask the user which one rather than guessing.

## Reading a project

```
capcut inspect "<project>"                      tracks, roles, gaps, pacing
capcut inspect "<project>" --media              which files are used and for how long
capcut inspect "<project>" --timeline           every clip on the track, in order
capcut inspect "<project>" --track 2 --timeline a specific track
capcut inspect "<project>" --json               machine-readable overview
```

Track 0 is the main track. Tracks with role `overlay` sit above it. The `gaps` column is
empty timeline space inside a track, which is normal on overlay and audio tracks and usually
a mistake on the main one.

Pacing reports median clip length and cuts per minute. Use it when someone asks whether an
edit is too fast, too slow, or uneven, rather than guessing from the clip count.

## Diagnosing

```
capcut doctor "<project>"
```

Errors mean the project is damaged or unopenable in some way. Warnings are cosmetic.

- `offline-media` the file moved or was deleted. If it was moved, the fix is CapCut's own
  Link Media dialog, where the user picks the folder once. Tell them that rather than
  editing paths by hand.
- `dangling-material` or `dangling-extra-ref` a segment points at something that no longer
  exists. Usually the result of a failed external edit. Restore from a backup.
- `overlap` or `empty-segment` two clips occupy the same time, or a clip has no length.
- `source-out-of-range` a clip reads past the end of its own source file.
- `duration-drift` the stored length disagrees with the timeline. Harmless, fixed on the next
  write.
- `untested-format` this CapCut version is newer or older than the tested one. Reads are
  still fine. Writes will refuse without `--force`.

Files under CapCut's own cache and its internal `##_draftpath_placeholder_` paths are
resolved automatically and are not reported as missing.

## Backups

```
capcut backup "<project>"              snapshot now
capcut backups "<project>"             list snapshots, newest first
capcut restore "<project>"             roll back to the newest
capcut restore "<project>" 20260911-141500 --force
```

Snapshots live in `~/.capcut-kit/backups/`, never inside the project folder. They cover
`draft_info.json` and `draft_meta_info.json`, which is the timeline and the media panel. They
do not cover media files.

`restore` needs CapCut closed. `--force` quits it automatically and reopens it afterwards.

## Rules

1. Never suggest editing `draft_info.json` by hand. Use the commands.
2. Before any command that writes, take a backup and say the stamp out loud so the user can
   roll back.
3. A restore overwrites whatever the user did in CapCut since that snapshot. Warn them and
   get a yes before running it.
4. If `doctor` reports errors on a project the user cares about, report the findings and stop.
   Do not repair by writing unless they ask.
