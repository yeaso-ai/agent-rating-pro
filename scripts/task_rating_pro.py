#!/usr/bin/env python3
"""Task Rating Pro — portable task ledger with separate performance vs result ratings.

This script is bundled inside the task-rating-pro Skill. It is designed to be
workspace-portable (no absolute paths).

Ledger default: memory/task-ledger.json
Schema reference (optional): references/task-ledger.schema.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def default_ledger_path() -> Path:
    return Path("memory/task-ledger.json")


def ensure_ledger(path: Path) -> dict[str, Any]:
    if path.exists():
        obj = read_json(path)
        if "tasks" not in obj:
            obj["tasks"] = []
        if "updatedAt" not in obj:
            obj["updatedAt"] = now_iso()
        return obj
    obj = {"updatedAt": now_iso(), "tasks": []}
    write_json(path, obj)
    return obj


def find_task(tasks: list[dict[str, Any]], task_id: str) -> dict[str, Any] | None:
    for t in tasks:
        if t.get("id") == task_id:
            return t
    return None


def parse_meta(meta: str | None) -> Any:
    if not meta:
        return None
    try:
        return json.loads(meta)
    except json.JSONDecodeError:
        raise SystemExit("--meta must be valid JSON")


def cmd_init(args: argparse.Namespace) -> None:
    path = Path(args.ledger)
    ensure_ledger(path)
    print(f"OK init {path}")


def cmd_add(args: argparse.Namespace) -> None:
    path = Path(args.ledger)
    obj = ensure_ledger(path)
    tasks: list[dict[str, Any]] = obj["tasks"]

    if find_task(tasks, args.id):
        raise SystemExit(f"task already exists: {args.id}")

    task = {
        "id": args.id,
        "title": args.title,
        "status": args.status,
        "ratings": {
            "performance": {"stars": None, "rationale": None, "whatWorked": None, "whatToChange": None},
            "result": {"stars": None, "rationale": None, "whatWorked": None, "whatToChange": None},
        },
        "feedback": None,
        "execution": {
            "approach": args.approach,
            "steps": args.step or None,
        } if (args.approach or args.step) else None,
        "results": {
            "acceptanceCriteria": args.accept or None,
        } if args.accept else None,
        "notes": args.note,
        "tags": args.tag or None,
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
        "completedAt": None,
    }

    tasks.append(task)
    obj["updatedAt"] = now_iso()
    write_json(path, obj)
    print(f"OK add {args.id}")


def cmd_status(args: argparse.Namespace) -> None:
    path = Path(args.ledger)
    obj = ensure_ledger(path)
    t = find_task(obj["tasks"], args.id)
    if not t:
        raise SystemExit(f"task not found: {args.id}")

    t["status"] = args.status
    t["updatedAt"] = now_iso()
    if args.status in ("DONE", "SENT", "CANCELED") and not t.get("completedAt"):
        t["completedAt"] = now_iso()

    obj["updatedAt"] = now_iso()
    write_json(path, obj)
    print(f"OK status {args.id} {args.status}")


def cmd_rate(args: argparse.Namespace) -> None:
    path = Path(args.ledger)
    obj = ensure_ledger(path)
    t = find_task(obj["tasks"], args.id)
    if not t:
        raise SystemExit(f"task not found: {args.id}")

    if "ratings" not in t or t["ratings"] is None:
        t["ratings"] = {"performance": None, "result": None}

    note = args.note
    worked = args.worked or []
    change = args.change or []

    touched = []

    def apply(which: str, stars: int | None):
        nonlocal touched
        if stars is None:
            return
        if which not in t["ratings"] or t["ratings"][which] is None:
            t["ratings"][which] = {"stars": None, "rationale": None, "whatWorked": None, "whatToChange": None}
        rr = t["ratings"][which]
        rr["stars"] = stars
        if note:
            rr["rationale"] = note
        if worked:
            rr["whatWorked"] = _listify(rr.get("whatWorked")) + worked
        if change:
            rr["whatToChange"] = _listify(rr.get("whatToChange")) + change
        touched.append(which)

    apply("performance", args.performance)
    apply("result", args.result)

    if not touched:
        raise SystemExit("rate: specify --performance and/or --result")

    if note:
        t["feedback"] = note

    t["updatedAt"] = now_iso()
    obj["updatedAt"] = now_iso()
    write_json(path, obj)
    print(f"OK rate {args.id} ({', '.join(touched)})")


def cmd_attach(args: argparse.Namespace) -> None:
    path = Path(args.ledger)
    obj = ensure_ledger(path)
    t = find_task(obj["tasks"], args.id)
    if not t:
        raise SystemExit(f"task not found: {args.id}")

    results = t.get("results") or {}
    deliverables = results.get("deliverables") or []
    deliverables.append({"kind": args.kind, "path": args.path, "meta": parse_meta(args.meta)})
    results["deliverables"] = deliverables
    t["results"] = results

    t["updatedAt"] = now_iso()
    obj["updatedAt"] = now_iso()
    write_json(path, obj)
    print(f"OK attach {args.id} {args.kind}")


def _stars(t: dict[str, Any], which: str) -> int | None:
    r = t.get("ratings") or {}
    v = (r.get(which) or {}).get("stars")
    return v


def _listify(x: Any) -> list[str]:
    if not x:
        return []
    if isinstance(x, list):
        return [str(i) for i in x if i is not None]
    return [str(x)]


def _extract_coaching(t: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (whatWorked, whatToChange) from ratings if present, else empty."""
    r = t.get("ratings") or {}
    ww: list[str] = []
    wc: list[str] = []

    # Support nested rating schema
    for which in ("performance", "result"):
        rr = r.get(which) or {}
        if isinstance(rr, dict):
            ww += _listify(rr.get("whatWorked"))
            wc += _listify(rr.get("whatToChange"))

    # Support flat sample schema
    if isinstance(r, dict):
        ww += _listify(r.get("worked"))
        wc += _listify(r.get("change"))

    # de-dup preserve order
    def dedup(items: list[str]) -> list[str]:
        seen = set()
        out = []
        for it in items:
            it2 = it.strip()
            if not it2 or it2 in seen:
                continue
            seen.add(it2)
            out.append(it2)
        return out

    return dedup(ww), dedup(wc)


