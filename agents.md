# agents.md

> **Agent Instructions**: When working with tasks in this repository, load and reference the documentation from the `references/` folder for detailed information about Terminal-Bench, task structure, agent evaluation, and LLM-as-judge verification.

## Purpose
This repository contains **Harbor / Terminal-Bench-style tasks** for evaluating terminal agents' performance on Umple.

## Current tasks

Current dataset lives under `tasks/` and contains five Umple state-machine tasks:
- `umple-state-machine-door`
- `umple-state-machine-hotel-booking`
- `umple-state-machine-drivers-license`
- `umple-state-machine-credit-card`
- `umple-state-machine-agent-loop`

Input: instruction with requirements in Umple syntax.
Output: a single `.ump` file in `/app` (task-specific filename).

## Quick start

```bash
harbor --help
```

## Verifier Shared Helper Workflow

State-machine verifier logic is maintained in one canonical file:

`scripts/state_machine_graph.py`

Each task keeps a local copy at:

`tasks/<task-name>/tests/state_machine_graph.py`

This duplication is intentional because Harbor uploads only the task-local `tests/` directory into `/tests` during verifier execution, so verifiers must remain self-contained per task.

When updating verifier graph/isomorphism logic:

```bash
scripts/sync_state_machine_graph.sh
scripts/sync_state_machine_graph.sh --check
```

- `sync` copies the canonical helper into all task-local verifier test directories.
- `--check` validates that all task-local copies match the canonical source (useful for CI/pre-commit).

## Loading Reference Documents

When starting work on this repository, agents should load the following reference documents:

```
references/core-concepts.md    - Harbor core concepts and terminology
references/getting-started.md  - Terminal Bench overview and quick start
references/task-structure.md   - Task format and required files
references/agents.md           - Agent evaluation and integration guide
references/llm-judge.md        - LLM-as-judge verification methods
```
