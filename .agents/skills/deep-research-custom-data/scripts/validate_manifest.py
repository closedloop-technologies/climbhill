#!/usr/bin/env python3
"""Validate a custom-source deep research manifest."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import socket
import sys
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import unquote, urlsplit

SUPPORTED_SOURCE_TYPES = {
    "google_drive",
    "youtube",
    "local_file",
    "s3",
    "arxiv",
    "database",
    "csv",
    "slack",
    "email",
    "ticket",
}

COMMON_REQUIRED = {"source_id", "source_type", "title", "citation_anchor"}
TYPE_REQUIRED = {
    "google_drive": {"file_id", "web_url", "modified_time"},
    "youtube": {"video_id", "url", "published_at"},
    "local_file": {"path", "sha256", "modified_time"},
    "s3": {"bucket", "key", "etag"},
    "arxiv": {"arxiv_id", "version", "pdf_url"},
    "database": {"database", "query_id", "query"},
    "csv": {"path", "sha256", "schema"},
    "slack": {"workspace", "channel", "message_id", "timestamp"},
    "email": {"mailbox", "message_id", "timestamp"},
    "ticket": {"system", "ticket_id", "url"},
}
URL_FIELDS_BY_TYPE = {
    "google_drive": ("web_url",),
    "youtube": ("url",),
    "arxiv": ("pdf_url",),
    "ticket": ("url",),
}
MALFORMED_PERCENT_ENCODING_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
HOST_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)
NAT64_WELL_KNOWN_PREFIX = ipaddress.IPv6Network("64:ff9b::/96")


def parse_legacy_ipv4_address(hostname: str) -> ipaddress.IPv4Address | None:
    try:
        packed_address = socket.inet_aton(hostname)
    except OSError:
        return None
    try:
        return ipaddress.IPv4Address(packed_address)
    except ipaddress.AddressValueError:
        return None


def normalize_host_ip(
    host_ip: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    if isinstance(host_ip, ipaddress.IPv6Address) and host_ip in NAT64_WELL_KNOWN_PREFIX:
        return ipaddress.IPv4Address(int(host_ip) & 0xFFFFFFFF)
    return host_ip


def has_valid_hostname_syntax(hostname: str) -> bool:
    if not hostname or len(hostname) > 253:
        return False
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        labels = hostname.split(".")
        return (
            len(labels) >= 2
            and any(character.isalpha() for character in labels[-1])
            and all(HOST_LABEL_RE.fullmatch(label) for label in labels)
        )
    return True


def is_safe_relative_path(value: str) -> bool:
    if MALFORMED_PERCENT_ENCODING_RE.search(value):
        return False
    if "\\" in value:
        return False
    if "?" in value or "#" in value:
        return False
    if any(character.isspace() for character in value):
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    try:
        decoded_value = unquote(value, errors="strict")
    except UnicodeDecodeError:
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in decoded_value):
        return False
    if "\\" in decoded_value:
        return False
    if "?" in decoded_value or "#" in decoded_value:
        return False
    if decoded_value.split("/") != value.split("/"):
        return False
    if decoded_value != value:
        return False
    return not Path(decoded_value).is_absolute() and all(
        part not in {"", ".", ".."} for part in decoded_value.split("/")
    )


def has_decoded_control_character(value: str) -> bool:
    decoded_value = value
    for _ in range(3):
        previous_value = decoded_value
        try:
            decoded_value = unquote(previous_value, errors="strict")
        except UnicodeDecodeError:
            return True
        if any(ord(character) < 32 or ord(character) == 127 for character in decoded_value):
            return True
        if decoded_value == previous_value:
            return False
    return False


def fully_unquote(value: str) -> str:
    decoded_value = value
    for _ in range(3):
        previous_value = decoded_value
        decoded_value = unquote(previous_value, errors="strict")
        if decoded_value == previous_value:
            return decoded_value
    return decoded_value


def is_safe_http_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if value != value.strip():
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    if any(character.isspace() for character in value):
        return False
    if MALFORMED_PERCENT_ENCODING_RE.search(value):
        return False
    if has_decoded_control_character(value):
        return False
    decoded_value = fully_unquote(value)
    if any(character.isspace() for character in decoded_value):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.hostname:
        return False
    if unquote(parsed.path, errors="strict") != parsed.path:
        return False
    try:
        parsed.port
    except ValueError:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    hostname = parsed.hostname.lower()
    if hostname.endswith("."):
        return False
    try:
        host_ip = normalize_host_ip(ipaddress.ip_address(hostname))
    except ValueError:
        host_ip = parse_legacy_ipv4_address(hostname)
    if host_ip is not None and (
        host_ip.is_private
        or host_ip.is_loopback
        or host_ip.is_link_local
        or host_ip.is_multicast
        or host_ip.is_unspecified
    ):
        return False
    if "%" in parsed.netloc.rsplit("@", 1)[-1].split(":", 1)[0]:
        return False
    if (
        hostname == "localhost"
        or hostname.endswith(".localhost")
        or hostname == "0.0.0.0"
        or hostname == "127.0.0.1"
        or hostname.startswith("127.")
        or hostname == "::1"
    ):
        return False
    if not has_valid_hostname_syntax(hostname):
        return False
    return True


def load_manifest(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_source(source: Dict[str, Any], index: int) -> List[str]:
    errors: List[str] = []
    label = source.get("source_id") or f"sources[{index}]"
    source_type = source.get("source_type")

    missing_common = sorted(name for name in COMMON_REQUIRED if not source.get(name))
    for name in missing_common:
        errors.append(f"{label}: missing required field {name}")

    if source_type not in SUPPORTED_SOURCE_TYPES:
        errors.append(f"{label}: unsupported source_type {source_type!r}")
        return errors

    missing_type = sorted(name for name in TYPE_REQUIRED[source_type] if not source.get(name))
    for name in missing_type:
        errors.append(f"{label}: missing {source_type} field {name}")

    for field_name in URL_FIELDS_BY_TYPE.get(source_type, ()):
        value = source.get(field_name)
        if value and not is_safe_http_url(value):
            errors.append(f"{label}: {field_name} must be an absolute http(s) URL")

    anchors = source.get("anchors", [])
    if anchors is not None and not isinstance(anchors, list):
        errors.append(f"{label}: anchors must be a list when provided")

    if source_type in {"local_file", "csv"}:
        path_value = source.get("path")
        if path_value and not is_safe_relative_path(str(path_value)):
            errors.append(f"{label}: path must be a safe relative path")

    if source_type == "s3":
        key_value = source.get("key")
        if key_value and not is_safe_relative_path(str(key_value)):
            errors.append(f"{label}: key must be a safe relative path")

    return errors


def validate_manifest(manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not manifest.get("corpus_id"):
        errors.append("manifest: missing corpus_id")
    if not manifest.get("research_question"):
        errors.append("manifest: missing research_question")
    if not manifest.get("allowed_sources"):
        errors.append("manifest: missing allowed_sources")

    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("manifest: sources must be a non-empty list")
        return errors

    seen = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"sources[{index}]: source must be an object")
            continue
        source_id = source.get("source_id")
        if source_id in seen:
            errors.append(f"{source_id}: duplicate source_id")
        if source_id:
            seen.add(source_id)
        errors.extend(validate_source(source, index))

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to custom-source manifest JSON.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        manifest = load_manifest(args.manifest)
    except json.JSONDecodeError as exc:
        print(f"{args.manifest}: invalid JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)

    errors = validate_manifest(manifest)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)

    print(f"Custom source manifest valid: {args.manifest}")


if __name__ == "__main__":
    main()
