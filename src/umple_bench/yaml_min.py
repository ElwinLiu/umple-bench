from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")


class YamlMinError(ValueError):
    pass


def load_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    data, idx = _parse_block(lines, 0, indent=0)
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx != len(lines):
        raise YamlMinError(f"Unexpected trailing content at line {idx + 1}: {lines[idx]!r}")
    return data


def _count_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_comment(line: str) -> str:
    # Minimal: treat '#' as a comment start only when preceded by whitespace.
    if "#" not in line:
        return line
    out = []
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        if ch == "#" and not in_single and not in_double:
            if i == 0 or line[i - 1].isspace():
                break
        out.append(ch)
    return "".join(out)


def _parse_block(lines: list[str], start: int, indent: int) -> tuple[Any, int]:
    result: Any = None
    i = start
    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue

        line = _strip_comment(raw).rstrip()
        if not line.strip():
            i += 1
            continue

        cur_indent = _count_indent(line)
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise YamlMinError(f"Unexpected indentation at line {i + 1}: {raw!r}")

        stripped = line.strip()
        if stripped.startswith("- "):
            if result is None:
                result = []
            if not isinstance(result, list):
                raise YamlMinError(f"Mixed list/dict at line {i + 1}: {raw!r}")

            item_text = stripped[2:].strip()
            if not item_text:
                raise YamlMinError(f"Empty list item at line {i + 1}")

            if ":" in item_text:
                key, val = _split_kv(item_text, i)
                item: dict[str, Any] = {key: _parse_scalar(val)}
                i += 1
                # Parse additional key/value lines indented by +2
                while i < len(lines):
                    nxt_raw = lines[i]
                    if not nxt_raw.strip():
                        i += 1
                        continue
                    nxt_line = _strip_comment(nxt_raw).rstrip()
                    if not nxt_line.strip():
                        i += 1
                        continue
                    nxt_indent = _count_indent(nxt_line)
                    if nxt_indent <= indent:
                        break
                    if nxt_indent != indent + 2:
                        raise YamlMinError(
                            f"Unsupported indentation at line {i + 1} (expected {indent + 2}): {nxt_raw!r}"
                        )
                    k, v = _split_kv(nxt_line.strip(), i)
                    if v == "":
                        nested, j = _parse_block(lines, i + 1, indent=nxt_indent + 2)
                        item[k] = nested
                        i = j
                        continue
                    item[k] = _parse_scalar(v)
                    i += 1
                result.append(item)
                continue

            result.append(_parse_scalar(item_text))
            i += 1
            continue

        # dict entry
        if result is None:
            result = {}
        if not isinstance(result, dict):
            raise YamlMinError(f"Mixed list/dict at line {i + 1}: {raw!r}")

        key, val = _split_kv(stripped, i)
        if val == "":
            nested, j = _parse_block(lines, i + 1, indent=indent + 2)
            result[key] = nested
            i = j
            continue
        result[key] = _parse_scalar(val)
        i += 1

    return result, i


def _split_kv(text: str, i: int) -> tuple[str, str]:
    if ":" not in text:
        raise YamlMinError(f"Expected key: value at line {i + 1}: {text!r}")
    key, val = text.split(":", 1)
    key = key.strip()
    if not key:
        raise YamlMinError(f"Empty key at line {i + 1}: {text!r}")
    return key, val.strip()


def _parse_scalar(val: str) -> Any:
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        items = [x.strip() for x in inner.split(",")]
        return [_parse_scalar(x) for x in items if x]

    if val in ("true", "True"):
        return True
    if val in ("false", "False"):
        return False
    if _INT_RE.match(val):
        try:
            return int(val)
        except ValueError:
            return val
    if _FLOAT_RE.match(val):
        try:
            return float(val)
        except ValueError:
            return val

    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1]

    return val
