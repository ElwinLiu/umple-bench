"""Common utilities for Umple state-machine graph verification.

Source of truth for task verifier copies.
Run scripts/sync_state_machine_graph.sh to update task-local copies.
"""

from dataclasses import dataclass
from enum import Enum
from importlib import util
import inspect
import itertools
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class MachineContext:
    enum_cls: type
    getter_name: str
    setter_name: str


@dataclass(frozen=True)
class MachineModel:
    state_count: int
    initial_index: int
    adjacency: Tuple[Tuple[int, ...], ...]


def load_class(
    module_path: Path,
    class_name: Optional[str] = None,
    strict_class_name: bool = True,
):
    if not module_path.exists():
        raise FileNotFoundError(f"Expected {module_path} to exist")

    spec = util.spec_from_file_location(module_path.stem, module_path)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    if class_name is not None:
        if hasattr(module, class_name):
            return getattr(module, class_name)
        if strict_class_name:
            raise RuntimeError(f"Expected class {class_name} in {module_path}")

    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__:
            return obj
    raise RuntimeError(f"No class found in module {module_path}")


def discover_machine_contexts(cls) -> List[MachineContext]:
    enum_classes = []
    for _, obj in inspect.getmembers(cls, inspect.isclass):
        if obj is Enum:
            continue
        if issubclass(obj, Enum):
            enum_classes.append(obj)

    if not enum_classes:
        raise AssertionError("No state machine enums discovered")

    getter_methods = []
    probe = cls()
    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if not name.startswith("get") or name.endswith("FullName"):
            continue
        if len(inspect.signature(method).parameters) != 1:
            continue
        try:
            value = getattr(probe, name)()
        except Exception:
            continue
        getter_methods.append((name, value))

    contexts = []
    for enum_cls in sorted(enum_classes, key=lambda e: e.__name__):
        matches = [name for name, value in getter_methods if isinstance(value, enum_cls)]
        if len(matches) != 1:
            raise AssertionError(
                f"Expected exactly one getter for enum {enum_cls.__name__}, found {matches}"
            )

        getter_name = matches[0]
        setter_name = f"set{getter_name[3:]}"
        if not hasattr(cls, setter_name):
            raise AssertionError(f"Missing setter {setter_name} for enum {enum_cls.__name__}")

        contexts.append(MachineContext(enum_cls, getter_name, setter_name))

    return contexts


def discover_event_names(cls, excluded_names) -> List[str]:
    events = []
    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if name.startswith("_"):
            continue
        if name in excluded_names:
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


def extract_machine_model(
    cls,
    context: MachineContext,
    event_names: List[str],
) -> MachineModel:
    states = list(context.enum_cls)
    if not states:
        raise AssertionError("No states discovered")

    index = {state: idx for idx, state in enumerate(states)}
    probe = cls()
    initial_state = getattr(probe, context.getter_name)()
    initial_index = index[initial_state]

    adjacency = [[0 for _ in states] for _ in states]

    for source in states:
        for event in event_names:
            obj = cls()
            getattr(obj, context.setter_name)(source)
            before = getattr(obj, context.getter_name)()
            result = getattr(obj, event)()
            after = getattr(obj, context.getter_name)()

            if not isinstance(result, bool):
                continue
            if result:
                adjacency[index[source]][index[after]] += 1
            elif (not result) and after != before:
                raise AssertionError(
                    f"Event {event} returned False but changed state "
                    f"from {before} to {after}"
                )

    frozen = tuple(tuple(row) for row in adjacency)
    return MachineModel(
        state_count=len(states),
        initial_index=initial_index,
        adjacency=frozen,
    )


def extract_all_machine_models(cls) -> List[MachineModel]:
    contexts = discover_machine_contexts(cls)
    excluded_names = {"__init__", "delete"}
    for context in contexts:
        excluded_names.add(context.getter_name)
        excluded_names.add(context.setter_name)

    event_names = discover_event_names(cls, excluded_names)
    return [extract_machine_model(cls, context, event_names) for context in contexts]


def supported_edges(model: MachineModel) -> Tuple[Tuple[int, ...], ...]:
    return tuple(
        tuple(1 if count > 0 else 0 for count in row) for row in model.adjacency
    )


def isomorphic_up_to_renaming(reference: MachineModel, candidate: MachineModel):
    if reference.state_count != candidate.state_count:
        return False, "State count mismatch"

    reference_edges = supported_edges(reference)
    candidate_edges = supported_edges(candidate)

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
                if reference_edges[i][j] != candidate_edges[mapping[i]][mapping[j]]:
                    matches = False
                    break
            if not matches:
                break
        if matches:
            return True, "ok"

    return False, "No graph isomorphism found with initial-state preservation"


def machine_sets_isomorphic(
    reference_models: List[MachineModel],
    candidate_models: List[MachineModel],
):
    if len(reference_models) != len(candidate_models):
        return (
            False,
            f"State-machine count mismatch: expected {len(reference_models)}, "
            f"got {len(candidate_models)}",
        )

    n = len(reference_models)
    for perm in itertools.permutations(range(n)):
        all_match = True
        for ref_idx, cand_idx in enumerate(perm):
            ok, _ = isomorphic_up_to_renaming(
                reference_models[ref_idx],
                candidate_models[cand_idx],
            )
            if not ok:
                all_match = False
                break
        if all_match:
            return True, "ok"

    return False, "No isomorphic mapping found between state machines"
