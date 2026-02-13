# Terminal Bench Documentation

## Overview

Terminal-Bench is a benchmark for evaluating the performance of AI agents on realistic, terminal-based tasks. From compiling code to training models and setting up servers, Terminal-Bench evaluates how well agents can handle real-world, end-to-end tasks autonomously.

## What is Harbor?

Harbor is the official framework for running Terminal-Bench 2.0. It provides:

- Simple, modular interfaces for environments, agents, and tasks
- All popular CLI agents pre-integrated
- A registry of popular benchmarks and datasets
- Integrations with cloud sandbox providers like Daytona, Modal, and E2B for horizontal scaling
- Integrations with frameworks like SkyRL and GEPA for optimizing agents

## Installation

Install Harbor using uv or pip:

```bash
uv tool install harbor
```

or

```bash
pip install harbor
```

## Quick Start

### Prerequisites

- Docker installed and running on your machine
- An API key for the model you want to use (e.g., Anthropic for Claude)

### Running Terminal-Bench

Verify installation by running oracle solutions:

```bash
harbor run -d terminal-bench@2.0 -a oracle
```

Run with Claude Code on Daytona:

```bash
export DAYTONA_API_KEY="<your-daytona-api-key>"
export ANTHROPIC_API_KEY="<your-anthropic-api-key>"
harbor run \
  -d terminal-bench@2.0 \
  -m anthropic/claude-haiku-4-5 \
  -a claude-code \
  --env daytona \
  -n 32
```

## Basic Commands

```bash
harbor --help                    # View all commands
harbor datasets list             # List available datasets
harbor run --help                # View run options
harbor tasks init <task-name>   # Initialize a new task
```

## Use Cases

- **Evaluating agents**: Test Claude Code, OpenHands, Codex CLI, and more
- **Building custom benchmarks**: Create and share your own tasks
- **Running at scale**: Conduct experiments in thousands of environments in parallel
- **RL optimization**: Generate rollouts for reinforcement learning
- **Prompt optimization**: Test and improve agent prompts

## Leaderboard

Leaderboard logs are stored in the [Terminal-Bench 2.0 Leaderboard](https://huggingface.co/datasets/alexgshaw/terminal-bench-2-leaderboard) HuggingFace repository. To submit results, open a PR following the instructions in the README.

View the full leaderboard at [tbench.ai/leaderboard](https://tbench.ai/leaderboard).
