# Umple-Bench (State Machines) — Medium-Detail Overview

## Scope
- Build a Docker-only benchmark runner for **state-machine generation** from requirements.
- Evaluate with **test-based verification**, not diffs.
- Provide a fixed **results schema** for all tasks.
- Include timeouts, memory limits, and tags in task metadata.
- Seed with requirements examples (hotel booking, driver’s license).

## CLI Contract
- Primary command: `umple-bench run`
- Required inputs:
  - `--harness-cmd -- <argv...>` (argv list only)
  - `--dataset <name==version>` or `--task-id <id>`
- Optional:
  - `--model <id>` (passed through; harness decides how to use it)
  - `--output-dir <path>`
- CLI prints a concise summary and writes a structured results file.

## Task Format (per task)
- `task.yaml`
  - `id`, `name`, `description`
  - `timeout_seconds`, `memory_mb`
  - `tags` (e.g., `basic`, `nested`, `guards`, `timed`)
  - `entrypoint` for tests (e.g., `run-tests.sh`)
- `req.md` (requirements)
- `prompt.md` (prompt given to the harness)
- `tests/` (test cases)
- `Dockerfile` (or `docker-compose.yaml`)
- `run-tests.sh` (executes tests and writes fixed results JSON)

## Harness Contract
- Harness is a user-provided command, run inside the task container.
- It reads `req.md` and `prompt.md`.
- It outputs a single Umple model file to a known location (e.g., `submission.ump`).
- It may emit optional `usage.json` if it can track token/costs.
- CLI passes `--model` to the harness via environment variable.

## Execution Flow (Docker Only)
1. Resolve task from dataset.
2. Build the task’s Docker image.
3. Run container with mounted task and output directories.
4. Execute `--harness-cmd` inside container.
5. Run `run-tests.sh` inside container.
6. Collect fixed results JSON plus logs.
7. Emit a run summary.

## Fixed Results Schema (per task)
Required fields:
- `task_id`
- `model_id`
- `pass_rate`
- `error_rate`
- `num_tests`
- `num_passed`
- `num_failed`
- `generation_time_ms`
- `test_time_ms`
- `timeout` (boolean)
- `stderr` and `stdout` (paths or inline)
Optional:
- `cost` (if harness provides usage)
- `notes`

## Dataset/Registry
- Registry file lists datasets by `name`, `version`, `path`.
- CLI can resolve by `name==version` and run a subset by `task-id`.
