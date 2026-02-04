from __future__ import annotations

import json
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from umple_bench.registry import RegistryError, iter_task_dirs, load_registry, resolve_dataset
from umple_bench.task_spec import TaskSpec, TaskSpecError, load_task_spec


class RunnerError(RuntimeError):
    pass


@dataclass(frozen=True)
class BenchmarkRun:
    run_dir: Path
    run_json_path: Path
    all_passed: bool
    summary_lines: list[str]


@dataclass(frozen=True)
class _ExecResult:
    exit_code: int | None
    duration_ms: int
    timed_out: bool


def run_benchmark(
    *,
    dataset: str | None,
    task_id: str | None,
    model_id: str,
    harness_argv: list[str],
    output_dir: Path | None,
    registry_path: Path,
) -> BenchmarkRun:
    run_dir = _prepare_run_dir(output_dir)
    started_at = datetime.now(timezone.utc).isoformat()

    tasks = _resolve_task_dirs(dataset=dataset, task_id=task_id, registry_path=registry_path)
    if not tasks:
        raise SystemExit("No tasks resolved.")

    task_runs: list[dict[str, Any]] = []
    summary: list[str] = []
    all_passed = True

    for task_dir in tasks:
        spec = load_task_spec(task_dir)
        task_out = run_dir / spec.id
        task_out.mkdir(parents=True, exist_ok=True)

        result = _run_single_task(
            task_dir=task_dir,
            spec=spec,
            task_out=task_out,
            model_id=model_id,
            harness_argv=harness_argv,
        )
        task_runs.append(result["task_run"])
        summary.append(result["summary_line"])
        if not result["passed"]:
            all_passed = False

    run_json = {
        "schema_version": 1,
        "started_at": started_at,
        "model_id": model_id,
        "dataset": dataset,
        "task_id": task_id,
        "harness_cmd": harness_argv,
        "run_dir": str(run_dir),
        "tasks": task_runs,
    }

    run_json_path = run_dir / "run.json"
    run_json_path.write_text(json.dumps(run_json, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return BenchmarkRun(
        run_dir=run_dir,
        run_json_path=run_json_path,
        all_passed=all_passed,
        summary_lines=summary,
    )


def _prepare_run_dir(output_dir: Path | None) -> Path:
    if output_dir is not None:
        out = output_dir
    else:
        stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        out = Path("umple-bench-out") / stamp
    out.mkdir(parents=True, exist_ok=True)
    return out.resolve()


def _resolve_task_dirs(*, dataset: str | None, task_id: str | None, registry_path: Path) -> list[Path]:
    registry_path = registry_path.resolve()

    def abs_dataset_path(ds_path: Path) -> Path:
        return (registry_path.parent / ds_path).resolve() if not ds_path.is_absolute() else ds_path.resolve()

    # dataset + optional task_id
    if dataset:
        ds = resolve_dataset(registry_path, dataset)
        ds_path = abs_dataset_path(ds.path)
        tasks = iter_task_dirs(ds_path)
        if task_id:
            tasks = [t for t in tasks if _task_id_from_dir(t) == task_id]
        return tasks

    # task_id only: search all datasets
    if not task_id:
        return []

    matches: list[Path] = []
    try:
        datasets = load_registry(registry_path)
    except RegistryError as e:
        raise SystemExit(str(e)) from e

    for ds in datasets:
        ds_path = abs_dataset_path(ds.path)
        for tdir in iter_task_dirs(ds_path):
            if _task_id_from_dir(tdir) == task_id:
                matches.append(tdir)
    if len(matches) > 1:
        joined = "\n".join(f"- {m}" for m in matches)
        raise SystemExit(f"Task id {task_id!r} is ambiguous across datasets:\n{joined}")
    return matches


def _task_id_from_dir(task_dir: Path) -> str | None:
    try:
        spec = load_task_spec(task_dir)
    except TaskSpecError:
        return None
    return spec.id


def _run_single_task(
    *,
    task_dir: Path,
    spec: TaskSpec,
    task_out: Path,
    model_id: str,
    harness_argv: list[str],
) -> dict[str, Any]:
    image_tag = _docker_image_tag(spec.id)

    build_stdout = task_out / "docker-build.stdout.txt"
    build_stderr = task_out / "docker-build.stderr.txt"
    _docker_build(task_dir=task_dir, image_tag=image_tag, stdout_path=build_stdout, stderr_path=build_stderr)

    harness_stdout = task_out / "harness.stdout.txt"
    harness_stderr = task_out / "harness.stderr.txt"
    tests_stdout = task_out / "tests.stdout.txt"
    tests_stderr = task_out / "tests.stderr.txt"

    harness = _run_step_in_container(
        step_name="harness",
        image_tag=image_tag,
        task_dir=task_dir,
        task_out=task_out,
        spec=spec,
        model_id=model_id,
        exec_argv=harness_argv,
        stdout_path=harness_stdout,
        stderr_path=harness_stderr,
        extra_env={},
    )

    tests_env = {
        "GENERATION_TIME_MS": str(harness.duration_ms),
        "HARNESS_EXIT_CODE": str(harness.exit_code if harness.exit_code is not None else -1),
        "HARNESS_TIMED_OUT": "1" if harness.timed_out else "0",
        "HARNESS_STDOUT_PATH": "/out/" + harness_stdout.name,
        "HARNESS_STDERR_PATH": "/out/" + harness_stderr.name,
        "TESTS_STDOUT_PATH": "/out/" + tests_stdout.name,
        "TESTS_STDERR_PATH": "/out/" + tests_stderr.name,
    }

    tests = _run_step_in_container(
        step_name="tests",
        image_tag=image_tag,
        task_dir=task_dir,
        task_out=task_out,
        spec=spec,
        model_id=model_id,
        exec_argv=["sh", f"/task/{spec.entrypoint}"],
        stdout_path=tests_stdout,
        stderr_path=tests_stderr,
        extra_env=tests_env,
    )

    results_path = task_out / "results.json"
    if not results_path.is_file():
        _write_fallback_results(
            results_path=results_path,
            task_id=spec.id,
            model_id=model_id,
            generation_time_ms=harness.duration_ms,
            test_time_ms=tests.duration_ms,
            timeout=harness.timed_out or tests.timed_out,
            stdout=str(tests_stdout),
            stderr=str(tests_stderr),
            notes="Missing /out/results.json (tests did not produce results).",
        )

    try:
        results = json.loads(results_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        results = {}

    if isinstance(results, dict):
        _normalize_result_paths(results, task_out=task_out)
        results_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    passed = bool(results.get("num_failed", 1) == 0 and results.get("num_tests", 0) > 0)
    if not passed:
        # Allow tasks with 0 tests to still be considered failures
        pass

    summary_line = _format_summary(
        task_id=spec.id,
        results=results,
        results_path=results_path,
        generation_ms=harness.duration_ms,
        tests_ms=tests.duration_ms,
        timeout=harness.timed_out or tests.timed_out,
    )

    task_run = {
        "task_id": spec.id,
        "task_dir": str(task_dir.resolve()),
        "image_tag": image_tag,
        "outputs_dir": str(task_out),
        "results_path": str(results_path),
        "metadata": {
            "name": spec.name,
            "description": spec.description,
            "timeout_seconds": spec.timeout_seconds,
            "memory_mb": spec.memory_mb,
            "tags": spec.tags,
        },
        "steps": {
            "generation": {
                "duration_ms": harness.duration_ms,
                "timed_out": harness.timed_out,
                "exit_code": harness.exit_code,
                "stdout": str(harness_stdout),
                "stderr": str(harness_stderr),
            },
            "tests": {
                "duration_ms": tests.duration_ms,
                "timed_out": tests.timed_out,
                "exit_code": tests.exit_code,
                "stdout": str(tests_stdout),
                "stderr": str(tests_stderr),
            },
        },
    }

    return {"task_run": task_run, "summary_line": summary_line, "passed": passed}


def _write_fallback_results(
    *,
    results_path: Path,
    task_id: str,
    model_id: str,
    generation_time_ms: int,
    test_time_ms: int,
    timeout: bool,
    stdout: str,
    stderr: str,
    notes: str,
) -> None:
    fallback = {
        "task_id": task_id,
        "model_id": model_id,
        "pass_rate": 0.0,
        "error_rate": 1.0,
        "num_tests": 0,
        "num_passed": 0,
        "num_failed": 0,
        "generation_time_ms": generation_time_ms,
        "test_time_ms": test_time_ms,
        "timeout": bool(timeout),
        "stdout": stdout,
        "stderr": stderr,
        "notes": notes,
    }
    results_path.write_text(json.dumps(fallback, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalize_result_paths(results: dict[str, Any], *, task_out: Path) -> None:
    for key in ("stdout", "stderr"):
        val = results.get(key)
        if not isinstance(val, str):
            continue
        if val.startswith("/out/"):
            results[key] = str(task_out / Path(val).name)


def _format_summary(
    *,
    task_id: str,
    results: dict[str, Any],
    results_path: Path,
    generation_ms: int,
    tests_ms: int,
    timeout: bool,
) -> str:
    num_passed = results.get("num_passed", "?")
    num_tests = results.get("num_tests", "?")
    pass_rate = results.get("pass_rate", "?")
    timeout_mark = " (timeout)" if timeout else ""
    return (
        f"{task_id}: {num_passed}/{num_tests} passed (pass_rate={pass_rate})"
        f" gen={generation_ms}ms test={tests_ms}ms{timeout_mark} -> {results_path}"
    )


def _docker_image_tag(task_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in task_id)
    return f"umple-bench-task:{safe}"


def _docker_build(*, task_dir: Path, image_tag: str, stdout_path: Path, stderr_path: Path) -> None:
    _run_cmd(
        ["docker", "build", "-t", image_tag, str(task_dir.resolve())],
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_s=None,
    )


def _run_step_in_container(
    *,
    step_name: str,
    image_tag: str,
    task_dir: Path,
    task_out: Path,
    spec: TaskSpec,
    model_id: str,
    exec_argv: list[str],
    stdout_path: Path,
    stderr_path: Path,
    extra_env: dict[str, str],
) -> _ExecResult:
    container_name = f"umple-bench-{spec.id}-{uuid.uuid4().hex[:10]}"

    task_dir_abs = task_dir.resolve()
    out_abs = task_out.resolve()

    env = {
        "MODEL_ID": model_id,
        "TASK_ID": spec.id,
        "TASK_DIR": "/task",
        "OUT_DIR": "/out",
        "REQ_PATH": "/task/req.md",
        "PROMPT_PATH": "/task/prompt.md",
        "SUBMISSION_PATH": "/out/submission.ump",
    }
    env.update(extra_env)

    docker_run = [
        "docker",
        "run",
        "-d",
        "--rm",
        "--name",
        container_name,
        "--memory",
        f"{spec.memory_mb}m",
        "--memory-swap",
        f"{spec.memory_mb}m",
        "--mount",
        f"type=bind,src={task_dir_abs},dst=/task,readonly",
        "--mount",
        f"type=bind,src={out_abs},dst=/out",
    ]
    for k, v in env.items():
        docker_run.extend(["-e", f"{k}={v}"])
    docker_run.extend([image_tag, "sh", "-lc", "sleep infinity"])

    _run_cmd(
        docker_run,
        stdout_path=task_out / f"docker-run.{step_name}.stdout.txt",
        stderr_path=task_out / f"docker-run.{step_name}.stderr.txt",
        timeout_s=None,
    )

    start = time.monotonic()
    timed_out = False
    exit_code: int | None = None
    try:
        _run_cmd(
            ["docker", "exec", "-w", "/out", container_name, *exec_argv],
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timeout_s=spec.timeout_seconds,
        )
        exit_code = 0
    except subprocess.TimeoutExpired:
        timed_out = True
    except RunnerError as e:
        # Non-zero exit is not fatal for the runner; record it and continue.
        exit_code = getattr(e, "exit_code", 1)
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        _best_effort(["docker", "kill", container_name])

    if exit_code is None and timed_out:
        exit_code = None

    return _ExecResult(exit_code=exit_code, duration_ms=duration_ms, timed_out=timed_out)


def _run_cmd(
    argv: list[str],
    *,
    stdout_path: Path,
    stderr_path: Path,
    timeout_s: int | None,
) -> None:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        try:
            proc = subprocess.run(argv, stdout=out, stderr=err, timeout=timeout_s, check=False)
        except FileNotFoundError as e:
            raise RunnerError(f"Command not found: {argv[0]!r}") from e

    if proc.returncode != 0:
        exc = RunnerError(f"Command failed ({proc.returncode}): {' '.join(argv)}")
        setattr(exc, "exit_code", proc.returncode)
        raise exc


def _best_effort(argv: list[str]) -> None:
    try:
        subprocess.run(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except FileNotFoundError:
        pass
