# capcut-kit

Ask Claude about your CapCut projects, and let it edit them.

CapCut desktop has no API and no plugin system. But every project it saves is plain JSON on
disk. This toolkit reads that JSON, checks it for damage, and writes new timelines back into
it safely. You drive it by talking to Claude Code, or by running the CLI yourself.

**Status: early.** Reading, diagnosing, and backing up projects work today. Generating drafts
from raw footage and cutting by silence, audio events, or beats are next.

---

## Read this before installing

**It cannot export your video.** Nothing here starts a render. Every workflow ends the same
way: you open CapCut and press export yourself. If you wanted unattended rendering, stop here.

**macOS only.** It quits and reopens CapCut using macOS commands, and looks for your projects
in `~/Movies/CapCut`. There is no Windows support and none planned.

**One CapCut version is verified.** CapCut 179.x, draft format version 360000. Other versions
can still be read. Writing to them is refused unless you pass `--force`, because a format
change could corrupt a project.

---

## Which Claude app do I use?

**Claude Code.** Any of its forms works: the terminal CLI, the Code tab in the Claude desktop
app, or the VS Code and JetBrains extensions. All three run commands directly on your Mac,
which is what this needs.

**Claude Cowork will not work.** Cowork runs on Anthropic's servers in an isolated
environment, and reaches your Mac only to read and write files in folders you connect. It
cannot run a local command line tool, cannot quit and reopen CapCut, and cannot call `ffmpeg`
on your machine. Those three things are the entire job here. Use Claude Code.

---

## Requirements

| Thing | Why | Install |
|---|---|---|
| macOS | CapCut desktop and its control commands | already there |
| CapCut desktop | the projects themselves | capcut.com |
| Python 3.10+ | runs the toolkit | handled for you, see below |
| ffmpeg | reading video length, size, and audio | `brew install ffmpeg` |

You do not need to set up Python yourself. On first run the toolkit builds its own isolated
environment in `~/.capcut-kit`. If your Mac has no Python 3.10 or newer, it offers to install
[uv](https://github.com/astral-sh/uv) inside that same folder and nowhere else. It asks first.
Deleting `~/.capcut-kit` removes everything it ever created.

---

## Install

### As a Claude Code plugin (recommended)

```
/plugin marketplace add adithya-13/capcut-kit
/plugin install capcut-kit@capcut-kit
```

Then just talk to Claude:

> what's in my CapCut project 0908?

> why does my project show offline media?

> back up my LEGO project before I change anything

> is my edit cut too fast?

Claude picks the right command, runs it, and explains the output. It will take a backup before
anything that writes, and tell you the snapshot name so you can roll back.

### As a plain command line tool

```bash
git clone https://github.com/adithya-13/capcut-kit
cd capcut-kit
./bin/capcut projects
```

First run takes a few seconds while it builds its environment. After that it is instant.

---

## Commands

```bash
capcut projects                    # list your CapCut projects, newest first
capcut build <folder>              # turn a folder of footage into a project
capcut inspect <project>           # tracks, roles, gaps, pacing
capcut inspect <project> --media   # which files are used, and for how long
capcut inspect <project> --timeline  # every clip on the track, in order
capcut inspect <project> --json    # machine readable
capcut doctor <project>            # find broken media links and damaged references
capcut backup <project>            # snapshot before you change anything
capcut backups <project>           # list snapshots, newest first
capcut restore <project> [stamp]   # roll back, defaults to the newest snapshot
```

Project names match on fragments. `capcut inspect 0908` and `capcut inspect "auto Minecraft"`
both work. If a fragment matches more than one project, it lists them and stops.

### Building a project from footage

```bash
capcut build ~/Footage/saturday-shoot
capcut build ~/Footage/shoot --name "Saturday cut" --order time
capcut build ~/Footage/shoot --per-camera --trim-start 2 --max-clip 10
```

Clips go on the timeline in recording order, read from each file's creation time, falling back
to filename order when that is missing. `--per-camera` puts each recording device on its own
track, which is what you want for a two-camera shoot. `--trim-start` and `--trim-end` cut the
same number of seconds off every clip, for shaving the reach-for-the-record-button moments.
`--max-clip` caps each clip's length.

The canvas size is taken from whatever size most of your footage is, so vertical footage gives
you a vertical project. Nothing is copied or re-encoded. The project points at your files
where they already live, so leave them there.

If CapCut is open when you build, restart it for the new project to appear.

### What inspect tells you

```
0908  49.73s  draft version 360000

#  type   role     clips  content  gaps
-  -----  -------  -----  -------  ------
0  video  main     39     49.73s   0.00s
1  text   main     1      6.33s    0.00s
2  text   overlay  45     44.30s   4.97s

track 0 pacing: 39 clips, median 1.13s, range 0.20s to 4.40s, 47.1 cuts/min
```

Track 0 is the main track. `overlay` tracks sit above it. `gaps` is empty space inside a
track, which is normal on overlay and audio tracks and usually a mistake on the main one.

### What doctor tells you

Errors mean something is actually broken. Warnings are cosmetic.

| Code | Meaning | Fix |
|---|---|---|
| `offline-media` | a file moved or was deleted | if it moved, use CapCut's own Link Media dialog and pick the folder once |
| `dangling-material` | a clip points at something that no longer exists | restore from a backup |
| `overlap` | two clips occupy the same moment on one track | restore from a backup |
| `source-out-of-range` | a clip reads past the end of its own source file | restore from a backup |
| `duration-drift` | stored length disagrees with the timeline | harmless, fixed on the next write |
| `untested-format` | your CapCut version is not the verified one | reading is fine, writing needs `--force` |

CapCut's own cache files and its internal `##_draftpath_placeholder_` paths are resolved
automatically, so they are never reported as missing.

---

## How it keeps your projects safe

1. **CapCut is closed before any write.** It holds the open project in memory and overwrites
   outside changes when it saves. Write commands quit it, make the change, and reopen it. If
   CapCut refuses to quit, usually because an export is running, the command stops instead of
   forcing it.
2. **Every write takes a timestamped snapshot first.** Snapshots live in
   `~/.capcut-kit/backups/`, outside your project folder, so CapCut never sees stray files.
3. **Reading is always safe**, even with CapCut open. `projects`, `inspect`, and `doctor`
   never write anything.
4. **Files are written atomically**, so an interrupted write cannot leave half a project.

What snapshots do **not** cover: your actual video files. They capture the timeline and the
media panel only. Moving your footage still breaks the links, and CapCut will ask you to
relink the folder once.

Restoring overwrites anything you did in CapCut since that snapshot. Claude will warn you
before doing it.

---

## Roadmap

- [x] Read projects, report pacing and media usage
- [x] Diagnose damage and broken links
- [x] Snapshot and roll back
- [x] Build a project from a folder of footage
- [ ] Cut by silence, for talking-head and podcast footage
- [ ] Sync two or more cameras by their audio
- [ ] Detect audio events, with recipes for LEGO clicks, keyboards, cooking, impacts
- [ ] Import subtitles into a real text track
- [ ] Cut a montage to music beats

## Contributing

Recipes for audio-event detection are plain config files, not code. If you tune one for a
kind of content, send it in.

## License

MIT. Not affiliated with CapCut or ByteDance.
