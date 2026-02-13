from __future__ import annotations

import asyncio
import re
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.utils.templating import render_prompt_template


@dataclass
class _SubprocessResult:
    return_code: int
    stdout: str
    stderr: str


class PiAgent(BaseAgent):
    """
    Task-agnostic external Harbor agent that:
    1) calls local `pi` on the host,
    2) extracts bash script output,
    3) executes it once in the task container.

    Note: retry/attempt policy should be controlled by Harbor job-level n_attempts,
    not by internal agent loops, for fair comparisons with built-in agents.
    """

    _FALLBACK_PROMPT_TEMPLATE = """You are generating a bash script that will run INSIDE a Linux container.
Return ONLY bash commands (no markdown fences, no commentary).
The script must be complete and directly executable via bash -lc.
Follow the task instruction literally and exactly.
Do NOT add wrappers/classes/files unless explicitly requested.
If exact filenames/syntax are requested, use them exactly.
If writing files, use cat <<'EOF' redirection.

TASK INSTRUCTION:
{instruction}
"""

    def __init__(
        self,
        logs_dir: Path,
        model_name: str | None = None,
        pi_command: str = "pi",
        prompt_template_path: str | Path | None = None,
        no_tools: bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(logs_dir=logs_dir, model_name=model_name, *args, **kwargs)
        self._pi_command = pi_command
        self._no_tools = no_tools
        self._pi_available = False

        explicit_template_path = Path(prompt_template_path) if prompt_template_path else None
        default_template_path = self._default_prompt_template_path()
        self._prompt_template_path = explicit_template_path or (
            default_template_path if default_template_path.exists() else None
        )

    @staticmethod
    def name() -> str:
        return "pi"

    def version(self) -> str | None:
        return "2.0.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        # External agent: pi runs on host.
        self._pi_available = shutil.which(self._pi_command) is not None
        if not self._pi_available:
            raise RuntimeError(f"pi CLI not found on host: {self._pi_command}")

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        prompt = self._render_instruction(instruction)
        planner = await self._run_pi_prompt(prompt)

        command_0_dir = self.logs_dir / "command-0"
        command_0_dir.mkdir(parents=True, exist_ok=True)
        (command_0_dir / "prompt.txt").write_text(prompt)
        (command_0_dir / "command.txt").write_text(self._pi_command_preview(prompt))
        (command_0_dir / "return-code.txt").write_text(str(planner.return_code))
        (command_0_dir / "stdout.txt").write_text(planner.stdout)
        (command_0_dir / "stderr.txt").write_text(planner.stderr)

        script = self._extract_script(planner.stdout)
        (command_0_dir / "script.sh").write_text(script)

        exec_return_code: int | None = None
        exec_stdout = ""
        exec_stderr = ""

        if script.strip():
            command_1_dir = self.logs_dir / "command-1"
            command_1_dir.mkdir(parents=True, exist_ok=True)

            script_to_run = "set -euo pipefail\n\n" + script.strip() + "\n"
            (command_1_dir / "command.txt").write_text(script_to_run)

            exec_result = await environment.exec(command=script_to_run)
            exec_return_code = exec_result.return_code
            exec_stdout = exec_result.stdout or ""
            exec_stderr = exec_result.stderr or ""

            (command_1_dir / "return-code.txt").write_text(str(exec_return_code))
            (command_1_dir / "stdout.txt").write_text(exec_stdout)
            (command_1_dir / "stderr.txt").write_text(exec_stderr)

        context.metadata = {
            "pi_command": self._pi_command,
            "model_name": self.model_name,
            "prompt_template_path": (
                str(self._prompt_template_path) if self._prompt_template_path else None
            ),
            "prompt_template_source": (
                "file" if self._prompt_template_path else "fallback"
            ),
            "no_tools": self._no_tools,
            "pi_return_code": planner.return_code,
            "pi_stdout_length": len(planner.stdout),
            "pi_stderr_length": len(planner.stderr),
            "script_generated": bool(script.strip()),
            "script_length": len(script),
            "exec_return_code": exec_return_code,
            "exec_stdout_length": len(exec_stdout),
            "exec_stderr_length": len(exec_stderr),
        }

    def _default_prompt_template_path(self) -> Path:
        return (
            Path(__file__).resolve().parents[2]
            / "prompts/agents/base/task_script_prompt.txt"
        )

    def _render_instruction(self, instruction: str) -> str:
        if self._prompt_template_path:
            return render_prompt_template(
                template_path=self._prompt_template_path,
                instruction=instruction,
            )

        return self._FALLBACK_PROMPT_TEMPLATE.format(instruction=instruction)

    def _pi_command_preview(self, prompt: str) -> str:
        command = [
            self._pi_command,
            "-p",
            "--no-session",
            "--no-extensions",
            "--no-skills",
            "--no-prompt-templates",
            "--no-themes",
        ]
        if self._no_tools:
            command.append("--no-tools")
        if self.model_name:
            command.extend(["--model", self.model_name])
        command.append(prompt)
        return shlex.join(command)

    async def _run_pi_prompt(self, prompt: str) -> _SubprocessResult:
        command = [
            self._pi_command,
            "-p",
            "--no-session",
            "--no-extensions",
            "--no-skills",
            "--no-prompt-templates",
            "--no-themes",
        ]

        if self._no_tools:
            command.append("--no-tools")

        if self.model_name:
            command.extend(["--model", self.model_name])

        command.append(prompt)

        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await process.communicate()

        return _SubprocessResult(
            return_code=process.returncode if process.returncode is not None else 0,
            stdout=stdout_b.decode(errors="replace") if stdout_b else "",
            stderr=stderr_b.decode(errors="replace") if stderr_b else "",
        )

    def _extract_script(self, text: str) -> str:
        if not text:
            return ""

        stripped = text.strip()

        fence_match = re.search(
            r"```(?P<lang>[a-zA-Z0-9_-]*)[ \t]*\r?\n(?P<body>.*?)```",
            stripped,
            flags=re.DOTALL,
        )
        if fence_match:
            language = fence_match.group("lang").lower()
            if language in {"", "bash", "sh", "shell", "zsh"}:
                return fence_match.group("body").strip()
            # Non-shell fenced output (e.g., ```python / ```ump) is not executable.
            return ""

        # If output still contains markdown fences but no parsable shell block, skip execution.
        if "```" in stripped:
            return ""

        return stripped