def cmd_show(args: argparse.Namespace) -> None:
    path = Path(args.ledger)
    obj = ensure_ledger(path)
    t = find_task(obj["tasks"], args.id)
    if not t:
        raise SystemExit(f"task not found: {args.id}")

    perf = _stars(t, "performance")
    res = _stars(t, "result")
    print(f"{t.get('id')} — {t.get('title')}")
    print(f"status: {t.get('status')} | performance: {perf} | result: {res}")
    if t.get("feedback"):
        print(f"feedback: {t.get('feedback')}")

    tags = t.get("tags") or []
    if tags:
        print("tags: " + ", ".join(tags))

    ww, wc = _extract_coaching(t)
    if ww:
        print("\nwhat worked:")
        for it in ww[:10]:
            print(f"- {it}")
    if wc:
        print("\nwhat to change:")
        for it in wc[:10]:
            print(f"- {it}")

    results = t.get("results") or {}
    dels = results.get("deliverables") or []
    if dels:
        print("\ndeliverables:")
        for d in dels[:10]:
            print(f"- {d.get('kind')}: {d.get('path')}")


def cmd_query(args: argparse.Namespace) -> None:
    """Find similar tasks and print coaching-oriented summaries."""
    path = Path(args.ledger)
    obj = ensure_ledger(path)
    tasks: list[dict[str, Any]] = obj["tasks"]

    q = (args.q or "").lower().strip()
    tagset = set(args.tag or [])

    def match(t: dict[str, Any]) -> bool:
        if tagset:
            tt = set(t.get("tags") or [])
            if not tagset.issubset(tt):
                return False
        if q:
            blob = (t.get("title") or "") + "\n" + (t.get("notes") or "") + "\n" + (t.get("feedback") or "")
            blob += "\n" + "\n".join(_extract_coaching(t)[0] + _extract_coaching(t)[1])
            return q in blob.lower()
        return True

    def score(t: dict[str, Any]) -> int:
        perf = _stars(t, "performance") or 0
        res = _stars(t, "result") or 0
        return perf + res

    hits = [t for t in tasks if match(t)]
    hits.sort(key=lambda t: (score(t), t.get("updatedAt") or t.get("createdAt") or ""), reverse=True)
    hits = hits[: args.limit]

    if not hits:
        print("No matches.")
        return

    for t in hits:
        perf = _stars(t, "performance")
        res = _stars(t, "result")
        print(f"- {t.get('id')} | {t.get('status')} | perf={perf} result={res} | {t.get('title')}")
        ww, wc = _extract_coaching(t)
        if ww:
            print("  what worked:")
            for it in ww[:3]:
                print(f"   • {it}")
        if wc:
            print("  what to change:")
            for it in wc[:3]:
                print(f"   • {it}")
        fb = t.get("feedback")
        if fb and (not ww and not wc):
            print(f"  feedback: {fb}")


