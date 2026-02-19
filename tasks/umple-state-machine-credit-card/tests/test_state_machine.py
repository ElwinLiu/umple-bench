"""Name-agnostic verification of the CreditCardApplication state machines.

Compares generated machines against expected directed-graph models.
State-machine, state, and event identifiers may differ.
"""

from pathlib import Path
import sys

from state_machine_graph import (
    MachineModel,
    extract_all_machine_models,
    load_class,
    machine_sets_isomorphic,
)

CANDIDATE_MODULE_PATH = Path("/app/CreditCardApplication.py")
EXPECTED_CLASS_NAME = "CreditCardApplication"


def expected_machine_models():
    process_model = MachineModel(
        state_count=5,
        initial_index=0,
        adjacency=(
            (0, 1, 1, 1, 1),
            (0, 0, 1, 1, 1),
            (0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0),
        ),
    )
    account_status_model = MachineModel(
        state_count=2,
        initial_index=0,
        adjacency=(
            (0, 1),
            (1, 0),
        ),
    )
    return [process_model, account_status_model]


def main():
    candidate_class = load_class(CANDIDATE_MODULE_PATH, EXPECTED_CLASS_NAME)

    candidate_models = extract_all_machine_models(candidate_class)
    reference_models = expected_machine_models()

    equivalent, reason = machine_sets_isomorphic(reference_models, candidate_models)
    assert equivalent, (
        f"State machine mismatch: {reason}. "
        f"expected={reference_models}, candidate={candidate_models}"
    )

    print("OK: CreditCardApplication state machines match expected graph models")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
