"""Name-agnostic verification of the License state machine.

Compares the generated machine against an oracle using directed graph
isomorphism. State-machine, state, and event identifiers may differ.
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

CANDIDATE_MODULE_PATH = Path("/app/License.py")
EXPECTED_CLASS_NAME = "License"
UMPLE_JAR = Path("/opt/umple/umple.jar")
ORACLE_UMPLE = """class License {
  level {
    noLicense {
      passG1Test() -> G1;
    }
    G1 {
      passG2Test() -> G2;
      expire() -> noLicense;
      suspend() -> suspendedG1;
    }
    G2 {
      passGTest() -> G;
      expire() -> noLicense;
      suspend() -> suspendedG2;
    }
    G {
      renew() -> G;
      suspend() -> suspendedG;
    }
    suspendedG1 {
      reinstate() -> G1;
    }
    suspendedG2 {
      reinstate() -> G2;
    }
    suspendedG {
      reinstate() -> G;
    }
  }
}
"""


def load_oracle_class():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        oracle_ump = tmp_path / "oracle.ump"
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

        return load_class(tmp_path / f"{EXPECTED_CLASS_NAME}.py", EXPECTED_CLASS_NAME)


def main():
    candidate_class = load_class(CANDIDATE_MODULE_PATH, EXPECTED_CLASS_NAME)
    oracle_class = load_oracle_class()

    candidate_models = extract_all_machine_models(candidate_class)
    oracle_models = extract_all_machine_models(oracle_class)

    equivalent, reason = machine_sets_isomorphic(oracle_models, candidate_models)
    assert equivalent, (
        f"State machine mismatch: {reason}. "
        f"oracle={oracle_models}, candidate={candidate_models}"
    )

    print("OK: License state machine matches oracle up to renaming")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
