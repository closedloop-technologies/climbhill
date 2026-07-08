from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from ipaddress import ip_address
from pathlib import Path
from typing import Iterable, List, Sequence
from urllib.parse import unquote, urlparse

import requests


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = REPO_ROOT / "skills" / "provider-source-index.md"
SKILLS_ROOT = REPO_ROOT / "skills"
DATE_RE = re.compile(r"^Last refreshed:\s*(\d{4}-\d{2}-\d{2})\.", re.MULTILINE)
ROW_RE = re.compile(r"^\|\s*`([^`]*)`\s*\|\s*([^|]*?)\s*\|", re.MULTILINE)
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ENCODED_PATH_SEPARATOR_RE = re.compile(r"%2f|%5c", re.IGNORECASE)
MALFORMED_PERCENT_ENCODING_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
DNS_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)


@dataclass
class SourceEntry:
    skill: str
    source: str


@dataclass
class CheckResult:
    ok: bool
    message: str


def parse_refreshed_date(text: str) -> date | None:
    match = DATE_RE.search(text)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def parse_source_entries(text: str) -> List[SourceEntry]:
    entries = []
    for skill, source in ROW_RE.findall(text):
        if skill == "Skill" or source.strip() == "Source":
            continue
        entries.append(SourceEntry(skill=skill, source=source.strip()))
    return entries


def expected_skill_names(skills_root: Path = SKILLS_ROOT) -> List[str]:
    return sorted(path.name for path in skills_root.iterdir() if path.is_dir())


def normalized_skill_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")


def fully_unquote(value: str) -> str:
    decoded = value
    for _ in range(5):
        next_value = unquote(decoded)
        if next_value == decoded:
            return decoded
        decoded = next_value
    return decoded


def has_encoded_control_character(value: str) -> bool:
    decoded = fully_unquote(value)
    return any(ord(character) < 32 or ord(character) == 127 for character in decoded)


def has_encoded_whitespace(value: str) -> bool:
    decoded = fully_unquote(value)
    return any(character.isspace() for character in decoded)


def has_encoded_query_or_fragment_marker(value: str) -> bool:
    decoded = fully_unquote(value)
    return decoded != value and ("?" in decoded or "#" in decoded)


def has_encoded_path_separator(value: str) -> bool:
    decoded = fully_unquote(value)
    return (
        bool(ENCODED_PATH_SEPARATOR_RE.search(value))
        or ("\\" in decoded and "\\" not in value)
        or len(decoded.split("/")) != len(value.split("/"))
    )


def has_encoded_path_alias(value: str) -> bool:
    return unquote(value) != value


def has_malformed_percent_encoding(value: str) -> bool:
    return bool(MALFORMED_PERCENT_ENCODING_RE.search(value))


