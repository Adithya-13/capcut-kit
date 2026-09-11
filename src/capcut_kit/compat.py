from dataclasses import dataclass

TESTED_APP_VERSIONS = ("179",)
TESTED_DRAFT_VERSIONS = (360000,)
KNOWN_DRAFT_RANGE = (340000, 380000)


@dataclass(frozen=True)
class Compat:
    draft_version: int | None
    app_version: str | None
    tested: bool
    plausible: bool
    message: str


def probe(info: dict) -> Compat:
    version = info.get("version")
    app = info.get("new_version") or info.get("app_version")
    draft_version = version if isinstance(version, int) else None
    if draft_version in TESTED_DRAFT_VERSIONS:
        return Compat(draft_version, app, True, True, "draft format matches a tested version")
    if draft_version is None:
        return Compat(None, app, False, False,
                      "draft_info.json has no version field; this may not be a CapCut draft")
    low, high = KNOWN_DRAFT_RANGE
    if low <= draft_version <= high:
        return Compat(draft_version, app, False, True,
                      f"draft version {draft_version} is untested but close to the tested "
                      f"{TESTED_DRAFT_VERSIONS[0]}; reads are fine, writes may be risky")
    return Compat(draft_version, app, False, False,
                  f"draft version {draft_version} is far from the tested "
                  f"{TESTED_DRAFT_VERSIONS[0]}; writing could corrupt this project")


class IncompatibleDraft(RuntimeError):
    pass


def require_writable(compat: Compat, force: bool = False) -> None:
    if compat.tested or force:
        return
    raise IncompatibleDraft(
        f"{compat.message}. Re-run with --force to write anyway "
        f"(a timestamped backup is always taken first)."
    )
