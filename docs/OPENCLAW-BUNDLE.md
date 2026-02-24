# Using Agent Rating Pro with an OpenClaw Bundle

This document explains how to run Agent Rating Pro as part of an OpenClaw-based assistant package.

## Architecture

- **OpenClaw**: conversation + orchestration layer (tool routing, policy, memory)
- **Agent Rating Pro**: task quality ledger (performance/result ratings + lessons)
- **Your app(s)**: domain UIs and APIs

## Recommended Pattern

1. User asks OpenClaw to execute a task.
2. OpenClaw performs work via allowlisted tools.
3. At completion, OpenClaw records:
   - task metadata
   - performance/result rating
   - what worked / what to change
   - linked artifacts
4. Future tasks query similar prior tasks to improve outcome quality.

## Safety Model

- Conversation can be broad/open.
- Execution is constrained by explicit tool allowlists and approvals.
- Rating updates are append-only operational records (auditable).

## Suggested Hooks

- `task.start` → create task entry (`add`, `status IN_PROGRESS`)
- `task.done` → attach artifacts + ratings (`rate`, `attach`, `status DONE`)
- `task.fail` → capture failure lessons + remediation items

## Example Automation Snippets

```bash
# Start
python3 scripts/task_rating_pro.py add --id run_20260224_001 --title "Weekly custody export" --tag custody
python3 scripts/task_rating_pro.py status --id run_20260224_001 --status IN_PROGRESS

# Complete
python3 scripts/task_rating_pro.py attach --id run_20260224_001 --kind report --path "reports/WEEKLY.md"
python3 scripts/task_rating_pro.py rate --id run_20260224_001 --performance 5 --result 4 --worked "Clear status updates" --change "Add stronger error handling"
python3 scripts/task_rating_pro.py status --id run_20260224_001 --status DONE
```

## Operational Tip

Use tags aggressively (`custody`, `qa`, `release`, `triage`) so `query`/`lessons` stay high-signal.
