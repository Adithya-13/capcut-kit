# capcut-kit

Read, edit, and generate CapCut desktop projects from the command line, and from Claude Code.

CapCut has no API and no plugin system, but every project on disk is plain JSON. This toolkit
reads that JSON, checks it for damage, and writes new timelines into it safely.

## What it will not do

**It cannot export.** Nothing here can start a render. Every workflow ends with you opening
CapCut and pressing export yourself. If you need unattended rendering, this is the wrong tool.

macOS only. Verified against CapCut 179.x, draft format version 360000. Other versions are
readable, but writes are refused unless you pass `--force`.

## Install

As a Claude Code plugin:

```
/plugin marketplace add adithya/capcut-kit
/plugin install capcut-kit@capcut-kit
```

Standalone, from a clone:

```
./bin/capcut projects
```

The first run builds an isolated environment under `~/.capcut-kit`. It needs Python 3.10 or
newer, plus `ffmpeg` for anything that touches media. If neither Python 3.10+ nor `uv` is on
your Mac, it offers to install `uv` inside `~/.capcut-kit` and nowhere else.

## Commands

```
capcut projects                  list your CapCut projects
capcut inspect <project>         tracks, pacing, media usage
capcut inspect <project> --timeline --media
capcut doctor <project>          find broken references and offline media
capcut backup <project>          snapshot draft_info.json and draft_meta_info.json
capcut backups <project>         list snapshots
capcut restore <project> [stamp] roll back to a snapshot
```

Project names can be partial. `capcut inspect 0908` and `capcut inspect "auto Minecraft"`
both work.

## Safety

1. **CapCut must be closed before any write.** It holds the open project in memory and will
   overwrite external changes when it saves. Write commands quit it, edit, then reopen it.
2. **Every write takes a timestamped backup first**, stored in `~/.capcut-kit/backups/`,
   outside your project folder. `capcut restore` rolls back.
3. **Reads are always safe**, including while CapCut is running.
4. Backups capture the timeline, not your media. Moving media files still breaks links, and
   CapCut will ask you to relink the folder once.

## License

MIT
