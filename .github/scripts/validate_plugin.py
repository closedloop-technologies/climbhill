#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[+-][0-9A-Za-z.-]+)?$")
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a local Codex plugin package.")
    parser.add_argument("plugin_path", type=Path)
    args = parser.parse_args()

    plugin_root = args.plugin_path.resolve()
    errors = validate_plugin(plugin_root)
    if errors:
        print("Plugin validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Plugin validation passed: {plugin_root}")
    return 0


def validate_plugin(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        return ["missing .codex-plugin/plugin.json"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid .codex-plugin/plugin.json: {exc}"]
    if not isinstance(manifest, dict):
        return [".codex-plugin/plugin.json must contain an object"]

    require_string(manifest, "name", errors)
    version = require_string(manifest, "version", errors)
    if version and not SEMVER_RE.fullmatch(version):
        errors.append("version must be semver")
    require_string(manifest, "description", errors)

    author = manifest.get("author")
    if not isinstance(author, dict) or not author.get("name"):
        errors.append("author.name is required")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("interface object is required")
    else:
        for field in [
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
        ]:
            require_string(interface, field, errors, prefix="interface")
        if not interface.get("defaultPrompt") and not interface.get("default_prompt"):
            errors.append("interface.defaultPrompt is required")
        capabilities = interface.get("capabilities")
        if not isinstance(capabilities, list) or not all(isinstance(item, str) and item for item in capabilities):
            errors.append("interface.capabilities must be a non-empty string list")
        brand_color = interface.get("brandColor")
        if brand_color is not None and (
            not isinstance(brand_color, str) or not HEX_COLOR_RE.fullmatch(brand_color)
        ):
            errors.append("interface.brandColor must be #RRGGBB")

    validate_relative_path(plugin_root, manifest.get("skills"), errors, "skills")
    validate_relative_path(plugin_root, manifest.get("mcpServers"), errors, "mcpServers")
    reject_todo_markers(manifest, "$", errors)
    return errors


def require_string(payload: dict[str, Any], key: str, errors: list[str], *, prefix: str = "") -> str | None:
    value = payload.get(key)
    field = f"{prefix}.{key}" if prefix else key
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")
        return None
    return value


def validate_relative_path(plugin_root: Path, value: Any, errors: list[str], field: str) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not value.startswith("./"):
        errors.append(f"{field} must be a relative path starting with ./")
        return
    if not (plugin_root / value).exists():
        errors.append(f"{field} points to missing path: {value}")


def reject_todo_markers(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, str):
        if "[TODO:" in value:
            errors.append(f"{path} contains a TODO placeholder")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            reject_todo_markers(item, f"{path}[{index}]", errors)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            reject_todo_markers(item, f"{path}.{key}", errors)


if __name__ == "__main__":
    raise SystemExit(main())
