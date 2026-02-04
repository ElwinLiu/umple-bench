from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any


TRANSITION_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*->\s*([A-Za-z_]\w*)\s*;\s*$")


def main() -> None:
    started = time.monotonic()

    out_dir = Path(os.environ.get("OUT_DIR", "/out"))
    submission_path = Path(os.environ.get("SUBMISSION_PATH", str(out_dir / "submission.ump")))
    spec_path = Path(__file__).with_name("spec.json")
    results_path = out_dir / "results.json"

    task_id = os.environ.get("TASK_ID", "unknown-task")
    model_id = os.environ.get("MODEL_ID", "unknown")
    generation_time_ms = _parse_int(os.environ.get("GENERATION_TIME_MS", "0"), default=0)
    harness_timed_out = os.environ.get("HARNESS_TIMED_OUT", "0") == "1"

    stdout_path = os.environ.get("TESTS_STDOUT_PATH", "/out/tests.stdout.txt")
    stderr_path = os.environ.get("TESTS_STDERR_PATH", "/out/tests.stderr.txt")

    failures: list[str] = []
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except Exception as e:
        failures.append(f"Failed to read spec.json: {e}")
        spec = {}

    required_class = str(spec.get("required_class", "")).strip()
    required_states = list(spec.get("required_states", []))
    required_transitions = list(spec.get("required_transitions", []))

    text = ""
    if not submission_path.is_file():
        failures.append(f"Missing submission file: {submission_path}")
    else:
        text = submission_path.read_text(encoding="utf-8", errors="replace")

    num_tests = 0

    num_tests += 1
    if required_class and f"class {required_class}" not in text:
        failures.append(f"Missing class declaration: class {required_class}")

    num_tests += 1
    if "stateMachine" not in text:
        failures.append("Missing 'stateMachine' block")

    state_blocks = _parse_state_blocks(text, failures)

    for state in required_states:
        num_tests += 1
        if state not in state_blocks:
            failures.append(f"Missing state: {state}")

    transitions_by_state = {st: _parse_transitions(block) for st, block in state_blocks.items()}

    for t in required_transitions:
        num_tests += 1
        src = str(t.get("from", ""))
        event = str(t.get("event", ""))
        dst = str(t.get("to", ""))
        if not src or not event or not dst:
            failures.append(f"Malformed required transition entry: {t!r}")
            continue
        if src not in transitions_by_state:
            failures.append(f"Missing transition source state: {src}")
            continue
        if (event, dst) not in transitions_by_state[src]:
            failures.append(f"Missing transition: {src}: {event} -> {dst};")

    num_failed = len(failures)
    num_passed = max(0, num_tests - num_failed)
    pass_rate = float(num_passed) / float(num_tests) if num_tests else 0.0
    error_rate = float(num_failed) / float(num_tests) if num_tests else 1.0

    test_time_ms = int((time.monotonic() - started) * 1000)

    results: dict[str, Any] = {
        "task_id": task_id,
        "model_id": model_id,
        "pass_rate": pass_rate,
        "error_rate": error_rate,
        "num_tests": num_tests,
        "num_passed": num_passed,
        "num_failed": num_failed,
        "generation_time_ms": generation_time_ms,
        "test_time_ms": test_time_ms,
        "timeout": bool(harness_timed_out),
        "stdout": stdout_path,
        "stderr": stderr_path,
    }

    usage_path = out_dir / "usage.json"
    if usage_path.is_file():
        try:
            results["cost"] = json.loads(usage_path.read_text(encoding="utf-8"))
        except Exception:
            results["cost"] = {"usage_json": str(usage_path)}

    if failures:
        results["notes"] = {"failures": failures}

    results_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_int(s: str, *, default: int) -> int:
    try:
        return int(s)
    except Exception:
        return default


def _parse_state_blocks(text: str, failures: list[str]) -> dict[str, str]:
    idx = text.find("stateMachine")
    if idx == -1:
        return {}

    brace_start = text.find("{", idx)
    if brace_start == -1:
        failures.append("Malformed 'stateMachine' (missing '{')")
        return {}

    content, ok = _extract_brace_content(text, brace_start)
    if not ok:
        failures.append("Malformed 'stateMachine' (unbalanced braces)")
        return {}

    return _parse_top_level_named_blocks(content)


def _extract_brace_content(text: str, open_brace_index: int) -> tuple[str, bool]:
    depth = 0
    start = open_brace_index + 1
    for i in range(open_brace_index, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i], True
    return "", False


def _parse_top_level_named_blocks(content: str) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    n = len(content)
    while i < n:
        while i < n and content[i].isspace():
            i += 1
        if i >= n:
            break
        if not (content[i].isalpha() or content[i] == "_"):
            i += 1
            continue
        j = i + 1
        while j < n and (content[j].isalnum() or content[j] == "_"):
            j += 1
        name = content[i:j]
        k = j
        while k < n and content[k].isspace():
            k += 1
        if k >= n or content[k] != "{":
            i = j
            continue
        block, ok = _extract_brace_content(content, k)
        if not ok:
            break
        out[name] = block
        i = k + 1 + len(block) + 1
    return out


def _parse_transitions(state_block: str) -> set[tuple[str, str]]:
    transitions: set[tuple[str, str]] = set()
    for line in state_block.splitlines():
        m = TRANSITION_RE.match(line)
        if not m:
            continue
        event, dst = m.group(1), m.group(2)
        transitions.add((event, dst))
    return transitions


if __name__ == "__main__":
    main()
