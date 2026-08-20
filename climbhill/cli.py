from __future__ import annotations

import argparse
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import unquote

from .preparedness import initialize_repo, inspect_preparedness
from .policy import check_paths, load_policy, paths_from_patch, policy_allows_promotion
from .registry import Registry
from .reports import generate_markdown_report
from .resources import add_resource, search_resources

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / ".agents" / "skills"
PROMPT_FILE = REPO_ROOT / "docs" / "taxonomy-and-examples.md"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs"
DEFAULT_REGISTRY = Path(".climbhill") / "registry.local.sqlite"
ENCODED_PATH_SEPARATOR_RE = re.compile(r"%2f|%5c", re.IGNORECASE)
MALFORMED_PERCENT_ENCODING_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")


@dataclass
class PromptExample:
    identifier: str
    category: str
    text: str


@dataclass
class SkillInfo:
    name: str
    path: Path
    source: str
    runnable: bool


SKILL_ROOTS = [
    ("agents", REPO_ROOT / ".agents" / "skills"),
    ("plugin", REPO_ROOT / "skills"),
]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "prompt"


def load_skill_infos(include_documentation: bool = True) -> Dict[str, SkillInfo]:
    skills: Dict[str, SkillInfo] = {}
    for source, root in SKILL_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.iterdir()):
            if not path.is_dir():
                continue
            scripts_dir = path / "scripts"
            runnable = scripts_dir.exists() and any(scripts_dir.glob("*.py"))
            if not include_documentation and not runnable:
                continue
            existing = skills.get(path.name)
            if existing and existing.runnable:
                continue
            skills[path.name] = SkillInfo(
                name=path.name,
                path=path,
                source=source,
                runnable=runnable,
            )
    return skills


def load_skills() -> Dict[str, Path]:
    return {name: info.path for name, info in load_skill_infos(include_documentation=False).items()}


