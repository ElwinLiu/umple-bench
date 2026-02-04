# umple-bench

Docker-only benchmark runner for **state-machine generation** tasks (Umple models) based on `umple-bench-spec.md`.

## Quick start

1. Install (editable):
   - `python -m pip install -e .`
2. Run a seeded task:
   - `umple-bench run --dataset state-machines==0.1 --task-id hotel-booking --model local --harness-cmd -- sh -lc 'cp /task/fixtures/submission.ump /out/submission.ump'`

That example harness just copies the task’s fixture solution into `/out/submission.ump` so you can verify the runner end-to-end.

## Requirements

- Docker Desktop / Docker Engine running (the runner uses the `docker` CLI).

## CLI

`umple-bench run` requires:
- `--dataset <name==version>` or `--task-id <id>`
- `--harness-cmd -- <argv...>`

Optional:
- `--model <id>`
- `--output-dir <path>`

## Task contract

Each task directory contains:
- `task.yaml` (metadata: `id`, `timeout_seconds`, `memory_mb`, `tags`, `entrypoint`)
- `req.md` and `prompt.md`
- `tests/` (task-specific checks)
- `run-tests.sh` (writes `/out/results.json`)
- `Dockerfile`

Inside the container, these paths are mounted:
- `/task` (read-only): the task directory
- `/out` (read-write): outputs (`submission.ump`, logs, `results.json`, optional `usage.json`)

## Results

Per task, the runner expects `/out/results.json` with required fields:
- `task_id`, `model_id`, `pass_rate`, `error_rate`, `num_tests`, `num_passed`, `num_failed`
- `generation_time_ms`, `test_time_ms`, `timeout`
- `stdout`, `stderr` (paths or inline strings)

The runner also writes `run.json` in the run output directory with aggregated metadata.

## Registry

`datasets/registry.yaml` stores dataset paths **relative to the registry file’s directory**.
