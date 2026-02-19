"""Name-agnostic verification of the Door state machine.

This verifier compares the generated machine against an oracle machine using
directed graph isomorphism. State and event identifiers may differ.
Parallel transitions between the same source/target are treated as equivalent.
"""

from pathlib import Path
import subprocess
import sys
import tempfile

from state_machine_graph import (
    extract_all_machine_models,
    load_class,
    machine_sets_isomorphic,
)

CANDIDATE_MODULE_PATH = Path("/app/Door.py")
UMPLE_JAR = Path("/opt/umple/umple.jar")
ORACLE_UMPLE = """class Door {
  sm {
    Closed {
      open -> Open;
      lock -> Locked;
    }
    Open {
      close -> Closed;
    }
    Locked {
      unlock -> Closed;
    }
  }
}
"""


def load_oracle_class():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        oracle_ump = tmp_path / "door_oracle.ump"
        oracle_ump.write_text(ORACLE_UMPLE, encoding="utf-8")

        result = subprocess.run(
            ["java", "-jar", str(UMPLE_JAR), "-g", "Python", str(oracle_ump)],
            cwd=tmpdir,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "Failed to generate oracle Python from Umple:\n"
                f"{result.stdout}\n{result.stderr}"
            )

        oracle_module = tmp_path / "Door.py"
        return load_class(oracle_module, "Door", strict_class_name=False)


def main():
    candidate_class = load_class(CANDIDATE_MODULE_PATH, "Door", strict_class_name=False)
    oracle_class = load_oracle_class()

    candidate_models = extract_all_machine_models(candidate_class)
    oracle_models = extract_all_machine_models(oracle_class)

    equivalent, reason = machine_sets_isomorphic(oracle_models, candidate_models)
    assert equivalent, (
        f"State machine mismatch: {reason}. "
        f"oracle={oracle_models}, candidate={candidate_models}"
    )

    print("OK: Door state machine matches oracle up to state/event renaming")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
