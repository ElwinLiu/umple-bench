# Task Structure

Each task in Harbor (and Terminal-Bench) is a directory with a fixed layout that defines the environment, instruction, solution, and tests.

## Task Directory Layout

A task directory should contain:

```
task-name/
├── instruction.md          # Natural language task prompt
├── task.toml              # Metadata/configuration
├── environment/           # Docker environment files/assets
├── solution/              # Oracle/reference solution
│   └── solve.sh          # Solution script (optional but recommended)
└── tests/                 # Verifier test files
    ├── test.sh           # Verifier entrypoint (required)
    └── *                 # Any additional test dependencies
```

## Required Files

### instruction.md

Natural language description of the task that will be given to the agent. This should clearly explain:
- What the agent needs to accomplish
- Any constraints or requirements
- Expected output or final state

### task.toml

Metadata and configuration for the task:

```toml
name = "task-name"
description = "Description of the task"

# Timeouts (in seconds)
timeout = 300

# Resource limits
[resources]
cpu = 2
memory = "4GB"

# Internet policy
allow_internet = false
```

### environment/

Contains Docker environment files and assets needed to run the task. This typically includes:
- `Dockerfile` - Container definition
- Any required files, scripts, or data

### solution/solve.sh

Oracle/reference solution that solves the task correctly. This is used to verify the task is solvable.

### tests/test.sh

**Required** - The verifier entrypoint that checks if the agent completed the task successfully.

## Verifier Contract

`tests/test.sh` must write reward output to one of:
- `/logs/verifier/reward.txt` - Single numeric reward (e.g., `1` or `0`)
- `/logs/verifier/reward.json` - Multi-metric numeric rewards

Use absolute paths in tests (`/app`, `/tests`, `/logs/verifier`) to avoid path issues.

## Authoring Conventions

- **Deterministic**: Keep tasks deterministic and self-contained
- **Internet**: Default to `allow_internet = false` unless required
- **Dependencies**: Keep environment dependencies inside `environment/`
- **Validation**: Validate every task with oracle before committing

## Creating a New Task

1. Initialize scaffold:
   ```bash
   harbor tasks init <task-name>
   ```

2. Move task under `tasks/<task-name>`

3. Write `instruction.md` and `task.toml`

4. Define environment in `environment/Dockerfile`

5. Implement `solution/solve.sh`

6. Implement `tests/test.sh` and ensure reward file is written

7. Run validation:
   ```bash
   harbor run -p tasks/<task-name> -a oracle
   ```

## Task Examples

For more examples, see the [Terminal-Bench task gallery](https://tbench.ai/tasks).