def has_trailing_host_dot(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and parsed.hostname.endswith(".")


def has_percent_encoded_host(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and "%" in parsed.netloc


def has_non_global_ip_host(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        return not ip_address(parsed.hostname).is_global
    except ValueError:
        return False


def has_valid_dns_hostname(hostname: str) -> bool:
    try:
        ip_address(hostname)
        return True
    except ValueError:
        pass

    if len(hostname) > 253:
        return False
    labels = hostname.split(".")
    if len(labels) < 2 or labels[-1].isdigit():
        return False
    return all(DNS_LABEL_RE.fullmatch(label) for label in labels)


def has_valid_url_port(url: str) -> bool:
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError:
        return False
    if parsed.netloc.rsplit("@", 1)[-1].endswith(":"):
        return False
    if port == 0:
        return False
    return True


def has_remote_parent_directory_reference(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and ".." in Path(
        fully_unquote(parsed.path)
    ).parts


def decoded_path_segments(value: str) -> list[str]:
    return fully_unquote(value).split("/")


def has_current_directory_reference(value: str) -> bool:
    return "." in decoded_path_segments(value)


def has_repeated_path_separator(value: str) -> bool:
    return "//" in value


def has_symlink_path_component(repo_root: Path, relative_path: Path) -> bool:
    current = repo_root
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def validate_source_reference(entry: SourceEntry) -> CheckResult | None:
    if any(character.isspace() for character in entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain whitespace",
        )
    if has_encoded_whitespace(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain encoded whitespace",
        )
    if has_malformed_percent_encoding(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain malformed percent encoding",
        )
    if has_encoded_control_character(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain encoded control characters",
        )
    try:
        parsed = urlparse(entry.source)
    except ValueError:
        return CheckResult(False, f"{entry.skill}: {entry.source} must be a valid URL")
    if parsed.scheme == "http":
        return CheckResult(False, f"{entry.skill}: {entry.source} must use HTTPS")
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} has unsupported URL scheme",
        )
    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        return CheckResult(False, f"{entry.skill}: {entry.source} must include a host")
    if has_percent_encoded_host(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} host must not contain percent encoding",
        )
    if has_trailing_host_dot(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} host must not end with a dot",
        )
    if parsed.scheme in {"http", "https"} and "\\" in entry.source:
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} URL must use forward slashes",
        )
    if parsed.scheme in {"http", "https"} and parsed.hostname and not has_valid_dns_hostname(
        parsed.hostname
    ):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} host must be a valid DNS name or IP address",
        )
    if parsed.scheme in {"http", "https"} and not has_valid_url_port(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} URL port must be numeric and in range",
        )
    if parsed.scheme in {"http", "https"} and has_non_global_ip_host(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} IP host must be globally routable",
        )
    if parsed.scheme in {"http", "https"} and has_repeated_path_separator(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} URL path must not contain repeated separators",
        )
    if parsed.scheme in {"http", "https"} and has_encoded_path_separator(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} URL path must not encode path separators",
        )
    if parsed.scheme in {"http", "https"} and has_encoded_query_or_fragment_marker(
        parsed.path
    ):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} URL path must not encode query or fragment markers",
        )
    if has_remote_parent_directory_reference(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} URL path must not contain parent directory references",
        )
    if parsed.scheme in {"http", "https"} and has_current_directory_reference(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} URL path must not contain current directory references",
        )
    if parsed.scheme in {"http", "https"} and has_encoded_path_alias(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} URL path must not contain percent-encoded aliases",
        )
    if parsed.scheme in {"http", "https"} and (
        parsed.username is not None or parsed.password is not None
    ):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not include credentials",
        )
    if not parsed.scheme and parsed.query:
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not include query parameters",
        )
    if not parsed.scheme and has_encoded_path_separator(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not encode path separators",
        )
    if not parsed.scheme and has_encoded_query_or_fragment_marker(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not encode query or fragment markers",
        )
    local_path = fully_unquote(parsed.path) if not parsed.scheme else entry.source
    if not parsed.scheme and not local_path:
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must include a path",
        )
    if not parsed.scheme and "\\" in local_path:
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must use forward slashes",
        )
    if not parsed.scheme and has_repeated_path_separator(local_path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not contain repeated separators",
        )
    if not parsed.scheme and Path(local_path).is_absolute():
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must be repo-relative",
        )
    if not parsed.scheme and ".." in Path(local_path).parts:
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain parent directory references",
        )
    if not parsed.scheme and has_current_directory_reference(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain current directory references",
        )
    if not parsed.scheme and any(part.startswith(".") for part in Path(local_path).parts):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not contain hidden path components",
        )
    if not parsed.scheme and any(part.startswith("-") for part in Path(local_path).parts):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not contain flag-like path components",
        )
    if not parsed.scheme and has_encoded_path_alias(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not contain percent-encoded aliases",
        )
    return None


