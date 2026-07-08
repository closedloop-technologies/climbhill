#!/usr/bin/env python3
"""Run one prompt across API-backed deep research providers in parallel."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import secrets
import shlex
import string
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmark.live_smoke import REQUIRED_ENV_BY_SKILL
from benchmark.utils import discover_skills, get_skill_command_info


DEFAULT_API_PROVIDERS = [
    "deep-research-gemini",
    "deep-research-perplexity",
    "deep-research-you",
    "deep-research-tavily",
    "deep-research-jina",
    "deep-research-exa",
    "deep-research-openai",
    "deep-research-xai-grok",
]


@dataclass
class ProviderRun:
    provider: str
    command: List[str]
    response_file: str
    stderr_file: str
    returncode: int
    duration_seconds: float
    skipped: bool = False
    error: str | None = None


def random_suffix(length: int = 4) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_run_dir(base_dir: Path) -> Path:
    folder_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{random_suffix()}"
    run_dir = base_dir / folder_name
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def read_prompt(prompt_arg: str | None) -> str:
    if prompt_arg:
        return prompt_arg
    if not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
        if prompt:
            return prompt
    raise SystemExit("Provide a prompt argument or pipe prompt text on stdin.")


def discover_skill_map() -> Dict[str, Mapping[str, str]]:
    skills: Dict[str, Mapping[str, str]] = {}
    for skill in discover_skills():
        skills.setdefault(skill["name"], skill)
    return skills


def missing_env(provider: str) -> List[str]:
    return [name for name in REQUIRED_ENV_BY_SKILL.get(provider, []) if not os.getenv(name)]


def command_for_provider(provider: str, prompt: str, skills: Mapping[str, Mapping[str, str]]) -> List[str]:
    if provider not in skills:
        raise KeyError(f"{provider}: skill not discovered")

    cmd_info = get_skill_command_info(provider)
    if cmd_info.get("requires_server"):
        raise RuntimeError(f"{provider}: requires an external server")

    command = cmd_info["command"].format(
        script=shlex.quote(str(skills[provider]["script_path"])),
        question=shlex.quote(prompt),
        question_slug="prompt",
        category_slug="fanout",
        skill_name=provider,
        output_dir=".",
    )
    argv = shlex.split(command)
    if argv and argv[0] == "python":
        argv[0] = sys.executable

    # Keep OpenAI fan-out runs on the lowest available effort tier.
    if provider == "deep-research-openai" and "--effort" not in argv:
        argv.extend(["--effort", "low"])

    return argv


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def run_provider(provider: str, argv: Sequence[str], run_dir: Path, timeout: int) -> ProviderRun:
    started = datetime.now()
    response_path = run_dir / f"{provider}.response.txt"
    stderr_path = run_dir / f"{provider}.stderr.txt"
    try:
        result = subprocess.run(
            list(argv),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        write_text(response_path, result.stdout)
        write_text(stderr_path, result.stderr)
        error = None if result.returncode == 0 else f"exit code {result.returncode}"
        return ProviderRun(
            provider=provider,
            command=list(argv),
            response_file=str(response_path.relative_to(run_dir)),
            stderr_file=str(stderr_path.relative_to(run_dir)),
            returncode=result.returncode,
            duration_seconds=(datetime.now() - started).total_seconds(),
            error=error,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        write_text(response_path, stdout)
        write_text(stderr_path, stderr)
        return ProviderRun(
            provider=provider,
            command=list(argv),
            response_file=str(response_path.relative_to(run_dir)),
            stderr_file=str(stderr_path.relative_to(run_dir)),
            returncode=124,
            duration_seconds=(datetime.now() - started).total_seconds(),
            error=f"timeout after {timeout}s",
        )


def write_summary(run_dir: Path, prompt: str, results: Iterable[ProviderRun]) -> None:
    payload = {
        "prompt": prompt,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "results": [asdict(result) for result in results],
    }
    (run_dir / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_providers(values: Sequence[str] | None) -> List[str]:
    if not values:
        return list(DEFAULT_API_PROVIDERS)
    providers: List[str] = []
    for value in values:
        providers.extend(part.strip() for part in value.split(",") if part.strip())
    duplicates = sorted(
        provider for provider in set(providers) if providers.count(provider) > 1
    )
    if duplicates:
        raise ValueError(f"duplicate providers: {', '.join(duplicates)}")
    return providers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?", help="Prompt to send to each provider. Omit to read stdin.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Base directory for the timestamped output folder. Defaults to the current directory.",
    )
    parser.add_argument(
        "--providers",
        action="append",
        default=None,
        help="Comma-separated provider skill names to run. Can be repeated. Defaults to API-backed providers.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Per-provider timeout in seconds.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Maximum parallel provider calls. Defaults to the number of selected providers.",
    )
    parser.add_argument(
        "--fail-missing-env",
        action="store_true",
        help="Fail instead of skipping providers with missing required environment variables.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    prompt = read_prompt(args.prompt)
    run_dir = create_run_dir(args.output_dir)
    skills = discover_skill_map()
    providers = parse_providers(args.providers)

    ready: Dict[str, List[str]] = {}
    results: List[ProviderRun] = []

    for provider in providers:
        missing = missing_env(provider)
        if missing:
            message = f"missing environment variables: {', '.join(missing)}"
            if args.fail_missing_env:
                raise SystemExit(f"{provider}: {message}")
            response_path = run_dir / f"{provider}.response.txt"
            stderr_path = run_dir / f"{provider}.stderr.txt"
            write_text(response_path, "")
            write_text(stderr_path, message + "\n")
            results.append(
                ProviderRun(
                    provider=provider,
                    command=[],
                    response_file=str(response_path.relative_to(run_dir)),
                    stderr_file=str(stderr_path.relative_to(run_dir)),
                    returncode=0,
                    duration_seconds=0.0,
                    skipped=True,
                    error=message,
                )
            )
            continue

        try:
            ready[provider] = command_for_provider(provider, prompt, skills)
        except (KeyError, RuntimeError) as exc:
            response_path = run_dir / f"{provider}.response.txt"
            stderr_path = run_dir / f"{provider}.stderr.txt"
            write_text(response_path, "")
            write_text(stderr_path, f"{exc}\n")
            results.append(
                ProviderRun(
                    provider=provider,
                    command=[],
                    response_file=str(response_path.relative_to(run_dir)),
                    stderr_file=str(stderr_path.relative_to(run_dir)),
                    returncode=0,
                    duration_seconds=0.0,
                    skipped=True,
                    error=str(exc),
                )
            )

    max_workers = args.max_workers or max(1, len(ready))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_provider = {
            executor.submit(run_provider, provider, argv, run_dir, args.timeout): provider
            for provider, argv in ready.items()
        }
        for future in concurrent.futures.as_completed(future_to_provider):
            results.append(future.result())

    results.sort(key=lambda result: result.provider)
    write_summary(run_dir, prompt, results)
    print(run_dir)

    return 1 if any(not result.skipped and result.returncode != 0 for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
