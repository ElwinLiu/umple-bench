# Umple State Machine Tasks

This folder contains Harbor/Terminal-Bench tasks that evaluate an agent's ability to generate Umple state machines from natural-language requirements.

## Task List

- `umple-state-machine-door`
  - Output file: `/app/door.ump`
  - Focus: basic 3-state door transitions
- `umple-state-machine-hotel-booking`
  - Output file: `/app/room.ump`
  - Focus: room lifecycle (available/allocated/unavailable)
- `umple-state-machine-drivers-license`
  - Output file: `/app/license.ump`
  - Focus: progression + suspension/reinstatement
- `umple-state-machine-credit-card`
  - Output file: `/app/credit_card.ump`
  - Focus: approval flow + hold behavior
- `umple-state-machine-agent-loop`
  - Output file: `/app/agent.ump`
  - Focus: branching agent runtime loop

## Verifier contract

Every task verifier:
- checks the expected output file exists
- validates Umple syntax via `/opt/umple/umple.jar`
- generates Python from Umple via `java -jar /opt/umple/umple.jar -g Python <file>.ump`
- runs behavioral checks using `tests/test_state_machine.py`
- writes reward to `/logs/verifier/reward.txt` (`1` pass, `0` fail)

Environment note:
- `allow_internet = true` in task configs so installed agents can access model APIs and perform setup.

## Run locally

```bash
# Single task
harbor run -p tasks/umple-state-machine-door -a oracle

# Full dataset
harbor run -p tasks/ -a oracle -n 4
```

## Adding a new task

Use the scaffold helper:

```bash
./scripts/scaffold_umple_task.sh <task-name> <output-file> [difficulty]
```

Then customize:
- `instruction.md`
- `solution/solve.sh`
- `tests/test.sh` with strict required-transition checks
