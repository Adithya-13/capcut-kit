# capcut-kit

[![tests](https://github.com/Adithya-13/capcut-kit/actions/workflows/tests.yml/badge.svg)](https://github.com/Adithya-13/capcut-kit/actions/workflows/tests.yml)

Point it at a folder of raw footage. Get back a CapCut project that is already worth opening.

## The problem it solves

You filmed one thing from two angles. A camera on the work, a camera on your face. Now you
have forty files and an empty timeline, and before any real editing starts you have to:

1. Work out which clip from camera B happened during which clip from camera A.
2. Drag them into place so the same moment lines up vertically.
3. Scrub through the dead air, the setup, the silence, and cut it all out.

That is an hour of mechanical work before you make a single creative decision. This does it
for you.

```bash
capcut build ~/Footage/saturday --layout sync --cut-silence
```

**Every camera lands on its own track, at the real moment it was recorded**, read from the
timestamp your camera wrote into the file. The same instant lines up vertically, so picking an
angle is a click instead of a hunt.

**Then the silence goes.** It listens for speech across every camera, keeps the parts where
someone is talking, and closes the gaps. All tracks shift together, so cutting never breaks
the alignment it just built.

What you open in CapCut is a draft with the structure already right. You do the editing.

## Why not just do it by hand

- **CapCut cannot line up two cameras by recording time.** There is no command for it. By hand
  it is a lot of dragging and squinting at timecode.
- **It is repeatable.** Same footage in, same timeline out, every episode of a series.
- **Nothing is re-encoded.** The project points at your original files where they already sit.
- **You keep editing in CapCut.** This is not a replacement editor. It does the boring part and
  hands you a normal project, with your usual effects, text, and templates.
- **It reads projects too.** When CapCut says offline media and nothing else, `doctor` names the
  file and the reason.

**Status: early but real.** Building, aligning, silence cutting, inspecting, diagnosing, and
backups all work today. Audio-event detection, subtitles, and beat syncing are next.

---

## Read this before installing

**It cannot export your video.** Nothing here starts a render. Every workflow ends the same
way: you open CapCut and press export yourself. If you wanted unattended rendering, stop here.

**macOS only.** It quits and reopens CapCut using macOS commands, and looks for your projects
in `~/Movies/CapCut`. There is no Windows support and none planned.

**One CapCut version is verified.** CapCut 179.x, draft format version 360000. Projects are
written in that format, and `doctor` warns when it meets a project saved by a different one.
Nothing here rewrites an existing project's timeline yet, so a format mismatch cannot damage
your work today. When in-place editing lands, it will refuse unfamiliar formats.

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
/plugin marketplace add Adithya-13/capcut-kit
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
git clone https://github.com/Adithya-13/capcut-kit
cd capcut-kit
./bin/capcut projects
```

First run takes a few seconds while it builds its environment. After that it is instant.

---

## Commands

```bash
capcut projects                    # list your CapCut projects, newest first
capcut build <folder>              # turn a folder of footage into a project
capcut setup --analysis            # install what silence cutting needs
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
capcut build ~/Footage/shoot                                  everything end to end
capcut build ~/Footage/shoot --layout sync                    cameras stacked and aligned
capcut build ~/Footage/shoot --layout sync --refine-sync      alignment corrected by audio
capcut build ~/Footage/shoot --layout sync --cut-silence      aligned, dead air removed
capcut build ~/Footage/shoot --name "Saturday cut"
capcut build ~/Footage/shoot --trim-start 2 --max-clip 10
```

**`--layout sequence`** is the default. Every clip goes on one track, one after another, in
recording order.

**`--layout sync`** is the interesting one. Each camera gets its own track, and every clip sits
at the moment it was actually recorded. A clip filmed twenty minutes in starts twenty minutes
in. Two cameras rolling at once end up stacked, so the same moment is one vertical line. This
needs a recording time in every file, which phones and real cameras write automatically. If any
file is missing one, it says so and tells you to use `sequence` instead.

**`--refine-sync`** stops trusting the cameras' clocks. It matches the audio each camera heard
against the main camera's audio and corrects the placement, which is what saves you when two
devices disagree by a few seconds. Each clip reports how far it moved and how confident the
match was. A clip with no clear match keeps its clock position and says so, rather than being
moved on a guess. Needs the audio extras.

**`--cut-silence`** listens for speech across every camera, keeps the stretches where someone
is talking, and closes the gaps. Every track shifts by the same amount, so the alignment
survives. Tune it with `--pad` for how much air to leave around each phrase, `--merge-gap` for
how long a pause has to be before it becomes a cut, and `--min-window` to drop anything shorter
than you care about.

Silence cutting needs the audio extras, installed once with `capcut setup --analysis`. They are
a few hundred megabytes, because speech detection pulls in PyTorch. Everything else works
without them. `capcut setup --clear-cache` throws away the audio it extracted along the way.

`--layout sync` refuses `--trim-start`, `--trim-end`, `--max-clip`, and `--order`, because those
contradict placing clips at their real recording time. If two clips from one camera overlap,
usually a duplicate or a re-exported copy, that camera gets a second track and the command says
so rather than writing a broken timeline.

`--trim-start` and `--trim-end` cut the same number of seconds off every clip, for shaving the
reach-for-the-record-button moments. `--max-clip` caps each clip's length.

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
| `untested-format` | your CapCut version is not the verified one | reading is fine; treat anything this tool generates for that version as unproven |

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
- [x] Stack every camera at the moment it was recorded
- [x] Cut the stretches where nobody is talking
- [x] Refine camera alignment by cross-correlating audio, for clocks that drift
- [ ] Detect audio events, with recipes for LEGO clicks, keyboards, cooking, impacts
- [ ] Import subtitles into a real text track
- [ ] Cut a montage to music beats

## Contributing

Recipes for audio-event detection are plain config files, not code. If you tune one for a
kind of content, send it in.

## License

MIT. Not affiliated with CapCut or ByteDance.
