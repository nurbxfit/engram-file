#!/usr/bin/env python3
"""Engram — file-based memory store CLI. Query, add, archive, and manage memory entries."""

import argparse
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path


# Project root = CWD by default. Override via --root or ENGRAM_PROJECT_ROOT env.
# The script can live anywhere — CWD is always the target project directory.
PROJECT_ROOT = Path(os.environ.get("ENGRAM_PROJECT_ROOT", os.getcwd()))
MEMORY_DIR = PROJECT_ROOT / "memory"
INDEX_PATH = MEMORY_DIR / "index.jsonl"
ARCHIVE_PATH = MEMORY_DIR / "archive.jsonl"
DETAILS_DIR = MEMORY_DIR / "details"
BY_MODULE_DIR = MEMORY_DIR / "by-module"

REPO_BASE = "https://raw.githubusercontent.com/nurbxfit/engram-file/main"

# Paths the CLI can bootstrap when they don't exist in the target project
BOOTSTRAP_SOURCES = {
    ".agents/skills/memory.md": f"{REPO_BASE}/.agents/skills/memory.md",
}

SCHEMA = {
    "required": ["ts", "type", "topic", "tags", "note", "status"],
    "optional": ["details", "module", "layer", "id", "supersedes"],
    "valid_types": ["decision", "error", "pattern", "convention"],
    "valid_status": ["active", "superseded"],
}


def _now() -> str:
    return date.today().isoformat()


def _generate_id(entry: dict) -> str:
    slug = entry.get("topic", "unknown").replace(" ", "-").lower()
    ts_short = entry.get("ts", _now()).replace("-", "")
    return f"{slug}-{ts_short}"


def _download_text(url: str) -> str:
    """Download a URL and return its body as text. Exits on failure."""
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read().decode("utf-8")
    except Exception as e:
        print(f"✖  Failed to download {url}: {e}", file=sys.stderr)
        sys.exit(1)


