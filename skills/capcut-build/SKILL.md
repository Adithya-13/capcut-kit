---
name: capcut-build
description: Turn a folder of raw footage into a new CapCut project on macOS - lay clips on a timeline in recording order, put each camera on its own track, trim heads and tails, cap clip length. Use when the user has footage on disk and wants a CapCut project made from it, wants a rough assembly to start editing from, or wants two cameras lined up on separate tracks. Triggers - "make a capcut project from this folder", "turn my footage into an edit", "build a rough cut", "put my clips on a timeline", "line up my two cameras".
---

# Building CapCut projects from footage

Creates a new project. It never modifies an existing one, and it never copies, moves, or
re-encodes the footage. The project points at the files where they already are.

Run through the plugin's wrapper: `${CLAUDE_PLUGIN_ROOT}/bin/capcut`.

## The command

```
capcut build <folder>                            project named after the folder
capcut build <folder> --name "Saturday cut"
capcut build <folder> --per-camera               one track per recording device
capcut build <folder> --order name               filename order instead of recording time
capcut build <folder> --trim-start 2 --trim-end 1
capcut build <folder> --max-clip 10
capcut build <folder> --fps 60
capcut build <folder> --overwrite                replace a project of the same name
```

## Choosing the options

Ask about these rather than guessing, unless the user already said.

- **Order.** Recording time is the default and is what people mean by "in order". It reads each
  file's creation time. If any file lacks one, it falls back to filename order for the whole
  set, so the result stays consistent rather than half-sorted.
- **Per camera.** For a two-camera shoot, `--per-camera` groups by the recording device stored
  in the footage and gives each its own track. Without it everything lands on one track in one
  long line. Cameras are detected from file metadata, so this only works when the cameras
  actually recorded a device name.
- **Trim.** `--trim-start` and `--trim-end` take the same number of seconds off every clip.
  Useful for footage where every take begins with reaching for the record button. They are not
  smart, so keep them small.
- **Max clip.** Caps every clip. Good for a quick skimmable assembly of long takes.

Canvas size comes from whichever dimensions most of the footage uses. Vertical footage gives a
vertical project. Pass nothing for this unless the user asks for a specific size.

## After building

The command prints the clip count, total length, and track count. Two things to tell the user:

1. If CapCut was open, it must be restarted before the new project appears in the list.
2. Run `capcut doctor "<name>"` and report the result. A freshly built project should come back
   clean. Anything else is a bug worth showing them.

## Rules

1. **Never build into a name that already exists** without asking. `--overwrite` destroys the
   existing project, and it is not covered by a backup because the project was never read.
2. **Never move the user's footage** to tidy it up first. Moving files breaks the links and
   forces a relink in CapCut.
3. If a folder mixes unrelated content, say so and ask before building one project out of all
   of it. The command has no idea what belongs together.
4. Clips too short to survive trimming are skipped and named in the output. Pass that on rather
   than silently reporting a smaller clip count.
5. This builds an assembly, not an edit. It makes no cuts inside a clip and removes no silence.
   Say that plainly so nobody expects a finished rough cut.
