from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from umple_bench.runner import run_benchmark


@dataclass(frozen=True)
class RunArgs:
    dataset: str | None
    task_id: str | None
    model_id: str
    output_dir: Path | None
    registry_path: Path
    harness_argv: list[str]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="umple-bench")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run benchmark task(s)")
    run.add_argument("--dataset", help="Dataset selector: name==version")
    run.add_argument("--task-id", help="Run a single task id (optionally within --dataset)")
    run.add_argument("--model", dest="model_id", default="unknown", help="Model identifier (passed through)")
    run.add_argument("--output-dir", type=Path, default=None, help="Output directory")
    run.add_argument(
        "--registry",
        type=Path,
        default=Path("datasets/registry.yaml"),
        help="Dataset registry file",
    )
    run.add_argument(
        "--harness-cmd",
        metavar="-- <argv...>",
        help="Harness argv list (must be last): --harness-cmd -- <argv...>",
    )
    return parser


def _split_harness_cmd(argv: list[str]) -> tuple[list[str], list[str]]:
    try:
        idx = argv.index("--harness-cmd")
    except ValueError:
        raise SystemExit("Missing required flag: --harness-cmd -- <argv...>")

    if idx + 1 >= len(argv) or argv[idx + 1] != "--":
        raise SystemExit("Expected: --harness-cmd -- <argv...>")

    harness_argv = argv[idx + 2 :]
    if not harness_argv:
        raise SystemExit("Expected at least 1 argument after: --harness-cmd --")

    return argv[:idx], harness_argv


def _parse_run(argv: list[str]) -> RunArgs:
    if "--harness-cmd" not in argv:
        if "-h" in argv or "--help" in argv:
            _build_parser().parse_args(argv)
        raise SystemExit("Missing required flag: --harness-cmd -- <argv...>")

    argv_no_harness, harness_argv = _split_harness_cmd(argv)

    ns = _build_parser().parse_args(argv_no_harness)
    if ns.cmd != "run":
        raise SystemExit(f"Unknown command: {ns.cmd}")

    if not ns.dataset and not ns.task_id:
        raise SystemExit("Provide either --dataset <name==version> or --task-id <id>.")

    return RunArgs(
        dataset=ns.dataset,
        task_id=ns.task_id,
        model_id=ns.model_id,
        output_dir=ns.output_dir,
        registry_path=ns.registry,
        harness_argv=harness_argv,
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    run_args = _parse_run(argv)

    run = run_benchmark(
        dataset=run_args.dataset,
        task_id=run_args.task_id,
        model_id=run_args.model_id,
        harness_argv=run_args.harness_argv,
        output_dir=run_args.output_dir,
        registry_path=run_args.registry_path,
    )

    for line in run.summary_lines:
        print(line)

    print(f"\nWrote: {run.run_json_path}")

    return 0 if run.all_passed else 1
