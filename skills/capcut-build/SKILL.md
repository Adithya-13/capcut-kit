---
name: capcut-build
description: Turn a folder of raw footage into a new CapCut project on macOS - stack every camera on its own track at the real moment it was recorded so the same instant lines up vertically, cut out the stretches where nobody is talking, or lay everything end to end. Use when the user has multi-angle or multi-camera footage and wants the angles synced, wants dead air and silence removed before editing, or wants any CapCut project built from files on disk. Triggers - "make a capcut project from this folder", "sync my two cameras", "line up my angles", "cut the silence", "remove the dead air", "turn my footage into an edit", "build a rough cut".
---

# Building CapCut projects from footage

Creates a new project. It never modifies an existing one, and it never copies, moves, or
re-encodes the footage. The project points at the files where they already are.

Run through the plugin's wrapper: `${CLAUDE_PLUGIN_ROOT}/bin/capcut`.

## The command

```
capcut build <folder>                                   everything end to end, one track
capcut build <folder> --layout sync                     cameras stacked, aligned by real time
capcut build <folder> --layout sync --cut-silence       aligned, then dead air removed
capcut build <folder> --name "Saturday cut"
capcut build <folder> --pad 0.4 --merge-gap 0.8 --min-window 1.0
capcut build <folder> --order name
capcut build <folder> --trim-start 2 --trim-end 1 --max-clip 10
capcut build <folder> --fps 60 --overwrite
```

## Picking the layout

This is the decision that matters. Ask if it is not obvious.

**`--layout sync`** is what someone means by "line up my cameras" or "I filmed this from two
angles". Each recording device gets its own track, and every clip sits at the moment it was
actually recorded, taken from the timestamp in the file. Clips filmed at the same time end up
stacked vertically, so choosing an angle is a click. Use it whenever the folder holds more than
one camera, or one camera whose clips should keep their real spacing.

It needs a recording time in every file. If any file lacks one the command refuses and names
the files. Do not work around that by falling back silently, tell the user which files are the
problem, since it usually means those were exported or re-encoded somewhere.

**`--layout sequence`** is the default and puts everything on one track back to back. Right for
single-camera footage where the gaps between takes do not matter.

## Cutting the silence

`--cut-silence` finds speech across every camera, keeps those stretches, and closes the gaps.
All tracks move by the same amount, so a synced timeline stays synced.

- `--pad` seconds of air kept either side of each phrase. Raise it if cuts feel clipped.
- `--merge-gap` how long a pause must be before it becomes a cut. Raise it for fewer, longer
  takes, lower it for a tighter edit.
- `--min-window` drops kept stretches shorter than this. Good for killing one-word blips.

It needs the audio extras. If they are missing the command says so, and the fix is
`capcut setup --analysis`. Run that rather than telling the user to install anything by hand.

Be honest about what it detects: speech, not interest. It keeps talking and drops quiet. It has
no idea whether what was said was any good.

## The other options

- **Order.** Only affects `sequence` layout. Recording time by default, falling back to filename
  order for the whole set when any file lacks a timestamp.
- **Trim.** `--trim-start` and `--trim-end` take the same seconds off every clip, for footage
  where each take starts with reaching for the record button. Not smart, so keep them small.
  They apply to `sequence` layout only.
- **Max clip.** Caps every clip, for a skimmable assembly of long takes.

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
5. This builds a draft, not a finished edit. With `--cut-silence` it removes quiet, but it
   never chooses an angle, never reorders for story, and never judges what was worth saying.
   Say that plainly so nobody expects a finished rough cut.
6. A synced timeline can be long and sparse, because it spans real elapsed time including the
   hours nothing was filmed. That is correct, not a bug. If the user finds it unwieldy, the
   answer is `--cut-silence`, which collapses it to what was actually said.