def parse_skill_description(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ""

    description = ""
    inside_front_matter = False
    try:
        for raw_line in skill_md.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line == "---":
                if not inside_front_matter:
                    inside_front_matter = True
                    continue
                break
            if inside_front_matter and line.lower().startswith("description:"):
                description = line.split(":", 1)[1].strip()
                break
    except UnicodeDecodeError:
        return ""
    return description


def list_skills_command(_: argparse.Namespace) -> int:
    skills = load_skill_infos(include_documentation=True)
    if not skills:
        print("No skills found under .agents/skills/ or skills/", file=sys.stderr)
        return 1

    for name, skill in sorted(skills.items()):
        description = parse_skill_description(skill.path)
        runnable = "runnable" if skill.runnable else "docs"
        if description:
            print(f"{name}\t{skill.source}\t{runnable}\t{description}")
        else:
            print(f"{name}\t{skill.source}\t{runnable}")
    return 0


def load_prompt_examples() -> List[PromptExample]:
    if not PROMPT_FILE.exists():
        return []

    examples: List[PromptExample] = []
    counters: Dict[str, int] = {}
    current_category: Optional[str] = None
    current_slug: Optional[str] = None
    in_examples_section = False

    content = PROMPT_FILE.read_text(encoding="utf-8")
    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line == "---":
            if not in_examples_section:
                continue
            # Ignore horizontal rules once inside the section
            continue

        if not in_examples_section:
            if line.startswith("##") and "Canonical" in line:
                in_examples_section = True
            continue

        if line.startswith("##") and not line.startswith("###") and "Canonical" not in line:
            # Exiting the examples section
            break

        if line.startswith("###"):
            heading = line.lstrip("#").strip()
            heading = heading.replace("**", "").strip()
            heading = re.sub(r"^\d+(\.\d+)*\s*", "", heading)
            current_category = heading
            current_slug = slugify(heading)
            continue

        if not current_category or not current_slug:
            continue

        bullet_match = re.match(r"^[-*+]\s*(.+)", line)
        if bullet_match:
            prompt_text = bullet_match.group(1).strip()
            prompt_text = prompt_text.strip('"“”')
            if not prompt_text:
                continue
            count = counters.get(current_slug, 0) + 1
            counters[current_slug] = count
            identifier = f"{current_slug}-{count:02d}"
            examples.append(
                PromptExample(identifier=identifier, category=current_category, text=prompt_text)
            )

    return examples


def list_prompts_command(_: argparse.Namespace) -> int:
    prompts = load_prompt_examples()
    if not prompts:
        print(
            "No prompt examples were found. Ensure docs/taxonomy-and-examples.md is present.",
            file=sys.stderr,
        )
        return 1

    for prompt in prompts:
        print(f"{prompt.identifier}\t[{prompt.category}] {prompt.text}")
    return 0


def resolve_prompt_text(prompt_id: Optional[str], prompt_text: Optional[str]) -> PromptExample:
    if prompt_text is not None:
        if not prompt_text.strip():
            raise ValueError("--prompt-text must be a non-empty string.")
        return PromptExample(identifier="custom", category="Custom", text=prompt_text.strip())

    if not prompt_id:
        raise ValueError("Either --prompt-id or --prompt-text must be provided.")

    prompts = {example.identifier: example for example in load_prompt_examples()}
    if prompt_id not in prompts:
        raise KeyError(f"Prompt id '{prompt_id}' was not found in docs/taxonomy-and-examples.md.")
    return prompts[prompt_id]


def gather_skill_scripts(skill_dir: Path) -> Iterable[str]:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return []
    return [str(path.relative_to(REPO_ROOT)) for path in sorted(scripts_dir.glob("*.py"))]


def build_system_prompt(skill_name: str, skill_dir: Path) -> str:
    description = parse_skill_description(skill_dir)
    scripts = list(gather_skill_scripts(skill_dir))
    scripts_section = "\n".join(f"- {script}" for script in scripts) if scripts else "(no scripts directory found)"

    requirements_path = skill_dir / "requirements.txt"
    requirements_line = (
        f"requirements: {requirements_path.relative_to(REPO_ROOT)}"
        if requirements_path.exists()
        else "requirements: (none provided)"
    )

    system_prompt = textwrap.dedent(
        f"""
        You are running inside the ClimbHill.ai headless CLI.
        Skill: {skill_name}
        Description: {description or 'No description available.'}
        Skill path: {skill_dir.relative_to(REPO_ROOT)}
        {requirements_line}

        Accessible helper scripts:
        {scripts_section}

        Always rely on the selected skill's tooling for external research calls.
        Verify that required environment variables and dependencies are available before execution.
        If something is missing, stop and report precise remediation steps.
        Provide outputs with clear inline citations and a final reference list.
        """
    ).strip()

    return system_prompt


def build_user_prompt(prompt: PromptExample, extra: Optional[str]) -> str:
    extra_section = f"\n\n## Additional Instructions\n{extra.strip()}" if extra else ""

    return textwrap.dedent(
        f"""
        # Research Brief

        ## Category
        {prompt.category}

        ## Core Task
        {prompt.text}
        {extra_section}

        ## Deliverable
        Produce a concise but thorough Markdown report including:
        - Executive summary (2-3 paragraphs).
        - Key findings as bulleted insights with inline citations.
        - Risks, uncertainties, or open questions.
        - Recommended next steps for a human researcher.
        - Reference list with full source URLs.

        Confirm how the selected skill was used. If the task cannot be completed, explain why and propose alternatives.
        """
    ).strip()


def ensure_output_dir(path: Optional[str]) -> Path:
    if path is not None:
        if not path.strip():
            raise ValueError("--output-dir must be a non-empty path.")
        if path != path.strip():
            raise ValueError("--output-dir must be trimmed.")
        if MALFORMED_PERCENT_ENCODING_RE.search(path):
            raise ValueError("--output-dir must not contain malformed percent encoding.")
        if ENCODED_PATH_SEPARATOR_RE.search(path):
            raise ValueError("--output-dir must not encode path separators.")
        decoded_path = unquote(path)
        if decoded_path != path:
            raise ValueError("--output-dir must not contain percent-encoded aliases.")
        if "\\" in path:
            raise ValueError("--output-dir must use forward slashes.")
        if any(ord(character) < 32 or ord(character) == 127 for character in path):
            raise ValueError("--output-dir must not contain control characters.")
        if any(part in {".", ".."} for part in path.split("/")):
            raise ValueError("--output-dir must not contain dot path segments.")
        requested_dir = Path(path)
        output_dir = requested_dir if requested_dir.is_absolute() else REPO_ROOT / requested_dir
    else:
        output_dir = DEFAULT_OUTPUT_DIR
    output_dir = output_dir.resolve()
    try:
        output_dir.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("--output-dir must stay within the repository root.") from exc
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("--output-dir must be a directory.")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def next_output_path(output_dir: Path, skill_name: str) -> Path:
    if not isinstance(skill_name, str) or not skill_name.strip():
        raise ValueError("skill_name must be a non-empty string.")
    token = re.sub(r"[^A-Z0-9]+", "-", skill_name.upper())
    token = token.strip("-")
    if not token:
        raise ValueError("skill_name must contain at least one letter or number.")
    pattern = re.compile(rf"OUTPUT-{re.escape(token)}-(\d+)\.md$")
    max_index = 0
    for existing in output_dir.glob(f"OUTPUT-{token}-*.md"):
        match = pattern.match(existing.name)
        if match:
            max_index = max(max_index, int(match.group(1)))
    next_index = max_index + 1
    return output_dir / f"OUTPUT-{token}-{next_index:04d}.md"


def registry_path(repo_path: Path, requested: Optional[str]) -> Path:
    if requested:
        path = Path(requested)
        return path if path.is_absolute() else repo_path / path
    return repo_path / DEFAULT_REGISTRY


def current_commit(repo_path: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def init_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    created = initialize_repo(repo_path, force=args.force)
    database = registry_path(repo_path, args.registry)
    registry = Registry(database)
    registry.close()

    print(f"Initialized ClimbHill repository support in {repo_path}")
    print(f"Registry: {database}")
    if created:
        print("Created or updated:")
        for path in created:
            print(f"- {path.relative_to(repo_path)}")
    else:
        print("No files were created; existing repository support files were preserved.")
    return 0


def prepare_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    before = inspect_preparedness(repo_path)
    if not before.missing:
        print("Repository support files are present.")
        return 0
    if args.apply:
        created = initialize_repo(repo_path, force=False)
        print("Created missing repository support files:")
        for path in created:
            print(f"- {path.relative_to(repo_path)}")
        return 0
    print(f"Repository: {before.repo_path}")
    print(f"Remote: {before.git_remote or 'unknown'}")
    print(f"Current commit: {before.current_commit or 'unknown'}")
    print("Missing repository support files:")
    for relative in before.missing:
        print(f"- {relative}")
    print("\nRun with --apply to create conservative defaults without overwriting existing files.")
    return 2


def policy_check_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    policy = load_policy(repo_path / ".climbhill" / "policy.yaml")
    paths = list(args.paths or [])
    if args.patch_file:
        patch_path = Path(args.patch_file)
        if not patch_path.is_absolute():
            patch_path = repo_path / patch_path
        paths.extend(paths_from_patch(patch_path.read_text(encoding="utf-8")))
    if not paths:
        print("No paths were provided.", file=sys.stderr)
        return 1
    results = check_paths(paths, policy)
    for result in results:
        pattern = f" ({result.matched_pattern})" if result.matched_pattern else ""
        print(f"{result.path}\t{result.classification}{pattern}")
    return 0 if policy_allows_promotion(results) else 3


def registry_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    registry = Registry(registry_path(repo_path, args.registry))
    try:
        if args.registry_command == "create-run":
            run_id = registry.create_run(args.goal, repo_path, base_commit=current_commit(repo_path))
            print(run_id)
            return 0
        if args.registry_command == "register-attempt":
            attempt_id = registry.register_attempt(
                args.run_id,
                args.summary,
                branch=args.branch or "",
                base_commit=args.base_commit or "",
                head_commit=args.head_commit or "",
                patch_path=args.patch_path or "",
                status=args.status,
            )
            print(attempt_id)
            return 0
        if args.registry_command == "record-evaluation":
            evaluation_id = registry.record_evaluation(
                args.attempt_id,
                args.type,
                args.status,
                command=args.command or "",
                score=args.score,
                logs_path=args.logs_path or "",
                failure_reason=args.failure_reason or "",
            )
            print(evaluation_id)
            return 0
        if args.registry_command == "attach-patch":
            registry.attach_attempt_patch(
                args.attempt_id,
                patch_path=args.patch_path,
                head_commit=args.head_commit or "",
                status=args.status,
            )
            print(args.attempt_id)
            return 0
        if args.registry_command == "record-cost":
            cost_id = registry.record_cost(
                run_id=args.run_id,
                attempt_id=args.attempt_id,
                agent=args.agent or "",
                model=args.model or "",
                input_tokens=args.input_tokens,
                output_tokens=args.output_tokens,
                tool_calls=args.tool_calls,
                wall_clock_seconds=args.wall_clock_seconds,
                estimated_usd=args.estimated_usd,
            )
            print(cost_id)
            return 0
        if args.registry_command == "record-lineage":
            lineage_id = registry.record_lineage(
                args.attempt_id,
                args.relationship,
                related_attempt_id=args.related_attempt_id,
                note=args.note or "",
            )
            print(lineage_id)
            return 0
        if args.registry_command == "list-runs":
            for run in registry.list_runs():
                print(f"{run.id}\t{run.status}\t{run.goal}")
            return 0
        raise ValueError(f"Unsupported registry command: {args.registry_command}")
    finally:
        registry.close()


def report_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    registry = Registry(registry_path(repo_path, args.registry))
    try:
        output = Path(args.output) if args.output else repo_path / ".climbhill" / "reports" / f"run-{args.run_id}.md"
        if not output.is_absolute():
            output = repo_path / output
        generate_markdown_report(registry, args.run_id, output)
        print(f"Generated report: {output}")
        return 0
    finally:
        registry.close()


def run_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    database = registry_path(repo_path, args.registry)
    registry = Registry(database)
    try:
        run_id = registry.create_run(args.goal, repo_path, base_commit=current_commit(repo_path))
        print(f"Created run {run_id}")
        for index in range(1, args.attempts + 1):
            branch = args.branch_template.format(run_id=run_id, attempt=index)
            attempt_id = registry.register_attempt(
                run_id,
                f"Attempt {index} for: {args.goal}",
                branch=branch,
                base_commit=current_commit(repo_path),
                status="planned",
            )
            print(f"Registered attempt {attempt_id}: {branch}")
        print(f"Registry: {database}")
        return 0
    finally:
        registry.close()


def compare_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    registry = Registry(registry_path(repo_path, args.registry))
    try:
        comparison = registry.compare_attempts(args.run_id)
        if not comparison:
            print("No attempts registered.")
            return 1
        print("rank\tattempt\tpasses\tfailures\tsummary")
        for index, attempt in enumerate(comparison, start=1):
            print(
                f"{index}\t{attempt['id']}\t{attempt['passing_evaluations']}\t"
                f"{attempt['failing_evaluations']}\t{attempt['summary']}"
            )
        return 0
    finally:
        registry.close()


def resource_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    if args.resource_command == "search":
        for match in search_resources(repo_path, args.query, limit=args.limit):
            print(f"{match.path}\t{match.title}\t{match.snippet}")
        return 0
    if args.resource_command == "add":
        path = add_resource(
            repo_path,
            args.title,
            summary=args.summary,
            source=args.source or "",
            author=args.author or "",
            date=args.date or "",
            path_or_url=args.path_or_url or "",
            resource_type=args.type,
            trust_level=args.trust_level,
            tags=args.tags or "",
            reason=args.reason or "",
        )
        print(path.relative_to(repo_path))
        return 0
    raise ValueError(f"Unsupported resource command: {args.resource_command}")


def decision_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    registry = Registry(registry_path(repo_path, args.registry))
    try:
        decision_id = registry.record_decision(
            args.run_id,
            args.type,
            attempt_id=args.attempt_id,
            rationale=args.rationale or "",
            actor=args.actor or "",
        )
        print(decision_id)
        return 0
    finally:
        registry.close()


def reflect_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    registry = Registry(registry_path(repo_path, args.registry))
    try:
        runs = [registry.get_run(args.run_id)] if args.run_id else registry.list_runs()
        runs = [run for run in runs if run is not None]
        if not runs:
            print("No runs found to reflect on.", file=sys.stderr)
            return 1

        issue_dir = repo_path / ".climbhill" / "issue-proposals"
        issue_dir.mkdir(parents=True, exist_ok=True)
        proposed = []

        for run in runs:
            attempts = registry.list_attempts(run.id)
            evaluations = registry.list_evaluations_for_attempts(attempt.id for attempt in attempts)
            failures = [evaluation for evaluation in evaluations if evaluation["status"] != "passed"]
            if not attempts:
                title = f"Add Attempts for run {run.id}"
                body = (
                    f"Problem: Run {run.id} has no registered attempts.\n\n"
                    f"Evidence: Goal was `{run.goal}` but no attempt records exist.\n\n"
                    "Suggested implementation: run at least two bounded Attempts and record patches, evaluations, and costs.\n\n"
                    "Acceptance criteria: run has multiple attempts with policy and evaluation records.\n\n"
                    "Risk level: medium\n"
                )
                priority = "medium"
            elif failures:
                title = f"Investigate failing evaluations for run {run.id}"
                failure_lines = "\n".join(
                    f"- Attempt {failure['attempt_id']}: {failure['type']} {failure['status']} {failure['failure_reason'] or ''}".strip()
                    for failure in failures
                )
                body = (
                    f"Problem: Run {run.id} has failing attempt evaluations.\n\n"
                    f"Evidence:\n{failure_lines}\n\n"
                    "Suggested implementation: inspect the failed attempts, improve tests or docs if they exposed real gaps, and record a follow-up run.\n\n"
                    "Acceptance criteria: failure causes are documented and a follow-up issue, resource, or child Run exists.\n\n"
                    "Risk level: medium\n"
                )
                priority = "high"
            else:
                continue

            issue_id = registry.propose_issue(
                title,
                body,
                labels="climbhill,meta-analysis",
                priority=priority,
                evidence=f"run:{run.id}",
                source_run_ids=str(run.id),
                source_attempt_ids=",".join(str(attempt.id) for attempt in attempts),
            )
            issue_path = issue_dir / f"issue-{issue_id}.md"
            issue_path.write_text(f"# {title}\n\n{body}", encoding="utf-8")
            proposed.append(issue_path)

        if not proposed:
            print("No issue proposals generated.")
            return 0
        for path in proposed:
            print(path.relative_to(repo_path))
        return 0
    finally:
        registry.close()


def history_command(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    registry = Registry(registry_path(repo_path, args.registry))
    try:
        query = (args.query or "").lower()
        count = 0
        for run in registry.list_runs():
            for attempt in registry.list_attempts(run.id):
                if query and query not in run.goal.lower() and query not in attempt.summary.lower():
                    continue
                print(f"run {run.id}\tattempt {attempt.id}\t{attempt.status}\t{attempt.summary}")
                count += 1
                if count >= args.limit:
                    return 0
        return 0
    finally:
        registry.close()


def legacy_run_command(args: argparse.Namespace) -> int:
    skills = load_skill_infos(include_documentation=False)
    if args.skill not in skills:
        available = ", ".join(skills.keys()) or "<none>"
        print(f"Runnable skill '{args.skill}' not found. Available runnable skills: {available}", file=sys.stderr)
        return 1

    skill_dir = skills[args.skill].path

    try:
        prompt = resolve_prompt_text(args.prompt_id, args.prompt_text)
    except (ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    try:
        output_dir = ensure_output_dir(args.output_dir)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    system_prompt = build_system_prompt(args.skill, skill_dir)
    user_prompt = build_user_prompt(prompt, args.extra_instructions)

    cmd = ["claude", "--print", "--append-system-prompt", system_prompt]
    if args.model:
        cmd.extend(["--model", args.model])
    cmd.append(user_prompt)

    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("The 'claude' CLI could not be found in PATH. Install Claude Code before running.", file=sys.stderr)
        return 1

    if completed.returncode != 0:
        print("Claude CLI command failed:", file=sys.stderr)
        if completed.stderr:
            print(completed.stderr.strip(), file=sys.stderr)
        return completed.returncode

    output_text = completed.stdout.strip()
    if not output_text:
        print("Claude CLI returned empty output.", file=sys.stderr)
        return 1

    output_path = next_output_path(output_dir, args.skill)
    output_path.write_text(output_text + "\n", encoding="utf-8")

    if completed.stderr:
        print(completed.stderr.strip(), file=sys.stderr)

    print(f"Saved report to {output_path.relative_to(REPO_ROOT)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="climbhill",
        description="ClimbHill.ai local CLI for safe recursive repository improvement.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize ClimbHill repository support.")
    init_parser.add_argument("--repo", default=".", help="Repository path to initialize.")
    init_parser.add_argument("--registry", help="Registry path relative to repo or absolute path.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing ClimbHill templates.")
    init_parser.set_defaults(func=init_command)

    prepare_parser = subparsers.add_parser(
        "prepare", help="Report or create repository support files."
    )
    prepare_parser.add_argument("--repo", default=".", help="Repository path to prepare.")
    prepare_parser.add_argument("--apply", action="store_true", help="Create missing files.")
    prepare_parser.set_defaults(func=prepare_command)

    policy_parser = subparsers.add_parser("policy", help="Policy commands.")
    policy_subparsers = policy_parser.add_subparsers(dest="policy_command", required=True)
    policy_check = policy_subparsers.add_parser("check", help="Classify paths against policy.")
    policy_check.add_argument("paths", nargs="*", help="Paths to classify.")
    policy_check.add_argument("--patch-file", help="Unified diff file to classify.")
    policy_check.add_argument("--repo", default=".", help="Repository path containing .climbhill/policy.yaml.")
    policy_check.set_defaults(func=policy_check_command)

    registry_parser = subparsers.add_parser("registry", help="Local registry commands.")
    registry_parser.add_argument("--repo", default=".", help="Repository path.")
    registry_parser.add_argument("--registry", help="Registry path relative to repo or absolute path.")
    registry_subparsers = registry_parser.add_subparsers(dest="registry_command", required=True)

    create_run = registry_subparsers.add_parser("create-run", help="Create an improvement run.")
    create_run.add_argument("--goal", required=True, help="Improvement goal.")
    create_run.set_defaults(func=registry_command)

    register_attempt = registry_subparsers.add_parser(
        "register-attempt", help="Register an Attempt."
    )
    register_attempt.add_argument("--run-id", required=True, type=int)
    register_attempt.add_argument("--summary", required=True)
    register_attempt.add_argument("--branch")
    register_attempt.add_argument("--base-commit")
    register_attempt.add_argument("--head-commit")
    register_attempt.add_argument("--patch-path")
    register_attempt.add_argument("--status", default="registered")
    register_attempt.set_defaults(func=registry_command)

    record_eval = registry_subparsers.add_parser("record-evaluation", help="Record an evaluation.")
    record_eval.add_argument("--attempt-id", required=True, type=int)
    record_eval.add_argument("--type", required=True)
    record_eval.add_argument("--status", required=True)
    record_eval.add_argument("--command")
    record_eval.add_argument("--score", type=float)
    record_eval.add_argument("--logs-path")
    record_eval.add_argument("--failure-reason")
    record_eval.set_defaults(func=registry_command)

    attach_patch = registry_subparsers.add_parser("attach-patch", help="Attach a patch to an Attempt.")
    attach_patch.add_argument("--attempt-id", required=True, type=int)
    attach_patch.add_argument("--patch-path", required=True)
    attach_patch.add_argument("--head-commit")
    attach_patch.add_argument("--status", default="patched")
    attach_patch.set_defaults(func=registry_command)

    record_cost = registry_subparsers.add_parser("record-cost", help="Record run or attempt cost.")
    record_cost.add_argument("--run-id", type=int)
    record_cost.add_argument("--attempt-id", type=int)
    record_cost.add_argument("--agent")
    record_cost.add_argument("--model")
    record_cost.add_argument("--input-tokens", type=int)
    record_cost.add_argument("--output-tokens", type=int)
    record_cost.add_argument("--tool-calls", type=int)
    record_cost.add_argument("--wall-clock-seconds", type=float)
    record_cost.add_argument("--estimated-usd", type=float)
    record_cost.set_defaults(func=registry_command)

    record_lineage = registry_subparsers.add_parser(
        "record-lineage", help="Record attempt lineage."
    )
    record_lineage.add_argument("--attempt-id", required=True, type=int)
    record_lineage.add_argument("--relationship", required=True)
    record_lineage.add_argument("--related-attempt-id", type=int)
    record_lineage.add_argument("--note")
    record_lineage.set_defaults(func=registry_command)

    list_runs = registry_subparsers.add_parser("list-runs", help="List recorded runs.")
    list_runs.set_defaults(func=registry_command)

    report_parser = subparsers.add_parser("report", help="Generate a Markdown run report.")
    report_parser.add_argument("--repo", default=".", help="Repository path.")
    report_parser.add_argument("--registry", help="Registry path relative to repo or absolute path.")
    report_parser.add_argument("--run-id", required=True, type=int)
    report_parser.add_argument("--output", help="Output Markdown path.")
    report_parser.set_defaults(func=report_command)

    run_parser = subparsers.add_parser("run", help="Create a bounded ClimbHill improvement run.")
    run_parser.add_argument("--repo", default=".", help="Repository path.")
    run_parser.add_argument("--registry", help="Registry path relative to repo or absolute path.")
    run_parser.add_argument("--goal", required=True, help="Improvement goal.")
    run_parser.add_argument("--attempts", type=int, default=1, help="Number of planned attempts to register.")
    run_parser.add_argument(
        "--branch-template",
        default="climbhill/run-{run_id}/attempt-{attempt}",
        help="Branch naming template using {run_id} and {attempt}.",
    )
    run_parser.set_defaults(func=run_command)

    compare_parser = subparsers.add_parser("compare", help="Compare attempts for a run.")
    compare_parser.add_argument("--repo", default=".", help="Repository path.")
    compare_parser.add_argument("--registry", help="Registry path relative to repo or absolute path.")
    compare_parser.add_argument("--run-id", required=True, type=int)
    compare_parser.set_defaults(func=compare_command)

    resource_parser = subparsers.add_parser("resources", help="Resource commands.")
    resource_parser.add_argument("--repo", default=".", help="Repository path.")
    resource_subparsers = resource_parser.add_subparsers(dest="resource_command", required=True)
    resource_search = resource_subparsers.add_parser("search", help="Search resources.")
    resource_search.add_argument("query")
    resource_search.add_argument("--limit", type=int, default=10)
    resource_search.set_defaults(func=resource_command)
    resource_add = resource_subparsers.add_parser("add", help="Add a resource.")
    resource_add.add_argument("--title", required=True)
    resource_add.add_argument("--summary", required=True)
    resource_add.add_argument("--source")
    resource_add.add_argument("--author")
    resource_add.add_argument("--date")
    resource_add.add_argument("--path-or-url")
    resource_add.add_argument("--type", default="user-guidance")
    resource_add.add_argument("--trust-level", default="experimental")
    resource_add.add_argument("--tags")
    resource_add.add_argument("--reason")
    resource_add.set_defaults(func=resource_command)

    decision_parser = subparsers.add_parser("decision", help="Record a human decision.")
    decision_parser.add_argument("--repo", default=".", help="Repository path.")
    decision_parser.add_argument("--registry", help="Registry path relative to repo or absolute path.")
    decision_parser.add_argument("--run-id", required=True, type=int)
    decision_parser.add_argument("--attempt-id", type=int)
    decision_parser.add_argument("--type", required=True, help="Decision type such as promote or reject.")
    decision_parser.add_argument("--rationale")
    decision_parser.add_argument("--actor")
    decision_parser.set_defaults(func=decision_command)

    reflect_parser = subparsers.add_parser("reflect", help="Run meta-analysis and propose issues.")
    reflect_parser.add_argument("--repo", default=".", help="Repository path.")
    reflect_parser.add_argument("--registry", help="Registry path relative to repo or absolute path.")
    reflect_parser.add_argument("--run-id", type=int)
    reflect_parser.set_defaults(func=reflect_command)

    history_parser = subparsers.add_parser("history", help="Historical attempt commands.")
    history_parser.add_argument("--repo", default=".", help="Repository path.")
    history_parser.add_argument("--registry", help="Registry path relative to repo or absolute path.")
    history_subparsers = history_parser.add_subparsers(dest="history_command", required=True)
    history_sample = history_subparsers.add_parser("sample", help="Sample historical attempts.")
    history_sample.add_argument("--query", default="")
    history_sample.add_argument("--limit", type=int, default=5)
    history_sample.set_defaults(func=history_command)

    list_skills = subparsers.add_parser("list-skills", help="List available Claude Code skills.")
    list_skills.set_defaults(func=list_skills_command)

    list_prompts = subparsers.add_parser(
        "list-prompts", help="List canned research prompts from the taxonomy examples."
    )
    list_prompts.set_defaults(func=list_prompts_command)

    legacy_run_parser = subparsers.add_parser(
        "legacy-run", help="Execute a legacy headless Claude Code skill run."
    )
    legacy_run_parser.add_argument("--skill", required=True, help="Skill name under .claude/skills to activate.")
    prompt_group = legacy_run_parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt-id", help="Identifier from 'climbhill list-prompts'.")
    prompt_group.add_argument("--prompt-text", help="Freeform research prompt text.")
    legacy_run_parser.add_argument("--model", help="Optional Claude model alias (passed through to claude CLI).")
    legacy_run_parser.add_argument(
        "--extra-instructions",
        help="Additional instructions appended to the research brief.",
    )
    legacy_run_parser.add_argument(
        "--output-dir",
        help="Directory for saving outputs (default: outputs/ in repo root).",
    )
    legacy_run_parser.set_defaults(func=legacy_run_command)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
