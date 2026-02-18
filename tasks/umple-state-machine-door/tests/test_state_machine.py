"""Name-agnostic verification of the Door state machine.

This verifier compares the generated machine against an oracle machine using
directed multigraph isomorphism. State and event identifiers may differ.
"""
from dataclasses import dataclass
from enum import Enum
from importlib import util
import inspect
import itertools
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Optional, Tuple

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


@dataclass(frozen=True)
class MachineModel:
    state_count: int
    initial_index: int
    adjacency: Tuple[Tuple[int, ...], ...]


def load_class(module_path: Path, class_name: Optional[str] = None):
    if not module_path.exists():
        raise FileNotFoundError(f"Expected {module_path} to exist")

    spec = util.spec_from_file_location(module_path.stem, module_path)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    if class_name is not None and hasattr(module, class_name):
        return getattr(module, class_name)

    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__:
            return obj
    raise RuntimeError(f"No class found in module {module_path}")


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
        return load_class(oracle_module, "Door")


def discover_state_machine_accessors(cls):
    enum_classes = []
    for _, obj in inspect.getmembers(cls, inspect.isclass):
        if obj is Enum:
            continue
        if issubclass(obj, Enum):
            enum_classes.append(obj)

    if len(enum_classes) != 1:
        raise AssertionError(
            "Expected exactly one state machine enum in Door class, "
            f"found {len(enum_classes)}"
        )

    enum_cls = enum_classes[0]
    probe = cls()
    getter_name = None
    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if not name.startswith("get") or name.endswith("FullName"):
            continue
        if len(inspect.signature(method).parameters) != 1:
            continue
        try:
            value = getattr(probe, name)()
        except Exception:
            continue
        if isinstance(value, enum_cls):
            getter_name = name
            break

    if getter_name is None:
        raise AssertionError("Could not find state-machine getter")

    setter_name = f"set{getter_name[3:]}"
    if not hasattr(cls, setter_name):
        raise AssertionError(f"Could not find setter {setter_name}")

    return enum_cls, getter_name, setter_name


def discover_event_names(cls, getter_name, setter_name):
    events = []
    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if name.startswith("_"):
            continue
        if name in {"__init__", "delete", getter_name, setter_name}:
            continue
        if name.startswith("get") and name.endswith("FullName"):
            continue
        if len(inspect.signature(method).parameters) != 1:
            continue

        probe = cls()
        try:
            outcome = getattr(probe, name)()
        except Exception:
            continue
        if isinstance(outcome, bool):
            events.append(name)

    if not events:
        raise AssertionError("No event methods discovered")
    return sorted(set(events))


def extract_machine_model(cls):
    enum_cls, getter_name, setter_name = discover_state_machine_accessors(cls)
    states = list(enum_cls)
    if not states:
        raise AssertionError("No states discovered")

    index = {state: idx for idx, state in enumerate(states)}
    probe = cls()
    initial_state = getattr(probe, getter_name)()
    initial_index = index[initial_state]

    event_names = discover_event_names(cls, getter_name, setter_name)
    adjacency = [[0 for _ in states] for _ in states]

    for source in states:
        for event in event_names:
            obj = cls()
            getattr(obj, setter_name)(source)
            before = getattr(obj, getter_name)()
            result = getattr(obj, event)()
            after = getattr(obj, getter_name)()

            if not isinstance(result, bool):
                continue
            if result:
                adjacency[index[source]][index[after]] += 1
            elif after != before:
                raise AssertionError(
                    f"Event {event} returned False but changed state "
                    f"from {before} to {after}"
                )

    frozen_adjacency = tuple(tuple(row) for row in adjacency)
    return MachineModel(
        state_count=len(states),
        initial_index=initial_index,
        adjacency=frozen_adjacency,
    )


def total_edges(model: MachineModel) -> int:
    return sum(sum(row) for row in model.adjacency)


def isomorphic_up_to_renaming(reference: MachineModel, candidate: MachineModel):
    if reference.state_count != candidate.state_count:
        return False, "State count mismatch"
    if total_edges(reference) != total_edges(candidate):
        return False, "Transition count mismatch"

    n = reference.state_count
    ref_initial = reference.initial_index
    cand_initial = candidate.initial_index
    ref_rest = [i for i in range(n) if i != ref_initial]
    cand_rest = [i for i in range(n) if i != cand_initial]

    for perm in itertools.permutations(cand_rest):
        mapping = {ref_initial: cand_initial}
        for ref_idx, cand_idx in zip(ref_rest, perm):
            mapping[ref_idx] = cand_idx

        matches = True
        for i in range(n):
            for j in range(n):
                if (
                    reference.adjacency[i][j]
                    != candidate.adjacency[mapping[i]][mapping[j]]
                ):
                    matches = False
                    break
            if not matches:
                break
        if matches:
            return True, "ok"

    return False, "No graph isomorphism found with initial-state preservation"


def main():
    candidate_class = load_class(CANDIDATE_MODULE_PATH, "Door")
    oracle_class = load_oracle_class()

    candidate_model = extract_machine_model(candidate_class)
    oracle_model = extract_machine_model(oracle_class)

    equivalent, reason = isomorphic_up_to_renaming(oracle_model, candidate_model)
    assert equivalent, (
        f"State machine mismatch: {reason}. "
        f"oracle={oracle_model}, candidate={candidate_model}"
    )

    print("OK: Door state machine matches oracle up to state/event renaming")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