def cmd_lessons(args: argparse.Namespace) -> None:
    """Aggregate coaching across a set of tasks."""
    path = Path(args.ledger)
    obj = ensure_ledger(path)
    tasks: list[dict[str, Any]] = obj["tasks"]

    tagset = set(args.tag or [])

    def match(t: dict[str, Any]) -> bool:
        if tagset:
            tt = set(t.get("tags") or [])
            if not tagset.issubset(tt):
                return False
        return True

    hits = [t for t in tasks if match(t)]
    if not hits:
        print("No matches.")
        return

    worked: dict[str, int] = {}
    change: dict[str, int] = {}

    for t in hits:
        ww, wc = _extract_coaching(t)
        for it in ww:
            worked[it] = worked.get(it, 0) + 1
        for it in wc:
            change[it] = change.get(it, 0) + 1

    def top(d: dict[str, int]) -> list[tuple[str, int]]:
        return sorted(d.items(), key=lambda kv: kv[1], reverse=True)[: args.limit]

    print("Top what worked:")
    for it, n in top(worked):
        print(f"- ({n}) {it}")

    print("\nTop what to change:")
    for it, n in top(change):
        print(f"- ({n}) {it}")



def cmd_report(args):
    data = ensure_ledger(Path(args.ledger))
    tasks = data.get("tasks", [])
    if args.tag:
        tasks = [t for t in tasks if args.tag in (t.get("tags") or [])]

    out: list[str] = []
    out.append("# Agent Rating Report")
    out.append("")
    out.append(f"Total tasks: {len(tasks)}")
    out.append("")

    for t in tasks:
        rid = t.get("id", "unknown")
        title = t.get("title", "(untitled)")
        status = t.get("status", "UNKNOWN")
        rr = t.get("ratings") or {}
        if isinstance(rr.get("performance"), int):
            perf = rr.get("performance")
        else:
            perf = _stars(t, "performance")
        if isinstance(rr.get("result"), int):
            res = rr.get("result")
        else:
            res = _stars(t, "result")
        out.append(f"## {rid} — {title}")
        out.append(f"- Status: {status}")
        out.append(f"- Performance: {perf if perf is not None else '-'}")
        out.append(f"- Result: {res if res is not None else '-'}")
        fb = t.get("feedback")
        if fb:
            out.append(f"- Note: {fb}")
        ww, wc = _extract_coaching(t)
        if ww:
            out.append("- Worked:")
            for w in ww[:10]:
                out.append(f"  - {w}")
        if wc:
            out.append("- Change:")
            for c in wc[:10]:
                out.append(f"  - {c}")
        out.append("")

    text = "\n".join(out).strip() + "\n"
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(f"report written: {out_path}")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="task_rating_pro")

    sub = ap.add_subparsers(dest="cmd", required=True)

    # Add global args to each subcommand so users can pass --ledger after the command
    def add_global(p: argparse.ArgumentParser) -> None:
        p.add_argument("--ledger", default=str(default_ledger_path()))

    p = sub.add_parser("init")
    add_global(p)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add")
    add_global(p)
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--status", default="PENDING", choices=["PENDING", "IN_PROGRESS", "DONE", "SENT", "CANCELED"])
    p.add_argument("--tag", action="append")
    p.add_argument("--accept", action="append", help="acceptance criteria")
    p.add_argument("--approach")
    p.add_argument("--step", action="append")
    p.add_argument("--note")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("status")
    add_global(p)
    p.add_argument("--id", required=True)
    p.add_argument("--status", required=True, choices=["PENDING", "IN_PROGRESS", "DONE", "SENT", "CANCELED"])
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("rate")
    add_global(p)
    p.add_argument("--id", required=True)
    p.add_argument("--performance", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--result", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--note")
    p.add_argument("--worked", action="append", help="what worked (repeatable) — can be used multiple times")
    p.add_argument("--change", action="append", help="what to change (repeatable) — can be used multiple times")
    p.set_defaults(func=cmd_rate)

    p = sub.add_parser("attach")
    add_global(p)
    p.add_argument("--id", required=True)
    p.add_argument("--kind", required=True)
    p.add_argument("--path", required=True)
    p.add_argument("--meta", help="JSON string")
    p.set_defaults(func=cmd_attach)

    p = sub.add_parser("show")
    add_global(p)
    p.add_argument("--id", required=True)
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("query")
    add_global(p)
    p.add_argument("--tag", action="append")
    p.add_argument("--q")
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=cmd_query)

    p = sub.add_parser("lessons")
    add_global(p)
    p.add_argument("--tag", action="append")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_lessons)

    p = sub.add_parser("report")
    add_global(p)
    p.add_argument("--tag")
    p.add_argument("--format", choices=["md"], default="md")
    p.add_argument("--output")
    p.set_defaults(func=cmd_report)

    return ap


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