def check_source_index(
    index_path: Path = DEFAULT_INDEX,
    *,
    max_age_days: int = 30,
    today: date | None = None,
) -> List[CheckResult]:
    today = today or datetime.now().date()
    if isinstance(max_age_days, bool) or not isinstance(max_age_days, int):
        return [CheckResult(False, "max_age_days must be a non-negative integer")]
    if max_age_days < 0:
        return [CheckResult(False, "max_age_days must be a non-negative integer")]
    if not index_path.exists():
        return [CheckResult(False, f"missing source index: {index_path}")]

    text = index_path.read_text(encoding="utf-8")
    results: List[CheckResult] = []
    if "| Skill | Source |" not in text:
        results.append(CheckResult(False, "source index table must include Skill and Source header"))

    refreshed = parse_refreshed_date(text)
    if refreshed is None:
        results.append(CheckResult(False, "missing Last refreshed date"))
    else:
        age = (today - refreshed).days
        if age < 0:
            results.append(
                CheckResult(
                    False,
                    f"Last refreshed {refreshed.isoformat()} is in the future",
                )
            )
        else:
            results.append(
                CheckResult(
                    age <= max_age_days,
                    f"Last refreshed {refreshed.isoformat()} ({age} days old)",
                )
            )

    entries = parse_source_entries(text)
    for entry in entries:
        if not entry.skill:
            results.append(CheckResult(False, "source index row has a blank skill name"))
        elif not SKILL_NAME_RE.fullmatch(entry.skill):
            results.append(
                CheckResult(False, f"{entry.skill}: skill name must be lowercase hyphen-case")
            )
        if not entry.source:
            results.append(
                CheckResult(False, f"{entry.skill or '<blank>'}: source must be non-empty")
            )
        else:
            source_result = validate_source_reference(entry)
            if source_result is not None:
                results.append(source_result)
    indexed_skills = {entry.skill for entry in entries}
    duplicate_entries = sorted(
        f"{skill} -> {source}"
        for (skill, source), count in Counter(
            (entry.skill, entry.source) for entry in entries
        ).items()
        if count > 1
    )
    if duplicate_entries:
        results.append(
            CheckResult(
                False,
                "duplicate source index rows: " + ", ".join(duplicate_entries),
            )
        )
    duplicate_sources = sorted(
        source
        for source, count in Counter(entry.source for entry in entries if entry.source).items()
        if count > 1
    )
    if duplicate_sources:
        results.append(
            CheckResult(
                False,
                "duplicate source index sources: " + ", ".join(duplicate_sources),
            )
        )
    expected_skills = set(expected_skill_names(index_path.parent))
    invalid_skill_dirs = sorted(
        skill_name for skill_name in expected_skills if not SKILL_NAME_RE.fullmatch(skill_name)
    )
    if invalid_skill_dirs:
        results.append(
            CheckResult(
                False,
                "skill directories must be lowercase hyphen-case: "
                + ", ".join(invalid_skill_dirs),
            )
        )
    normalized_directory_counts = Counter(
        normalized_skill_name(skill_name) for skill_name in expected_skills
    )
    duplicate_normalized_dirs = sorted(
        skill_name for skill_name, count in normalized_directory_counts.items() if count > 1
    )
    if duplicate_normalized_dirs:
        results.append(
            CheckResult(
                False,
                "skill directories collide after normalization: "
                + ", ".join(duplicate_normalized_dirs),
            )
        )
    for skill_name in sorted(expected_skills):
        results.append(
            CheckResult(
                skill_name in indexed_skills,
                f"{skill_name}: {'indexed' if skill_name in indexed_skills else 'missing'}",
            )
        )
    unknown_skills = sorted(indexed_skills - expected_skills)
    if unknown_skills:
        results.append(
            CheckResult(
                False,
                "unknown source index skills: " + ", ".join(unknown_skills),
            )
        )

    return results


