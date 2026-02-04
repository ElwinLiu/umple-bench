from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from umple_bench.yaml_min import YamlMinError, load_yaml


class TaskSpecError(ValueError):
    pass


@dataclass(frozen=True)
class TaskSpec:
    id: str
    name: str
    description: str
    timeout_seconds: int
    memory_mb: int
    tags: list[str]
    entrypoint: str


def load_task_spec(task_dir: Path) -> TaskSpec:
    task_yaml = task_dir / "task.yaml"
    try:
        doc = load_yaml(task_yaml)
    except (OSError, YamlMinError) as e:
        raise TaskSpecError(f"Failed to read task spec at {task_yaml}: {e}") from e

    if not isinstance(doc, dict):
        raise TaskSpecError(f"task.yaml must be a YAML mapping: {task_yaml}")

    def require_str(key: str) -> str:
        if key not in doc:
            raise TaskSpecError(f"task.yaml missing required key: {key!r}")
        val = doc[key]
        if not isinstance(val, str):
            raise TaskSpecError(f"task.yaml {key!r} must be a string")
        if not val.strip():
            raise TaskSpecError(f"task.yaml {key!r} must be non-empty")
        return val.strip()

    def require_int(key: str) -> int:
        if key not in doc:
            raise TaskSpecError(f"task.yaml missing required key: {key!r}")
        val = doc[key]
        if isinstance(val, bool) or not isinstance(val, int):
            raise TaskSpecError(f"task.yaml {key!r} must be an integer")
        return val

    task_id = require_str("id")
    name = require_str("name")
    description = require_str("description")
    timeout_seconds = require_int("timeout_seconds")
    memory_mb = require_int("memory_mb")

    tags_raw = doc.get("tags", [])
    if isinstance(tags_raw, str):
        tags = [tags_raw]
    elif isinstance(tags_raw, list) and all(isinstance(x, str) for x in tags_raw):
        tags = list(tags_raw)
    else:
        raise TaskSpecError("task.yaml 'tags' must be a string or list of strings")

    entrypoint = str(doc.get("entrypoint", "run-tests.sh"))
    if not entrypoint.strip():
        entrypoint = "run-tests.sh"

    return TaskSpec(
        id=task_id,
        name=name,
        description=description,
        timeout_seconds=timeout_seconds,
        memory_mb=memory_mb,
        tags=tags,
        entrypoint=entrypoint,
    )

