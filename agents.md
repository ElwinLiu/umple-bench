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

## Loading Reference Documents

When starting work on this repository, agents should load the following reference documents:

```
references/core-concepts.md    - Harbor core concepts and terminology
references/getting-started.md  - Terminal Bench overview and quick start
references/task-structure.md   - Task format and required files
references/agents.md           - Agent evaluation and integration guide
references/llm-judge.md        - LLM-as-judge verification methods
```