def check_link(entry: SourceEntry, repo_root: Path = REPO_ROOT, timeout: float = 10.0) -> CheckResult:
    if isinstance(timeout, bool):
        return CheckResult(False, "timeout must be a positive number")
    try:
        finite_timeout = math.isfinite(timeout)
    except TypeError:
        return CheckResult(False, "timeout must be a positive number")
    if not finite_timeout or timeout <= 0:
        return CheckResult(False, "timeout must be a positive number")

    if any(character.isspace() for character in entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain whitespace",
        )
    if has_encoded_whitespace(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain encoded whitespace",
        )
    if has_malformed_percent_encoding(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain malformed percent encoding",
        )
    if has_encoded_control_character(entry.source):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain encoded control characters",
        )

    try:
        parsed = urlparse(entry.source)
    except ValueError:
        return CheckResult(False, f"{entry.skill}: {entry.source} must be a valid URL")
    if parsed.scheme in {"http", "https"}:
        if parsed.scheme == "http":
            return CheckResult(False, f"{entry.skill}: {entry.source} must use HTTPS")
        if not parsed.netloc:
            return CheckResult(False, f"{entry.skill}: {entry.source} must include a host")
        if has_percent_encoded_host(entry.source):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} host must not contain percent encoding",
            )
        if has_trailing_host_dot(entry.source):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} host must not end with a dot",
            )
        if "\\" in entry.source:
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} URL must use forward slashes",
            )
        if parsed.hostname and not has_valid_dns_hostname(parsed.hostname):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} host must be a valid DNS name or IP address",
            )
        if not has_valid_url_port(entry.source):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} URL port must be numeric and in range",
            )
        if has_non_global_ip_host(entry.source):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} IP host must be globally routable",
            )
        if has_repeated_path_separator(parsed.path):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} URL path must not contain repeated separators",
            )
        if has_encoded_path_separator(parsed.path):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} URL path must not encode path separators",
            )
        if has_encoded_query_or_fragment_marker(parsed.path):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} URL path must not encode query or fragment markers",
            )
        if has_remote_parent_directory_reference(entry.source):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} URL path must not contain parent directory references",
            )
        if has_current_directory_reference(parsed.path):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} URL path must not contain current directory references",
            )
        if has_encoded_path_alias(parsed.path):
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} URL path must not contain percent-encoded aliases",
            )
        if parsed.username is not None or parsed.password is not None:
            return CheckResult(
                False,
                f"{entry.skill}: {entry.source} must not include credentials",
            )
        try:
            response = requests.get(
                entry.source,
                timeout=timeout,
                allow_redirects=True,
                headers={"User-Agent": "awesome-deep-researchers-source-check/0.1"},
            )
        except requests.RequestException as exc:
            return CheckResult(False, f"{entry.skill}: {entry.source} failed: {exc}")
        ok = 200 <= response.status_code < 400
        return CheckResult(ok, f"{entry.skill}: {entry.source} HTTP {response.status_code}")
    if parsed.scheme:
        return CheckResult(False, f"{entry.skill}: {entry.source} has unsupported URL scheme")

    if parsed.query:
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not include query parameters",
        )
    if has_encoded_path_separator(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not encode path separators",
        )
    if has_encoded_query_or_fragment_marker(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not encode query or fragment markers",
        )
    local_source_path = fully_unquote(parsed.path)
    if not local_source_path:
        return CheckResult(False, f"{entry.skill}: {entry.source} local source must include a path")
    if "\\" in local_source_path:
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must use forward slashes",
        )
    if has_repeated_path_separator(local_source_path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not contain repeated separators",
        )
    if Path(local_source_path).is_absolute():
        return CheckResult(False, f"{entry.skill}: {entry.source} must be repo-relative")
    if ".." in Path(local_source_path).parts:
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain parent directory references",
        )
    if has_current_directory_reference(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} must not contain current directory references",
        )
    if any(part.startswith(".") for part in Path(local_source_path).parts):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not contain hidden path components",
        )
    if any(part.startswith("-") for part in Path(local_source_path).parts):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not contain flag-like path components",
        )
    if has_encoded_path_alias(parsed.path):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not contain percent-encoded aliases",
        )
    if has_symlink_path_component(repo_root, Path(local_source_path)):
        return CheckResult(
            False,
            f"{entry.skill}: {entry.source} local source must not contain symlinks",
        )
    local_path = (repo_root / local_source_path).resolve()
    try:
        local_path.relative_to(repo_root.resolve())
    except ValueError:
        return CheckResult(False, f"{entry.skill}: {entry.source} escapes repo root")
    if not local_path.exists():
        return CheckResult(False, f"{entry.skill}: {entry.source} local path missing")
    if not local_path.is_file():
        return CheckResult(False, f"{entry.skill}: {entry.source} local path must be a file")
    return CheckResult(True, f"{entry.skill}: {entry.source} local path")


def check_links(index_path: Path = DEFAULT_INDEX) -> List[CheckResult]:
    text = index_path.read_text(encoding="utf-8")
    repo_root = index_path.parent.parent
    return [check_link(entry, repo_root=repo_root) for entry in parse_source_entries(text)]


def format_results(results: Iterable[CheckResult]) -> str:
    lines = []
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        lines.append(f"{status}\t{result.message}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check provider source freshness and coverage.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="Source index markdown file.")
    parser.add_argument("--max-age-days", type=int, default=30, help="Maximum allowed index age.")
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="Also perform live HTTP/local path checks for indexed sources.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = check_source_index(args.index, max_age_days=args.max_age_days)
    if args.check_links and args.index.exists():
        results.extend(check_links(args.index))
    print(format_results(results))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
