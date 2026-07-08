from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class ResourceMatch:
    path: str
    title: str
    snippet: str


def slugify_resource_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "resource"


def resources_root(repo_path: Path) -> Path:
    return repo_path / "resources"


def search_resources(repo_path: Path, query: str, limit: int = 10) -> List[ResourceMatch]:
    root = resources_root(repo_path)
    if not root.exists():
        return []
    query_lower = query.lower()
    matches: List[ResourceMatch] = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if query_lower not in text.lower() and query_lower not in path.as_posix().lower():
            continue
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        title = lines[0].lstrip("# ").strip() if lines else path.stem
        snippet = ""
        for line in lines:
            if query_lower in line.lower():
                snippet = line
                break
        matches.append(
            ResourceMatch(
                path=str(path.relative_to(repo_path)),
                title=title,
                snippet=snippet or (lines[1] if len(lines) > 1 else ""),
            )
        )
        if len(matches) >= limit:
            break
    return matches


def add_resource(
    repo_path: Path,
    title: str,
    *,
    summary: str,
    source: str = "",
    author: str = "",
    date: str = "",
    path_or_url: str = "",
    resource_type: str = "user-guidance",
    trust_level: str = "experimental",
    tags: str = "",
    reason: str = "",
) -> Path:
    root = resources_root(repo_path) / resource_type
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slugify_resource_title(title)}.md"
    content = "\n".join(
        [
            f"# {title}",
            "",
            "Metadata:",
            "",
            f"- Type: {resource_type}",
            f"- Source: {source or 'not specified'}",
            f"- Author: {author or 'not specified'}",
            f"- Date: {date or 'not specified'}",
            f"- Path or URL: {path_or_url or source or 'not specified'}",
            f"- Trust level: {trust_level}",
            f"- Tags: {tags or 'none'}",
            f"- Reason added: {reason or 'not specified'}",
            "",
            "Summary:",
            "",
            summary,
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")
    return path
