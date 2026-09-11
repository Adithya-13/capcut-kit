---
name: capcut-events
description: Find a specific kind of sound in footage and cut every occurrence into a CapCut montage - LEGO brick clicks, keyboard presses, impacts, or any transient you can describe with a recipe. Use when the user wants a satisfying-sounds compilation, an ASMR click montage, every hit or press collected into one clip, or wants to tune why detection is finding too many or too few sounds. Triggers - "find the clicks", "make a click montage", "cut every keyboard press", "asmr compilation", "too many bad clicks", "it is missing sounds", "tune the detection".
---

# Detecting sounds and cutting montages

Finds short, sharp sounds in footage and optionally cuts each one into a project. Detection is
driven by recipes, which are plain TOML files. Adding a new kind of sound means writing a
recipe, never code.

Needs the audio extras: `capcut setup --analysis`.

## Look before you build

```
capcut recipes                                      what is available
capcut events <file or folder> --recipe lego        count them
capcut events <file> --recipe lego --list           show each one
```

Always run `events` before `montage` when the user is unsure. It is read-only, it creates no
project, and the count tells you immediately whether the recipe fits the footage. A count of
zero or a count in the thousands both mean the recipe is wrong for this material.

## Building the montage

```
capcut montage <file or folder> --recipe lego
capcut montage <folder> --recipe lego --target-length 90
capcut montage <folder> --recipe keyboard --name "typing sounds"
```

`--target-length` samples evenly across the whole recording rather than taking the loudest or
the first ones. That matters: an entire montage drawn from the first two minutes of a three
hour build looks wrong even when every clip is a real detection.

Clips land in the order the sounds happened, so a build progresses forward.

## Tuning, in the order to try things

The user's complaint tells you which way to move.

- **"too many, and some are junk"**: raise `min_prominence_db` and `min_isolation_db` first.
  Isolation is the one that rejects rustle and handling noise, so reach for it before loudness.
- **"it is catching my voice or the room"**: narrow `max_width_ms` and raise `min_decay_db`. Real
  clicks are narrow and die fast. Speech and knocks are wider.
- **"it is missing obvious ones"**: lower `min_prominence_db` and `min_isolation_db`, in small
  steps of two or three decibels.
- **"the clips feel late or clipped"**: adjust `lead_s`, which is how far before the peak the
  clip starts, and `clip_s`, which is how long it runs.

The best tuning method is not guessing. Ask the user for two or three timestamps of bad
detections and two or three of good ones, run `events --list`, read the loudness, isolation, and
width of each, and set the thresholds between the two groups. One round of that beats ten
rounds of nudging.

## Writing a recipe

Copy an existing one into `~/.capcut-kit/recipes/<name>.toml` and edit it. The band matters most:
bright, small sounds live high, and heavy sounds live low. Set `exclude_speech = true` for
anything recorded near a talking person.

A recipe the user tunes successfully is worth offering to save under a name, so they never
redo the work.

## Rules

1. Run `events` before `montage` whenever the recipe or footage is new. Building blind wastes
   the user's time and fills their project list.
2. Report the count honestly, including when it is zero. Do not loosen a recipe silently to
   produce a result.
3. Detection finds sounds, not good moments. It cannot tell a satisfying click from an
   accidental one. Say so rather than implying it curates.
4. Long footage takes a while on the first pass because the audio is extracted and cached.
   Warn the user before starting on hours of material.
