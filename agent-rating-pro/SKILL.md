---
name: agent-rating-pro
description: Agent rating system with separate 5-star ratings for PERFORMANCE vs RESULT (outcome). Attach artifacts (PDFs/links/DB refs), record what worked vs what to change, and query similar past tasks to repeat 5-star outcomes. Use for assistants/teams who want continuous improvement and predictable execution.
---

# Agent Rating Pro

## What this skill is
A portable, opinionated task ledger system that turns “vibes” into operational feedback:
- Rate **PERFORMANCE** (process) separately from **RESULT** (delivered outcome).
- Store execution notes, artifacts, and acceptance criteria.
- Query similar tasks to reuse what earns 5-stars.

Default ledger path (workspace-relative): `memory/task-ledger.json`

## Quick start (commands)
Run via Python:

- Init ledger (create files if missing):
  - `python3 scripts/task_rating_pro.py init`

- Add a task:
  - `python3 scripts/task_rating_pro.py add --id my_task --title "Do the thing" --tag projectX --accept "PDF delivered"`

- Update status:
  - `python3 scripts/task_rating_pro.py status --id my_task --status IN_PROGRESS`

- Rate performance and/or result:
  - `python3 scripts/task_rating_pro.py rate --id my_task --performance 4 --result 5 --note "Great output; took 2 tries"`
  - `python3 scripts/task_rating_pro.py rate --id my_task --result 5 --note "Perfect deliverable"`

- Rate with reusable coaching bullets (these power `query` and `lessons`):
  - `python3 scripts/task_rating_pro.py rate --id my_task --performance 5 --note "Fast" --worked "Clear progress pings" --worked "No rework"`
  - `python3 scripts/task_rating_pro.py rate --id my_task --result 4 --note "Close" --change "Improve formatting" --change "Add more verbatim quotes"`

- Attach artifacts (paths/URLs/DB refs):
  - `python3 scripts/task_rating_pro.py attach --id my_task --kind pdf --path "media/outbound/report.pdf" --meta '{"channel":"telegram","messageId":"123"}'`

- Show a task (clean summary + coaching):
  - `python3 scripts/task_rating_pro.py show --id my_task`

- Query similar tasks (coaching-oriented output):
  - `python3 scripts/task_rating_pro.py query --tag projectX --q "roundtable pdf" --limit 5`

- Aggregate lessons (top what-worked / what-to-change across tasks):
  - `python3 scripts/task_rating_pro.py lessons --tag projectX --limit 10`

## Rules
- PERFORMANCE rating = how it was done (speed, comms, iteration count, QC discipline).
- RESULT rating = usefulness/quality of delivered artifact.
- Always keep ledger paths portable (workspace-relative) for ClawHub.

## References
- Ledger JSON schema: `references/task-ledger.schema.json`
