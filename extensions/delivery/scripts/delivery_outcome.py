#!/usr/bin/env python3
"""Validate and record one verified pull-request outcome.

This module owns the Delivery Close-specific evidence transition.  It is kept
separate from ``delivery_runtime.py`` so the runtime can import it without
turning the other coordinator operations into durable writers.  The public
``close_record`` function accepts the small duck-typed surface of Runtime that
it needs: ``root``, ``run``, ``directory``, ``inside``, ``relative``, ``git``
and, when available, ``load``.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any
from urllib.parse import urlparse


SCHEMA_VERSION = 1
CURRENT_BEGIN = "<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->"
CURRENT_END = "<!-- DELIVERY_CURRENT_OUTCOME_END -->"
HISTORY_HEADING = "## Historical validation snapshots"
HISTORY_NOTICE = "<!-- Existing validation, review, CI, and limitation content below is retained verbatim as historical evidence. -->"
SHA = re.compile(r"^[0-9a-fA-F]{40,64}$")
HASH = re.compile(r"^[0-9a-fA-F]{64}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
FIELD = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*)?([A-Za-z][A-Za-z0-9_]*)"
    r"(?:\*\*)?\s*:\s*(.*?)\s*$"
)
CURRENT_BLOCK = re.compile(
    re.escape(CURRENT_BEGIN) + r"\r?\n.*?\r?\n" + re.escape(CURRENT_END),
    re.DOTALL,
)
OBSERVED_KEYS = {
    "schema_version",
    "delivery_run",
    "lane",
    "provider",
    "repository",
    "number",
    "state",
    "head_revision",
    "base_revision",
    "merged_revision",
    "merged_at",
    "observed_at",
    "url",
}
LANES = {"feature", "bugfix", "lightweight"}
OUTCOMES = {"merged", "closed"}
NON_CONCRETE_PR = {
    "",
    "pending",
    "none",
    "not-created",
    "not-published",
    "not-yet-published",
}


class OutcomeError(ValueError):
    """A fail-closed Delivery Close validation error."""


# A parent Runtime may choose to catch this name while importing the module.
ProtocolError = OutcomeError


def _fail(message: str) -> None:
    raise OutcomeError(message)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"Observed tracker field {field!r} must be a non-empty string.")
    return value.strip()


def _sha(value: Any, field: str) -> str:
    value = _text(value, field)
    if not SHA.fullmatch(value):
        _fail(f"Observed tracker field {field!r} is not a full Git object id.")
    return value.lower()


def _nullable_sha(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _sha(value, field)


def _timestamp(value: Any, field: str) -> str:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError:
        _fail(f"Observed tracker field {field!r} must be an RFC3339 timestamp.")
    if parsed.tzinfo is None:
        _fail(f"Observed tracker field {field!r} must include a timezone.")
    return text


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _runtime_root(runtime: Any) -> Path:
    root = getattr(runtime, "root", None)
    if root is None:
        _fail("Close runtime does not expose its project root.")
    try:
        return Path(root).resolve()
    except (TypeError, OSError) as exc:
        _fail(f"Close runtime project root is invalid: {exc}")
    raise AssertionError("unreachable")


def _runtime_run(runtime: Any) -> str:
    run = getattr(runtime, "run", None)
    if not isinstance(run, str) or not RUN_ID.fullmatch(run) or ".." in run:
        _fail("Close runtime does not expose a safe delivery_run id.")
    return run


def _runtime_directory(runtime: Any, root: Path, run: str) -> Path:
    directory = getattr(runtime, "directory", None)
    expected = root / ".specify" / "delivery" / run
    if directory is not None:
        try:
            actual = Path(directory).resolve()
        except (TypeError, OSError) as exc:
            _fail(f"Close runtime run directory is invalid: {exc}")
        if actual != expected.resolve():
            _fail("Close runtime run directory does not match the canonical delivery_run path.")
        if Path(directory).is_symlink():
            _fail("Close runtime run directory must not be a symlink.")
    if expected.is_symlink():
        _fail("Close runtime run directory must not be a symlink.")
    return expected.resolve()


def _check_containment(path: Path, root: Path, *, allow_missing_leaf: bool = False) -> Path:
    try:
        resolved = path.resolve()
    except OSError as exc:
        _fail(f"Cannot resolve Close path {path}: {exc}")
    if not resolved.is_relative_to(root):
        _fail(f"Close path escapes its canonical root: {path}")
    current = path
    while current != root and current.is_relative_to(root):
        if current.is_symlink():
            _fail(f"Refusing a symlink in a Close-owned path: {path}")
        current = current.parent
    if not allow_missing_leaf and not path.is_file():
        _fail(f"Required Close file is missing: {path}")
    return resolved


def _run_file(runtime: Any, value: Any, expected: Path, root: Path, directory: Path) -> Path:
    if not isinstance(value, (str, Path)):
        _fail("The observed tracker file path is required.")
    raw = str(value).replace("\\", "/")
    canonical_run = f".specify/delivery/{_runtime_run(runtime)}/runtime/observed-pr.json"
    if raw not in {"runtime/observed-pr.json", canonical_run}:
        _fail("The observed tracker file must be exactly runtime/observed-pr.json for this run.")
    candidate = directory / "runtime" / "observed-pr.json"
    if candidate.resolve() != expected.resolve():
        _fail("The observed tracker file does not resolve to the canonical run runtime path.")
    if hasattr(runtime, "inside"):
        try:
            checked = Path(runtime.inside(candidate))
        except Exception as exc:  # Runtime implementations expose their own ProtocolError.
            _fail(f"The observed tracker file is outside the project: {exc}")
        if checked.resolve() != expected.resolve():
            _fail("The observed tracker file is not the canonical run runtime path.")
    _check_containment(candidate, directory, allow_missing_leaf=False)
    if candidate.is_symlink() or not candidate.is_file():
        _fail("The observed tracker file must be a regular, non-symlink JSON file.")
    return candidate


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"Cannot read {label}: {exc}")
    if not isinstance(value, dict):
        _fail(f"{label} must contain one JSON object.")
    return value


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(f"Cannot read {label}: {exc}")
    raise AssertionError("unreachable")


def _fields(text: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for line in text.splitlines():
        match = FIELD.match(line)
        if match:
            values.setdefault(match[1].lower(), []).append(match[2].strip().strip("`"))
    return values


def _first(values: dict[str, list[str]], key: str) -> str | None:
    entries = values.get(key.lower(), [])
    return entries[0] if entries else None


def _current_block(text: str) -> tuple[str | None, dict[str, list[str]], str]:
    matches = list(CURRENT_BLOCK.finditer(text))
    if len(matches) > 1:
        _fail("Evidence contains more than one DELIVERY_CURRENT_OUTCOME block.")
    if not matches:
        return None, {}, text
    match = matches[0]
    block = match.group(0)
    return block, _fields(block), text[: match.start()] + text[match.end() :]


def _state(runtime: Any, run: str) -> tuple[dict[str, Any], str]:
    state: dict[str, Any] = {}
    loader = getattr(runtime, "load", None)
    if callable(loader):
        try:
            loaded = loader()
        except Exception as exc:
            _fail(f"Cannot read the delivery runtime checkpoint: {exc}")
        if not isinstance(loaded, dict):
            _fail("Delivery runtime checkpoint must be a JSON object.")
        state = loaded
    state_run = state.get("delivery_run", run)
    if state_run != run:
        _fail("Runtime checkpoint delivery_run does not match the Close request.")
    lane = state.get("lane", getattr(runtime, "lane", None))
    if lane not in LANES:
        _fail("Runtime checkpoint does not provide a valid delivery lane.")
    return state, lane


def _canonical_repository(value: Any) -> str:
    value = _text(value, "repository")
    if not REPOSITORY.fullmatch(value):
        _fail("Observed tracker repository must be owner/name without a URL or extra path.")
    return value.lower()


def _canonical_pr(value: Any, repository: str | None = None) -> tuple[str, int]:
    value = _text(value, "pull request")
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme.lower() != "https" or parsed.netloc.lower() != "github.com" or parsed.query or parsed.fragment:
            _fail("Pull request URL must be a canonical HTTPS GitHub PR URL.")
        path = [part for part in parsed.path.rstrip("/").split("/") if part]
        if len(path) != 4 or path[2].lower() != "pull" or not path[3].isdigit():
            _fail("Pull request URL must use https://github.com/owner/name/pull/<number>.")
        repo = f"{path[0]}/{path[1]}".lower()
        number = int(path[3])
    else:
        qualified = re.fullmatch(r"([^#\s]+)#([0-9]+)", value)
        match = re.fullmatch(r"(?:#)?([0-9]+)", value)
        if qualified:
            repo = qualified[1].lower()
            number = int(qualified[2])
        elif match:
            if repository is None:
                _fail("A numeric pull request needs the observed repository identity.")
            repo = repository.lower()
            number = int(match[1])
        else:
            _fail("Pull request must be a number, owner/name#number, or canonical GitHub PR URL.")
    if not REPOSITORY.fullmatch(repo):
        _fail("Pull request repository must be owner/name.")
    if number < 1:
        _fail("Pull request number must be positive.")
    if repository is not None and repo != repository.lower():
        _fail("Pull request repository does not match the observed tracker repository.")
    return repo, number


def _validate_observation(value: dict[str, Any], run: str, lane: str, pr: str) -> dict[str, Any]:
    if set(value) != OBSERVED_KEYS:
        missing = sorted(OBSERVED_KEYS - set(value))
        extra = sorted(set(value) - OBSERVED_KEYS)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        _fail("Observed tracker JSON has the wrong exact schema (" + "; ".join(details) + ").")
    if type(value["schema_version"]) is not int or value["schema_version"] != SCHEMA_VERSION:
        _fail("Observed tracker schema_version must be exactly 1.")
    if value["delivery_run"] != run or value["lane"] != lane:
        _fail("Observed tracker delivery_run/lane does not match the active run.")
    if value["provider"] != "github":
        _fail("Only provider=github is supported by the Delivery Close contract.")
    repository = _canonical_repository(value["repository"])
    if type(value["number"]) is not int or value["number"] < 1:
        _fail("Observed tracker number must be a positive integer.")
    state = value["state"]
    if state not in {"MERGED", "CLOSED"}:
        _fail("Observed tracker state must be MERGED or CLOSED.")
    head = _sha(value["head_revision"], "head_revision")
    base = _sha(value["base_revision"], "base_revision")
    merged = _nullable_sha(value["merged_revision"], "merged_revision")
    merged_at = value["merged_at"]
    if state == "MERGED":
        if merged is None:
            _fail("A MERGED tracker observation requires merged_revision and merged_at.")
        merged_at = _timestamp(merged_at, "merged_at")
    else:
        if merged is not None or merged_at is not None:
            _fail("A CLOSED tracker observation must have null merged_revision and merged_at.")
    observed_at = _timestamp(value["observed_at"], "observed_at")
    url_repo, url_number = _canonical_pr(value["url"], repository)
    if (url_repo, url_number) != (repository, value["number"]):
        _fail("Observed tracker URL does not match repository/number.")
    pr_repo, pr_number = _canonical_pr(pr, repository)
    if (pr_repo, pr_number) != (repository, value["number"]):
        _fail("The requested PR does not match the observed tracker identity.")
    return {
        "schema_version": SCHEMA_VERSION,
        "delivery_run": run,
        "lane": lane,
        "provider": "github",
        "repository": repository,
        "number": value["number"],
        "state": state,
        "head_revision": head,
        "base_revision": base,
        "merged_revision": merged,
        "merged_at": merged_at.strip() if isinstance(merged_at, str) else None,
        "observed_at": observed_at,
        "url": f"https://github.com/{repository}/pull/{value['number']}",
    }


def _git(runtime: Any, *arguments: str) -> tuple[bool, bytes]:
    method = getattr(runtime, "git", None)
    if not callable(method):
        _fail("Close runtime does not expose a read-only Git helper.")
    try:
        output = method(*arguments)
    except Exception:
        return False, b""
    if not isinstance(output, (bytes, bytearray)):
        output = str(output).encode("utf-8")
    return True, bytes(output)


def _commit_object(runtime: Any, revision: str) -> bool:
    ok, output = _git(runtime, "cat-file", "-t", f"{revision}^{{commit}}")
    return ok and output.decode("utf-8", errors="replace").strip() == "commit"


def _reachable_commit(runtime: Any, revision: str) -> bool:
    if not _commit_object(runtime, revision):
        return False
    ok, output = _git(runtime, "rev-list", "--all", "--contains", revision)
    if ok and output.decode("utf-8", errors="replace").strip():
        return True
    ok, _ = _git(runtime, "merge-base", "--is-ancestor", revision, "HEAD")
    return ok


def _diff(runtime: Any, base: str, revision: str) -> bytes | None:
    if not _commit_object(runtime, base) or not _commit_object(runtime, revision):
        return None
    ok, output = _git(
        runtime,
        "diff",
        "--no-ext-diff",
        "--no-renames",
        "--binary",
        "--full-index",
        base,
        revision,
        "--",
    )
    return output if ok else None


def _path_from_run(runtime: Any, value: str, directory: Path) -> Path | None:
    raw = value.replace("\\", "/")
    run = _runtime_run(runtime)
    prefixes = (f".specify/delivery/{run}/", "")
    candidate: Path | None = None
    for prefix in prefixes:
        if raw.startswith(prefix):
            suffix = raw[len(prefix) :]
            if suffix:
                candidate = directory / suffix
            break
    if candidate is None:
        return None
    try:
        resolved = candidate.resolve()
    except OSError:
        return None
    if not resolved.is_relative_to(directory.resolve()) or candidate.is_symlink() or not candidate.is_file():
        return None
    return candidate


def _archive_content(
    runtime: Any,
    values: dict[str, list[str]],
    directory: Path,
    base: str,
    head: str,
) -> bytes | None:
    archive_value = _first(values, "reviewed_diff_archive") or _first(values, "evidence_archive")
    archive_hash = _first(values, "reviewed_diff_archive_sha256") or _first(values, "evidence_archive_sha256")
    archive_base = _first(values, "reviewed_diff_archive_base") or _first(values, "evidence_archive_base")
    archive_head = _first(values, "reviewed_diff_archive_head") or _first(values, "evidence_archive_head")
    archive_reviewed = _first(values, "reviewed_diff_archive_reviewed_head")
    archive_names = {
        "reviewed_diff_archive", "evidence_archive",
        "reviewed_diff_archive_sha256", "evidence_archive_sha256",
        "reviewed_diff_archive_base", "evidence_archive_base",
        "reviewed_diff_archive_head", "evidence_archive_head",
        "reviewed_diff_archive_reviewed_head",
    }
    if any(key in values for key in archive_names) and (
        not archive_value or not archive_hash or not archive_base or not archive_head
    ):
        _fail("Evidence archive binding is partial; preserve all archive path, digest, base, and head fields.")
    if not archive_value:
        return None
    if archive_reviewed is not None and not SHA.fullmatch(archive_reviewed):
        _fail("Evidence archive reviewed_head binding is malformed.")
    if not HASH.fullmatch(archive_hash):
        _fail("Evidence archive digest is malformed.")
    if _sha(archive_base, "archive base") != base or _sha(archive_head, "archive head") != head:
        _fail("Evidence archive base/head binding does not match the tracker observation.")
    path = _path_from_run(runtime, archive_value, directory)
    if path is None:
        _fail("Evidence archive path is missing, outside the run, or not a regular file.")
    try:
        content = path.read_bytes()
    except OSError as exc:
        _fail(f"Cannot read the Evidence archive: {exc}")
    if _digest(content) != archive_hash.lower():
        _fail("Evidence archive bytes do not match its recorded digest.")
    return content


def _archive_proof(
    runtime: Any,
    values: dict[str, list[str]],
    directory: Path,
    base: str,
    head: str,
    merged: str,
) -> bool:
    content = _archive_content(runtime, values, directory, base, head)
    if content is None:
        return False
    merged_diff = _diff(runtime, base, merged)
    return merged_diff is not None and content == merged_diff


def _state_review_head(runtime: Any, state: dict[str, Any], directory: Path) -> str | None:
    candidates: list[Any] = [state.get("reviewed_head")]
    stages = state.get("stages")
    if isinstance(stages, dict) and isinstance(stages.get("review"), dict):
        review = stages["review"]
        candidates.extend([review.get("reviewed_head"), review.get("head")])
        receipt = review.get("native_receipt")
        if isinstance(receipt, dict) and isinstance(receipt.get("path"), str):
            path = _path_from_run(runtime, receipt["path"], directory)
            if path is not None:
                try:
                    receipt_data = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError):
                    receipt_data = None
                if isinstance(receipt_data, dict):
                    candidates.append(receipt_data.get("head"))
    for candidate in candidates:
        if isinstance(candidate, str) and SHA.fullmatch(candidate):
            return candidate.lower()
    return None


def _current_identity(current: dict[str, list[str]], key: str) -> str | None:
    value = _first(current, key)
    return value.strip() if isinstance(value, str) else None


def _reviewed_head(
    runtime: Any,
    state: dict[str, Any],
    current: dict[str, list[str]],
    historical: dict[str, list[str]],
    directory: Path,
) -> str:
    value = _current_identity(current, "reviewed_head") or _first(historical, "reviewed_head") or _state_review_head(runtime, state, directory)
    if value is None:
        _fail("Evidence has no explicit reviewed_head or immutable native Review head; rerun Evidence/Review before Close.")
    return _sha(value, "reviewed_head")


def _concrete_existing_pr(current: dict[str, list[str]], historical: dict[str, list[str]], repository: str) -> tuple[str, int] | None:
    value = _current_identity(current, "pull_request") or _first(historical, "pull_request")
    if value is None or value.lower() in NON_CONCRETE_PR:
        return None
    return _canonical_pr(value, repository)


def _relation_proof(
    runtime: Any,
    current: dict[str, list[str]],
    historical: dict[str, list[str]],
    directory: Path,
    reviewed: str,
    head: str,
    base: str,
) -> str:
    values = dict(historical)
    for key, entries in current.items():
        values.setdefault(key, []).extend(entries)
    if reviewed == head:
        # The verified tracker head is the authoritative mapping even when a
        # clean clone has already discarded the historical PR object.
        return "tracker-head-mapped"
    published = _first(values, "published_head")
    if published is None or _sha(published, "published_head") != head:
        _fail("Tracker publication head differs from reviewed_head without an explicit published_head binding.")
    reviewed_diff = _diff(runtime, base, reviewed)
    published_diff = _diff(runtime, base, head)
    if reviewed_diff is not None and published_diff is not None and reviewed_diff == published_diff:
        return "published-content-equivalent"
    # An exact archive may prove the published head even when the old review
    # object is gone; it must be tied to the reviewed and published identities.
    archive_reviewed = _first(values, "reviewed_diff_archive_reviewed_head")
    if archive_reviewed is None:
        archive = None
    else:
        if _sha(archive_reviewed, "archive reviewed head") != reviewed:
            _fail("The evidence archive is bound to another reviewed_head.")
        archive = _archive_content(runtime, values, directory, base, head)
    if archive is not None:
        if published_diff is None or archive == published_diff:
            return "published-evidence-archive"
    _fail("Publication head differs from reviewed_head, but no content-equivalence or bookkeeping-only proof is available.")
    raise AssertionError("unreachable")


def _merge_proof(
    runtime: Any,
    values: dict[str, list[str]],
    directory: Path,
    outcome: str,
    state: str,
    head: str,
    base: str,
    merged: str | None,
    reviewed: str,
) -> str:
    if outcome == "closed":
        return "not-applicable"
    if state != "MERGED" or merged is None:
        _fail("A merged Close requires a MERGED tracker observation and merged_revision.")
    if not _reachable_commit(runtime, merged):
        _fail("Tracker merged_revision is not a locally reachable commit; do not fetch or rewrite history for Close.")
    if _first(values, "reviewed_diff_archive") or _first(values, "evidence_archive"):
        if not _archive_proof(runtime, values, directory, base, head, merged):
            _fail("The declared Evidence archive is not content-equivalent to the verified merged revision.")
        return "evidence-archive"
    head_diff = _diff(runtime, base, head)
    merged_diff = _diff(runtime, base, merged)
    if head_diff is not None and merged_diff is not None:
        if head_diff != merged_diff:
            _fail("The locally reachable merged_revision is not content-equivalent to the verified PR head.")
        return "diff-equivalent"
    if _archive_proof(runtime, values, directory, base, head, merged):
        return "evidence-archive"
    if reviewed == head:
        # No old PR object is required in a clean clone. The verified tracker
        # observation binds the historical head; the effective head remains the
        # separately checked, locally reachable merge revision. This is never a
        # new Review of the merge commit.
        return "tracker-head-mapped"
    _fail("The old PR head is unavailable and no exact evidence archive proves the merged content.")
    raise AssertionError("unreachable")


def _canonical_current_block(
    observation: dict[str, Any],
    outcome: str,
    reviewed: str,
    publication_proof: str,
    merge_proof: str,
) -> str:
    status = "delivered" if outcome == "merged" else "abandoned"
    merged = observation["merged_revision"]
    merged_at = observation["merged_at"]
    return "\n".join(
        [
            CURRENT_BEGIN,
            "## Current delivery outcome",
            "",
            f"- **delivery_run**: {observation['delivery_run']}",
            f"- **lane**: {observation['lane']}",
            f"- **status**: {status}",
            f"- **outcome**: {outcome}",
            f"- **provider**: {observation['provider']}",
            f"- **repository**: {observation['repository']}",
            f"- **number**: {observation['number']}",
            f"- **pull_request**: {observation['url']}",
            f"- **reviewed_head**: {reviewed}",
            f"- **original_pr_head**: {observation['head_revision']}",
            f"- **published_head_proof**: {publication_proof}",
            f"- **base_revision**: {observation['base_revision']}",
            f"- **merged_revision**: {merged if merged is not None else 'null'}",
            f"- **effective_head**: {merged if merged is not None else 'null'}",
            f"- **merged_at**: {merged_at if merged_at is not None else 'null'}",
            f"- **observed_at**: {observation['observed_at']}",
            f"- **outcome_recorded_at**: {observation['observed_at']}",
            f"- **verification_file**: .specify/delivery/{observation['delivery_run']}/runtime/observed-pr.json",
            f"- **merge_proof**: {merge_proof}",
            CURRENT_END,
        ]
    )


def _existing_conflicts(current: dict[str, list[str]], observation: dict[str, Any], outcome: str) -> None:
    old_outcome = _current_identity(current, "outcome")
    if old_outcome is None:
        old_status = _current_identity(current, "status")
        old_outcome = {"delivered": "merged", "abandoned": "closed"}.get((old_status or "").lower())
    if old_outcome and old_outcome != outcome:
        _fail("Evidence already has a different current terminal outcome; use the authorized override path.")
    old_pr = _current_identity(current, "pull_request")
    if old_pr and old_pr.lower() not in NON_CONCRETE_PR:
        old_identity = _canonical_pr(old_pr, observation["repository"])
        new_identity = (observation["repository"], observation["number"])
        if old_identity != new_identity:
            _fail("Current Evidence PR identity conflicts with the verified tracker observation.")
    for key in ("original_pr_head", "base_revision", "merged_revision"):
        old = _current_identity(current, key)
        if old and old.lower() != "null":
            expected = {
                "original_pr_head": observation["head_revision"],
                "base_revision": observation["base_revision"],
                "merged_revision": observation["merged_revision"],
            }[key]
            if expected is None or _sha(old, key) != expected:
                _fail(f"Current Evidence {key} conflicts with the verified tracker observation.")


def _ensure_history_marked(text: str, block: str) -> str:
    if HISTORY_HEADING in text:
        return text
    return block + "\n\n" + HISTORY_HEADING + "\n\n" + HISTORY_NOTICE + "\n\n" + text


def _replace_current(text: str, block: str) -> tuple[str, bool]:
    matches = list(CURRENT_BLOCK.finditer(text))
    if len(matches) > 1:
        _fail("Evidence contains more than one DELIVERY_CURRENT_OUTCOME block.")
    if not matches:
        return _ensure_history_marked(text, block), True
    match = matches[0]
    old = match.group(0)
    if old == block:
        return text, False
    return text[: match.start()] + block + text[match.end() :], True


def _atomic_write(path: Path, text: str) -> None:
    if path.is_symlink() or not path.is_file():
        _fail("Canonical evidence must be an existing regular, non-symlink file.")
    try:
        mode = path.stat().st_mode
        descriptor, temporary_name = tempfile.mkstemp(prefix=".evidence-close-", dir=str(path.parent))
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, mode & 0o7777)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    except OSError as exc:
        _fail(f"Atomic Evidence current-block write failed; original Evidence was retained: {exc}")


def close_record(runtime: Any, outcome: str, verified: bool, pr: str | None, file: str | None) -> dict[str, Any]:
    """Validate one verified PR observation and atomically record Close state.

    The function performs all validation before touching ``evidence.md`` and
    never calls ``runtime.save``.  Runtime checkpoints therefore remain
    unchanged on success and failure; the only durable mutation is the
    Close-owned current block in the canonical Evidence file.
    """

    if outcome not in OUTCOMES:
        _fail("close-record supports only outcome=merged or outcome=closed.")
    if type(verified) is not bool or not verified:
        _fail("Close outcome is unverified; pass a tracker observation with verified=true.")
    if not isinstance(pr, str) or not pr.strip():
        _fail("A concrete pull-request number or URL is required for close-record.")
    if file is None:
        file = "runtime/observed-pr.json"

    root = _runtime_root(runtime)
    run = _runtime_run(runtime)
    directory = _runtime_directory(runtime, root, run)
    state, lane = _state(runtime, run)
    evidence_path = directory / "evidence.md"
    _check_containment(evidence_path, directory, allow_missing_leaf=False)
    if evidence_path.is_symlink() or not evidence_path.is_file():
        _fail("Canonical Evidence must be an existing regular, non-symlink file.")
    observed_path = directory / "runtime" / "observed-pr.json"
    _run_file(runtime, file, observed_path, root, directory)
    observed = _read_json(observed_path, "runtime/observed-pr.json")
    observation = _validate_observation(observed, run, lane, pr)
    expected_state = {"merged": "MERGED", "closed": "CLOSED"}[outcome]
    if observation["state"] != expected_state:
        _fail(f"Outcome {outcome} conflicts with observed tracker state {observation['state']}.")

    evidence_text = _read_text(evidence_path, "evidence.md")
    current_block, current_values, historical_text = _current_block(evidence_text)
    historical_values = _fields(historical_text)
    identity_values = current_values if current_block is not None else historical_values
    evidence_run = _first(identity_values, "delivery_run")
    evidence_lane = _first(identity_values, "lane")
    if evidence_run != run or evidence_lane != lane:
        _fail("Canonical Evidence delivery_run/lane does not match the Close request.")
    existing_pr = _concrete_existing_pr(current_values, historical_values, observation["repository"])
    if existing_pr is not None and existing_pr != (observation["repository"], observation["number"]):
        _fail("Canonical Evidence contains a different concrete pull-request identity.")
    _existing_conflicts(current_values, observation, outcome)

    reviewed = _reviewed_head(runtime, state, current_values, historical_values, directory)
    relation_values = dict(historical_values)
    for key, entries in current_values.items():
        relation_values.setdefault(key, []).extend(entries)
    archive_reviewed = _first(relation_values, "reviewed_diff_archive_reviewed_head")
    if archive_reviewed is not None and _sha(archive_reviewed, "archive reviewed head") != reviewed:
        _fail("The evidence archive is bound to another reviewed_head.")
    _archive_content(
        runtime,
        relation_values,
        directory,
        observation["base_revision"],
        observation["head_revision"],
    )
    relation = _relation_proof(
        runtime,
        current_values,
        historical_values,
        directory,
        reviewed,
        observation["head_revision"],
        observation["base_revision"],
    )
    merge_proof = _merge_proof(
        runtime,
        relation_values,
        directory,
        outcome,
        observation["state"],
        observation["head_revision"],
        observation["base_revision"],
        observation["merged_revision"],
        reviewed,
    )
    if outcome == "merged" and relation == "published-content-equivalent":
        # Preserve the stronger proof in the current outcome while still
        # requiring the effective merge itself to match the published PR.
        pass

    block = _canonical_current_block(
        observation,
        outcome,
        reviewed,
        relation,
        merge_proof,
    )
    new_text, changed = _replace_current(evidence_text, block)
    if changed:
        _atomic_write(evidence_path, new_text)
    return {
        "recorded": True,
        "eligible": True,
        "changed": changed,
        "writes_performed": changed,
        "delivery_run": run,
        "lane": lane,
        "outcome": outcome,
        "status": "delivered" if outcome == "merged" else "abandoned",
        "pull_request": observation["url"],
        "reviewed_head": reviewed,
        "original_pr_head": observation["head_revision"],
        "base_revision": observation["base_revision"],
        "merged_revision": observation["merged_revision"],
        "effective_head": observation["merged_revision"],
        "published_head_proof": relation,
        "merge_proof": merge_proof,
        "evidence_path": evidence_path.as_posix(),
        "observation_path": observed_path.as_posix(),
    }


def _load_runtime(root: Path, run: str) -> Any:
    helper_path = Path(__file__).with_name("delivery_runtime.py")
    spec = importlib.util.spec_from_file_location("delivery_runtime_for_outcome_cli", helper_path)
    if spec is None or spec.loader is None:
        raise OutcomeError(f"Cannot import {helper_path}")
    module = importlib.util.module_from_spec(spec)
    # The installed helper is loaded in-place for Close; avoid creating a
    # consumer-project __pycache__ as a side effect of a read/atomic-write
    # operation.
    exec(compile(helper_path.read_bytes(), str(helper_path), "exec"), module.__dict__)
    return module.Runtime(root, run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    close = subparsers.add_parser("close-record", help="validate a verified PR observation and write Evidence current outcome")
    close.add_argument("--root", type=Path, default=Path.cwd())
    close.add_argument("--run", required=True)
    close.add_argument("--outcome", choices=sorted(OUTCOMES), required=True)
    close.add_argument("--pr", required=True)
    close.add_argument("--verified", action="store_true")
    close.add_argument("--file", default="runtime/observed-pr.json")
    args = parser.parse_args(argv)
    try:
        runtime = _load_runtime(args.root, args.run)
        result = close_record(runtime, args.outcome, args.verified, args.pr, args.file)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OutcomeError, OSError, ValueError) as exc:
        print(f"DELIVERY_OUTCOME: blocked\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
