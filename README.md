# Agent Rating Pro

Rate **how work was done** separately from **what outcome was delivered**.

Agent Rating Pro is a lightweight task ledger for AI-assisted work:
- ⭐ **Performance** rating (process quality)
- ⭐ **Result** rating (final output quality)
- Artifact tracking (PDFs, links, DB refs)
- Reusable lessons (`worked`, `change`) for continuous improvement

This is designed for teams/agents that want repeatable, high-quality execution instead of vibe-based retros.

---

## Why two ratings?

Most systems mix process + outcome into one score. That hides signal.

Agent Rating Pro keeps them separate:

- **Performance**: speed, communication, discipline, error handling, iteration quality.
- **Result**: usefulness, correctness, acceptance by user/stakeholder.

Example:
- Performance ⭐⭐⭐⭐⭐ (excellent execution)
- Result ⭐⭐⭐☆☆ (output missed one requirement)

That tells you *exactly* what to fix.

---

## Quick Start

From repo root:

```bash
python3 scripts/task_rating_pro.py init
```

Add a task:

```bash
python3 scripts/task_rating_pro.py add \
  --id custody_timeline_cleanup_001 \
  --title "Cleanup timeline categories/descriptions" \
  --tag custody \
  --accept "All selected rows reviewed and normalized"
```

Set status:

```bash
python3 scripts/task_rating_pro.py status --id custody_timeline_cleanup_001 --status IN_PROGRESS
```

Rate performance/result:

```bash
python3 scripts/task_rating_pro.py rate \
  --id custody_timeline_cleanup_001 \
  --performance 5 \
  --result 4 \
  --note "Great execution; one category still needed manual correction" \
  --worked "Clear progress updates" \
  --worked "Evidence-first review" \
  --change "Strengthen edge-case category rules"
```

Attach artifacts:

```bash
python3 scripts/task_rating_pro.py attach \
  --id custody_timeline_cleanup_001 \
  --kind report \
  --path "reports/CLEANUP-SUMMARY.md" \
  --meta '{"channel":"telegram","messageId":"123"}'
```

Show task summary:

```bash
python3 scripts/task_rating_pro.py show --id custody_timeline_cleanup_001
```

Query similar tasks:

```bash
python3 scripts/task_rating_pro.py query --tag custody --q "timeline cleanup" --limit 5
```

Aggregate lessons:

```bash
python3 scripts/task_rating_pro.py lessons --tag custody --limit 10
```

---

## Example Ledger

See `examples/task-ledger.sample.json` for a realistic sample dataset.

Default ledger path (workspace-relative):

`memory/task-ledger.json`

Schema reference:

`references/task-ledger.schema.json`

---

## Suggested Workflow

1. Create task with acceptance criteria.
2. Track status as work progresses.
3. Attach artifacts/proof.
4. Rate **Performance** and **Result** separately.
5. Record `worked` + `change` bullets.
6. Reuse lessons on next similar task.

---

## Roadmap (short)

- Markdown/HTML report export
- Lightweight local viewer dashboard
- Optional trend analytics (per tag/agent)
- OpenClaw bundle integration profile

---

## License

MIT (see `LICENSE`).
