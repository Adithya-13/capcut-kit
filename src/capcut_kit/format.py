US = 1_000_000


def timecode(us: int) -> str:
    total = us / US
    minutes, seconds = divmod(total, 60)
    hours, minutes = divmod(int(minutes), 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:06.3f}"
    return f"{minutes:d}:{seconds:06.3f}"


def duration(us: int) -> str:
    seconds = us / US
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes, rest = divmod(seconds, 60)
    return f"{int(minutes)}m{rest:04.1f}s"


def table(rows: list[list[str]], headers: list[str]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    out = [line, "  ".join("-" * w for w in widths)]
    for row in rows:
        out.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(out)