def _read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file, returning parsed entries. Silently skips bad lines."""
    if not path.exists():
        return []
    entries = []
    with open(path, "r") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"⚠  Warning: {path.name}:{lineno} — {e}", file=sys.stderr)
    return entries


def _write_jsonl(path: Path, entries: list[dict]):
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def _validate_entry(entry: dict, source: str = "entry") -> list[str]:
    errors = []
    for field in SCHEMA["required"]:
        if field not in entry:
            errors.append(f"{source}: missing required field '{field}'")
    if "type" in entry and entry["type"] not in SCHEMA["valid_types"]:
        errors.append(f"{source}: invalid type '{entry['type']}' — must be one of {SCHEMA['valid_types']}")
    if "status" in entry and entry["status"] not in SCHEMA["valid_status"]:
        errors.append(f"{source}: invalid status '{entry['status']}' — must be one of {SCHEMA['valid_status']}")
    if "tags" in entry and not isinstance(entry["tags"], list):
        errors.append(f"{source}: 'tags' must be a list")
    if "details" in entry and entry["details"]:
        detail_path = DETAILS_DIR / entry["details"]
        if not detail_path.exists():
            errors.append(f"{source}: details file '{entry['details']}' not found at {detail_path}")
    return errors


def cmd_add(args):
    entry = {
        "ts": args.ts or _now(),
        "type": args.type,
        "topic": args.topic,
        "tags": args.tags.split(",") if args.tags else [],
        "note": args.note,
        "status": "active",
    }
    if args.module:
        entry["module"] = args.module
    if args.layer:
        entry["layer"] = args.layer
    if args.details:
        entry["details"] = args.details
    if args.id:
        entry["id"] = args.id
    else:
        entry["id"] = _generate_id(entry)
    if args.supersedes:
        entry["supersedes"] = args.supersedes

    errors = _validate_entry(entry)
    if errors:
        for e in errors:
            print(f"✖  {e}", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"✓  Added entry '{entry['topic']}' ({entry['id']})")


def cmd_query(args):
    entries = _read_jsonl(INDEX_PATH)
    results = []

    for entry in entries:
        if entry.get("status") != "active":
            continue
        if args.type and entry.get("type") != args.type:
            continue
        if args.module and entry.get("module") != args.module:
            continue
        if args.tags:
            entry_tags = set(entry.get("tags", []))
            query_tags = set(args.tags.split(","))
            if not query_tags.intersection(entry_tags):
                continue
        if args.topic and args.topic.lower() not in entry.get("topic", "").lower():
            continue
        results.append(entry)

    if results:
        print(f"Found {len(results)} active entr{'y' if len(results) == 1 else 'ies'}:")
        print()
        for e in results:
            details_mark = " 📄" if e.get("details") else ""
            print(f"  [{e['type']:12}] {e['topic']}{details_mark}")
            print(f"           {e['note']}")
            print(f"           tags: {', '.join(e.get('tags', []))}")
            if e.get("module"):
                print(f"           module: {e['module']}")
            print()
    else:
        print("No matching active entries found.")


def cmd_archive(args):
    entries = _read_jsonl(INDEX_PATH)
    target = args.id or args.topic
    if not target:
        print("✖  Specify --id or --topic to archive.", file=sys.stderr)
        sys.exit(1)

    found = None
    remaining = []
    for entry in entries:
        if entry.get("status") != "active":
            remaining.append(entry)
            continue
        if args.id and entry.get("id") == args.id:
            found = entry
            continue
        if args.topic and entry.get("topic") == args.topic:
            found = entry
            continue
        remaining.append(entry)

    if not found:
        print(f"✖  No active entry found matching '{target}'.", file=sys.stderr)
        sys.exit(1)

    found["status"] = "superseded"
    _write_jsonl(INDEX_PATH, remaining)
    with open(ARCHIVE_PATH, "a") as f:
        f.write(json.dumps(found, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"✓  Archived '{found['topic']}' ({found['id']}) → archive.jsonl")


def cmd_digest(args):
    entries = _read_jsonl(INDEX_PATH)
    active = [e for e in entries if e.get("status") == "active"]
    archive_count = len(_read_jsonl(ARCHIVE_PATH))

    if not active:
        print("(memory is empty — run `engram init` to seed it)")
        return

    task_hint = args.task.lower() if args.task else ""
    matched = []
    unmatched = []
    for e in active:
        if not task_hint:
            matched.append(e)
            continue
        search_text = f"{e.get('topic', '')} {e.get('note', '')} {' '.join(e.get('tags', []))} {e.get('module', '')}".lower()
        if task_hint in search_text:
            matched.append(e)
        else:
            unmatched.append(e)

    total = len(active)
    print(f"Memory digest — {total} active, {archive_count} archived")
    print()

    if matched:
        print(f"Relevant to task{' (' + task_hint + ')' if task_hint else ''}:")
        for e in matched:
            details_mark = " 📄" if e.get("details") else ""
            print(f"  [{e['type']:12}] {e['topic']}{details_mark}")
            print(f"           {e['note']}")
        print()

    if unmatched and args.verbose:
        print(f"Other entries ({len(unmatched)}):")
        for e in unmatched:
            print(f"  [{e['type']:12}] {e['topic']} — {e['note']}")


def cmd_validate(args):
    paths = [INDEX_PATH, ARCHIVE_PATH]
    all_errors = []

    for path in paths:
        if not path.exists():
            continue
        entries = _read_jsonl(path)
        if not entries:
            print(f"✓  {path.name}: 0 entries (empty)")
            continue

        errors_for_file = []
        for idx, entry in enumerate(entries):
            entry_id = entry.get("id", entry.get("topic", f"line {idx + 1}"))
            errs = _validate_entry(entry, source=f"{path.name}:{entry_id}")
            errors_for_file.extend(errs)

        if errors_for_file:
            print(f"✖  {path.name}: {len(errors_for_file)} error(s)")
            for e in errors_for_file:
                print(f"     {e}")
        else:
            print(f"✓  {path.name}: {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} valid")

        all_errors.extend(errors_for_file)

    if all_errors:
        sys.exit(1)
    print("All checks passed.")


def _ensure_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True)
        print(f"✓  Created {path}/")


def cmd_init(args):
    if INDEX_PATH.exists() and INDEX_PATH.stat().st_size > 0 and not args.force:
        print("✖  index.jsonl already has content. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    _ensure_dir(MEMORY_DIR)
    _ensure_dir(DETAILS_DIR)
    _ensure_dir(BY_MODULE_DIR)
    for module in ("auth", "db", "api"):
        _ensure_dir(DETAILS_DIR / module)

    init_entry = {
        "ts": _now(),
        "id": "memory-system-schema-v1",
        "type": "pattern",
        "topic": "memory-system",
        "tags": ["memory", "meta", "workflow"],
        "note": "Two-layer file-based memory: index.jsonl for scan, details/*.md for deep context. Query via engram CLI.",
        "status": "active",
        "module": "core",
        "layer": "infra",
        "details": None,
    }
    _write_jsonl(INDEX_PATH, [init_entry])
    print(f"✓  Initialized index.jsonl.")

    if args.pull_skills:
        print()
        for rel_path, url in BOOTSTRAP_SOURCES.items():
            target = PROJECT_ROOT / rel_path
            if target.exists():
                print(f"•  {rel_path} already exists, skipping")
                continue
            text = _download_text(url)
            _ensure_dir(target.parent)
            with open(target, "w") as f:
                f.write(text)
            print(f"✓  Downloaded {rel_path}")


def cmd_sync_views(args):
    entries = _read_jsonl(INDEX_PATH) + _read_jsonl(ARCHIVE_PATH)
    by_module: dict[str, list[dict]] = {}

    for entry in entries:
        module = entry.get("module", "_unassigned")
        by_module.setdefault(module, []).append(entry)

    BY_MODULE_DIR.mkdir(parents=True, exist_ok=True)

    for f in BY_MODULE_DIR.iterdir():
        if f.suffix == ".jsonl" or f.name in ("README.md", ".gitkeep"):
            continue
        f.unlink()

    for module, mod_entries in sorted(by_module.items()):
        view_path = BY_MODULE_DIR / f"{module}.jsonl"
        _write_jsonl(view_path, mod_entries)

    print(f"✓  Synced {len(by_module)} module view(s) to by-module/")
    for module in sorted(by_module):
        count = len(by_module[module])
        print(f"     {module}/ — {count} entr{'y' if count == 1 else 'ies'}")


def _resolve_root(args) -> Path:
    explicit = getattr(args, "root", None)
    if explicit:
        return Path(explicit).resolve()
    env = os.environ.get("ENGRAM_PROJECT_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd()


def main():
    parser = argparse.ArgumentParser(
        description="Engram — file-based memory store CLI.",
        epilog=(
            "Commands: add, query, archive, digest, validate, init, sync-views\n"
            "  add         Add a new memory entry (validated)\n"
            "  query       Query active entries by topic/tags/type/module\n"
            "  archive     Move a superseded entry to archive.jsonl\n"
            "  digest      Print a session-start digest of relevant active entries\n"
            "  validate    Check index.jsonl and archive.jsonl for schema errors\n"
            "  init        Scaffold memory/ directory and seed index.jsonl\n"
            "  sync-views  Regenerate by-module/ views from the index\n"
            "\n"
            "Read/writes the project's memory/ directory. Python stdlib only — no dependencies."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", default=None, help="Project root dir (default: CWD, env: ENGRAM_PROJECT_ROOT)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new memory entry")
    p_add.add_argument("--ts", default=None, help="ISO date (default: today)")
    p_add.add_argument("--type", required=True, choices=SCHEMA["valid_types"], help="Entry type")
    p_add.add_argument("--topic", required=True, help="Short topic slug")
    p_add.add_argument("--tags", default="", help="Comma-separated tags")
    p_add.add_argument("--note", required=True, help="One-line summary")
    p_add.add_argument("--module", default=None, help="Module name (auth/db/api/...)")
    p_add.add_argument("--layer", default=None, help="Layer (frontend/backend/infra)")
    p_add.add_argument("--details", default=None, help="Detail filename (relative to details/)")
    p_add.add_argument("--id", default=None, help="Unique ID (auto-generated if omitted)")
    p_add.add_argument("--supersedes", default=None, help="ID of the entry this supersedes")

    p_q = sub.add_parser("query", help="Query active entries")
    p_q.add_argument("--topic", default=None, help="Filter by topic (substring match)")
    p_q.add_argument("--tags", default=None, help="Filter by comma-separated tags (any match)")
    p_q.add_argument("--type", default=None, choices=SCHEMA["valid_types"], help="Filter by type")
    p_q.add_argument("--module", default=None, help="Filter by module")

    p_a = sub.add_parser("archive", help="Move an active entry to archive.jsonl")
    p_a.add_argument("--id", default=None, help="ID of entry to archive")
    p_a.add_argument("--topic", default=None, help="Topic of entry to archive")

    p_d = sub.add_parser("digest", help="Print session-start digest")
    p_d.add_argument("--task", default="", help="Task description for relevance matching")
    p_d.add_argument("--verbose", "-v", action="store_true", help="Show all entries, including unmatched")

    sub.add_parser("validate", help="Check index and archive for schema errors")

    p_i = sub.add_parser("init", help="Scaffold memory/ directory and seed index.jsonl")
    p_i.add_argument("--force", "-f", action="store_true", help="Overwrite existing content")
    p_i.add_argument("--pull-skills", action="store_true", help="Download latest .agents/skills/ from GitHub")

    sub.add_parser("sync-views", help="Regenerate by-module/ views from the index")

    args = parser.parse_args()

    # Resolve project root and set module-level paths
    global PROJECT_ROOT, MEMORY_DIR, INDEX_PATH, ARCHIVE_PATH, DETAILS_DIR, BY_MODULE_DIR
    PROJECT_ROOT = _resolve_root(args)
    MEMORY_DIR = PROJECT_ROOT / "memory"
    INDEX_PATH = MEMORY_DIR / "index.jsonl"
    ARCHIVE_PATH = MEMORY_DIR / "archive.jsonl"
    DETAILS_DIR = MEMORY_DIR / "details"
    BY_MODULE_DIR = MEMORY_DIR / "by-module"

    commands = {
        "add": cmd_add,
        "query": cmd_query,
        "archive": cmd_archive,
        "digest": cmd_digest,
        "validate": cmd_validate,
        "init": cmd_init,
        "sync-views": cmd_sync_views,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
