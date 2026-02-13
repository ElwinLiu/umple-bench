# Central Prompt Library

This directory contains prompt templates used by external/internal agents in this repository.

## Goals

- Keep prompts in one place so multiple agents can share and evolve them.
- Make prompt changes reviewable without touching agent runtime logic.
- Support benchmark experiments where prompts are versioned and compared.

## Layout

- `prompts/agents/base/` — shared base templates intended for reuse.
- `prompts/agents/<agent-name>/` — agent-specific prompt templates when needed.

## Current usage

- `external_agents/pi/agent.py` reads:
  - `prompts/agents/base/task_script_prompt.txt`

If this file is missing, the Pi agent falls back to an internal default template.
