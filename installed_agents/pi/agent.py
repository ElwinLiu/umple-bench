from __future__ import annotations

import json
import os
import shlex
from pathlib import Path

from harbor.agents.installed.base import BaseInstalledAgent, ExecInput
from harbor.models.agent.context import AgentContext
from harbor.models.trial.paths import EnvironmentPaths


class PiAgent(BaseInstalledAgent):
    """
    Harbor installed agent that runs the pi CLI inside the task container.
    """

    _PASSTHROUGH_ENV_VARS = (
        # Provider API keys.
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_OAUTH_TOKEN",
        "OPENAI_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "MISTRAL_API_KEY",
        "GROQ_API_KEY",
        "CEREBRAS_API_KEY",
        "XAI_API_KEY",
        "OPENROUTER_API_KEY",
        "AI_GATEWAY_API_KEY",
        "ZAI_API_KEY",
        "OPENCODE_API_KEY",
        "HF_TOKEN",
        "KIMI_API_KEY",
        "MINIMAX_API_KEY",
        "MINIMAX_CN_API_KEY",
        # Azure OpenAI extras.
        "AZURE_OPENAI_BASE_URL",
        "AZURE_OPENAI_RESOURCE_NAME",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT_NAME_MAP",
        # Bedrock auth.
        "AWS_PROFILE",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_BEARER_TOKEN_BEDROCK",
        "AWS_REGION",
        "AWS_ENDPOINT_URL_BEDROCK_RUNTIME",
        "AWS_BEDROCK_SKIP_AUTH",
        "AWS_BEDROCK_FORCE_HTTP1",
        # Optional provider overrides.
        "OPENAI_BASE_URL",
        "ANTHROPIC_BASE_URL",
        "PI_CACHE_RETENTION",
    )

    def __init__(
        self,
        provider: str | None = None,
        no_tools: bool = False,
        tools: str | None = "read,bash,edit,write",
        thinking: str | None = None,
        extra_args: str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._provider = provider
        self._no_tools = no_tools
        self._tools = tools
        self._thinking = thinking
        self._extra_args = extra_args

    @staticmethod
    def name() -> str:
        return "pi"

    @property
    def _install_agent_template_path(self) -> Path:
        return Path(__file__).parent / "install-pi.sh.j2"

    def _build_env(self) -> dict[str, str]:
        env: dict[str, str] = {
            # Keep pi state isolated per-trial and persisted in /logs/agent.
            "PI_CODING_AGENT_DIR": (EnvironmentPaths.agent_dir / "pi-home").as_posix(),
            # Avoid background version-check traffic for deterministic runs.
            "PI_SKIP_VERSION_CHECK": os.environ.get("PI_SKIP_VERSION_CHECK", "1"),
        }

        for key in self._PASSTHROUGH_ENV_VARS:
            value = os.environ.get(key)
            if value:
                env[key] = value

        return env

    @staticmethod
    def _coerce_int(value: object) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return 0
        return 0

    @staticmethod
    def _coerce_float(value: object) -> float:
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    @classmethod
    def _first_int(cls, payload: dict[str, object], *keys: str) -> int:
        for key in keys:
            if key in payload and payload[key] is not None:
                return cls._coerce_int(payload[key])
        return 0

    @classmethod
    def _extract_usage_from_stdout(cls, stdout_path: Path) -> dict[str, float | int] | None:
        lines = stdout_path.read_text(errors="replace").splitlines()

        messages: list[dict[str, object]] | None = None
        for line in reversed(lines):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue

            if not isinstance(payload, dict) or payload.get("type") != "agent_end":
                continue

            raw_messages = payload.get("messages")
            if isinstance(raw_messages, list):
                messages = [item for item in raw_messages if isinstance(item, dict)]
                break

        if not messages:
            return None

        n_input_tokens = 0
        n_output_tokens = 0
        n_cache_tokens = 0
        cost_usd = 0.0
        found_usage = False

        for message in messages:
            if message.get("role") != "assistant":
                continue

            usage = message.get("usage")
            if not isinstance(usage, dict):
                continue

            found_usage = True

            prompt_tokens = cls._first_int(
                usage,
                "input",
                "inputTokens",
                "input_tokens",
                "prompt_tokens",
            )
            cache_tokens = cls._first_int(
                usage,
                "cacheRead",
                "cache_read_tokens",
                "cache_read_input_tokens",
                "cached_tokens",
            )
            output_tokens = cls._first_int(
                usage,
                "output",
                "outputTokens",
                "output_tokens",
                "completion_tokens",
            )

            n_input_tokens += prompt_tokens + cache_tokens
            n_output_tokens += output_tokens
            n_cache_tokens += cache_tokens

            raw_cost = usage.get("cost")
            if isinstance(raw_cost, dict):
                cost_usd += cls._coerce_float(
                    raw_cost.get("total")
                    or raw_cost.get("totalUsd")
                    or raw_cost.get("total_usd")
                )
            else:
                cost_usd += cls._coerce_float(
                    usage.get("costUsd") or usage.get("cost_usd")
                )

        if not found_usage:
            return None

        return {
            "n_input_tokens": n_input_tokens,
            "n_output_tokens": n_output_tokens,
            "n_cache_tokens": n_cache_tokens,
            "cost_usd": cost_usd,
        }

    def create_run_agent_commands(self, instruction: str) -> list[ExecInput]:
        args = [
            "pi",
            "--mode",
            "json",
            "-p",
            "--no-session",
            "--no-extensions",
            "--no-skills",
            "--no-prompt-templates",
            "--no-themes",
        ]

        if self._provider:
            args.extend(["--provider", self._provider])

        if self.model_name:
            args.extend(["--model", self.model_name])

        if self._thinking:
            args.extend(["--thinking", self._thinking])

        if self._no_tools:
            args.append("--no-tools")
        elif self._tools:
            args.extend(["--tools", self._tools])

        if self._extra_args:
            args.extend(shlex.split(self._extra_args))

        args.append(instruction)

        command = (
            "mkdir -p /logs/agent && "
            + shlex.join(args)
            + " 2>&1 </dev/null | tee /logs/agent/pi.txt"
        )

        return [ExecInput(command=command, env=self._build_env())]

    def populate_context_post_run(self, context: AgentContext) -> None:
        command_dir = self.logs_dir / "command-0"

        metadata: dict[str, object] = {
            "provider": self._provider,
            "model_name": self.model_name,
            "no_tools": self._no_tools,
            "tools": self._tools,
            "thinking": self._thinking,
            "extra_args": self._extra_args,
        }

        return_code_path = command_dir / "return-code.txt"
        if return_code_path.exists():
            raw = return_code_path.read_text().strip()
            try:
                metadata["pi_return_code"] = int(raw)
            except ValueError:
                metadata["pi_return_code"] = raw

        stdout_path = command_dir / "stdout.txt"
        if stdout_path.exists():
            metadata["pi_stdout_bytes"] = stdout_path.stat().st_size
            usage = self._extract_usage_from_stdout(stdout_path)
            if usage:
                context.n_input_tokens = int(usage["n_input_tokens"])
                context.n_output_tokens = int(usage["n_output_tokens"])
                context.n_cache_tokens = int(usage["n_cache_tokens"])

                parsed_cost = float(usage["cost_usd"])
                if parsed_cost > 0:
                    context.cost_usd = parsed_cost

                metadata["usage_parsed"] = True
            else:
                metadata["usage_parsed"] = False

        stderr_path = command_dir / "stderr.txt"
        if stderr_path.exists():
            metadata["pi_stderr_bytes"] = stderr_path.stat().st_size

        context.metadata = metadata
