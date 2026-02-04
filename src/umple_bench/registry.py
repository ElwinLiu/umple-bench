from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from umple_bench.yaml_min import YamlMinError, load_yaml


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class DatasetRef:
    name: str
    version: str
    path: Path


def load_registry(registry_path: Path) -> list[DatasetRef]:
    try:
        doc = load_yaml(registry_path)
    except (OSError, YamlMinError) as e:
        raise RegistryError(f"Failed to read registry at {registry_path}: {e}") from e

    if not isinstance(doc, dict):
        raise RegistryError("Registry must be a YAML mapping with a 'datasets' key.")
    raw = doc.get("datasets")
    if not isinstance(raw, list):
        raise RegistryError("Registry 'datasets' must be a YAML list.")

    out: list[DatasetRef] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise RegistryError(f"Registry datasets[{i}] must be a mapping.")
        for key in ("name", "version", "path"):
            if key not in item:
                raise RegistryError(f"Registry datasets[{i}] missing required key: {key!r}")
        out.append(
            DatasetRef(
                name=str(item["name"]),
                version=str(item["version"]),
                path=Path(str(item["path"])),
            )
        )
    return out


def parse_dataset_spec(spec: str) -> tuple[str, str]:
    if "==" not in spec:
        raise RegistryError("Dataset must be in form: name==version")
    name, version = spec.split("==", 1)
    name = name.strip()
    version = version.strip()
    if not name or not version:
        raise RegistryError("Dataset must be in form: name==version")
    return name, version


def resolve_dataset(registry_path: Path, spec: str) -> DatasetRef:
    name, version = parse_dataset_spec(spec)
    for ds in load_registry(registry_path):
        if ds.name == name and ds.version == version:
            return ds
    raise RegistryError(f"Dataset not found in registry: {name}=={version}")


def iter_task_dirs(dataset_path: Path) -> list[Path]:
    base = dataset_path / "tasks"
    if not base.is_dir():
        base = dataset_path

    if not base.is_dir():
        raise RegistryError(f"Dataset path is not a directory: {dataset_path}")

    tasks: list[Path] = []
    for child in base.iterdir():
        if not child.is_dir():
            continue
        if (child / "task.yaml").is_file():
            tasks.append(child)
    return sorted(tasks)

