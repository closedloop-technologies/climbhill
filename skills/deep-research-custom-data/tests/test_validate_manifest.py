import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_manifest import (
    has_valid_hostname_syntax,
    is_safe_http_url,
    is_safe_relative_path,
    validate_manifest,
)


def valid_manifest():
    return {
        "corpus_id": "demo",
        "research_question": "What does the private corpus say?",
        "allowed_sources": ["gdoc-1", "yt-1", "local-1", "s3-1", "arxiv-1"],
        "sources": [
            {
                "source_id": "gdoc-1",
                "source_type": "google_drive",
                "title": "Notes",
                "citation_anchor": "file ID plus heading",
                "file_id": "1abc",
                "web_url": "https://docs.google.com/document/d/1abc",
                "modified_time": "2026-06-23T00:00:00Z",
            },
            {
                "source_id": "yt-1",
                "source_type": "youtube",
                "title": "Interview",
                "citation_anchor": "video timestamp",
                "video_id": "abc123",
                "url": "https://www.youtube.com/watch?v=abc123",
                "published_at": "2026-01-01",
            },
            {
                "source_id": "local-1",
                "source_type": "local_file",
                "title": "Report",
                "citation_anchor": "path and page",
                "path": "docs/report.pdf",
                "sha256": "abc",
                "modified_time": "2026-01-01T00:00:00Z",
            },
            {
                "source_id": "s3-1",
                "source_type": "s3",
                "title": "Object",
                "citation_anchor": "bucket key and etag",
                "bucket": "bucket",
                "key": "prefix/object.json",
                "etag": "abc",
            },
            {
                "source_id": "arxiv-1",
                "source_type": "arxiv",
                "title": "Paper",
                "citation_anchor": "arXiv version and page",
                "arxiv_id": "2401.01234",
                "version": "v2",
                "pdf_url": "https://arxiv.org/pdf/2401.01234v2",
            },
        ],
    }


def test_valid_manifest_passes():
    assert validate_manifest(valid_manifest()) == []


def test_missing_citation_anchor_fails():
    manifest = valid_manifest()
    del manifest["sources"][0]["citation_anchor"]

    errors = validate_manifest(manifest)

    assert any("missing required field citation_anchor" in error for error in errors)


def test_unsupported_source_type_fails():
    manifest = valid_manifest()
    manifest["sources"][0]["source_type"] = "unsupported"

    errors = validate_manifest(manifest)

    assert any("unsupported source_type" in error for error in errors)


def test_safe_relative_path_rejects_absolute_and_dot_segments():
    assert is_safe_relative_path("docs/report.pdf") is True
    assert is_safe_relative_path("/docs/report.pdf") is False
    assert is_safe_relative_path("../report.pdf") is False
    assert is_safe_relative_path("docs/../report.pdf") is False
    assert is_safe_relative_path("./report.pdf") is False
    assert is_safe_relative_path("docs\\report.pdf") is False
    assert is_safe_relative_path("docs/my report.pdf") is False
    assert is_safe_relative_path("docs/report\tcopy.pdf") is False
    assert is_safe_relative_path("docs/report\x7f.pdf") is False
    assert is_safe_relative_path("docs/report.pdf?download=1") is False
    assert is_safe_relative_path("docs/report.pdf#page=2") is False
    assert is_safe_relative_path("docs/%2e%2e/report.pdf") is False
    assert is_safe_relative_path("docs/%252e%252e/report.pdf") is False
    assert is_safe_relative_path("docs%2freport.pdf") is False
    assert is_safe_relative_path("docs%5creport.pdf") is False
    assert is_safe_relative_path("docs/report%3fdownload.pdf") is False
    assert is_safe_relative_path("docs/report%253fdownload.pdf") is False
    assert is_safe_relative_path("docs/report%23page.pdf") is False
    assert is_safe_relative_path("docs/report%2523page.pdf") is False
    assert is_safe_relative_path("docs/report%2epdf") is False
    assert is_safe_relative_path("docs/report%zz.pdf") is False


def test_safe_http_url_requires_absolute_http_url_without_credentials():
    assert is_safe_http_url("https://example.com/report") is True
    assert is_safe_http_url("http://example.com/report") is True
    assert is_safe_http_url("example.com/report") is False
    assert is_safe_http_url("ftp://example.com/report") is False
    assert is_safe_http_url("https:///report") is False
    assert is_safe_http_url("https://user:token@example.com/report") is False
    assert is_safe_http_url("https://example.com/report\nnext") is False
    assert is_safe_http_url("https://example.com/bad%20path") is False
    assert is_safe_http_url("https://example.com/search?q=bad%2520path") is False
    assert is_safe_http_url("https://example.com/bad%7fpath") is False
    assert is_safe_http_url("https://example.com/search?q=%2500") is False
    assert is_safe_http_url("https://example.com/report%2epdf") is False
    assert is_safe_http_url("https://example.com/reports%2f2026") is False
    assert is_safe_http_url("https://example.com/bad%zzpath") is False
    assert is_safe_http_url("https://example.com:bad/report") is False
    assert is_safe_http_url("https://localhost/report") is False
    assert is_safe_http_url("https://127.0.0.1/report") is False
    assert is_safe_http_url("https://2130706433/report") is False
    assert is_safe_http_url("https://0x7f000001/report") is False
    assert is_safe_http_url("https://017700000001/report") is False
    assert is_safe_http_url("https://127.1/report") is False
    assert is_safe_http_url("https://10.0.0.5/report") is False
    assert is_safe_http_url("https://172.16.0.5/report") is False
    assert is_safe_http_url("https://192.168.1.5/report") is False
    assert is_safe_http_url("https://[fd00::1]/report") is False
    assert is_safe_http_url("https://[64:ff9b::7f00:1]/report") is False
    assert is_safe_http_url("https://[64:ff9b::a00:5]/report") is False
    assert is_safe_http_url("https://[64:ff9b::c0a8:105]/report") is False
    assert is_safe_http_url("https://[64:ff9b::808:808]/report") is True
    assert is_safe_http_url("https://example.com./report") is False
    assert is_safe_http_url("https://%65xample.com/report") is False
    assert is_safe_http_url("https://bad_host.example/report") is False
    assert is_safe_http_url("https://-bad.example/report") is False
    assert is_safe_http_url("https://bad-.example/report") is False
    assert is_safe_http_url("https://bad..example/report") is False
    assert is_safe_http_url("https://example/report") is False
    assert is_safe_http_url("https://example.123/report") is False
    assert is_safe_http_url(" https://example.com/report") is False


def test_has_valid_hostname_syntax_accepts_domains_and_ip_literals():
    assert has_valid_hostname_syntax("example.com")
    assert has_valid_hostname_syntax("docs.example-1.com")
    assert has_valid_hostname_syntax("8.8.8.8")
    assert has_valid_hostname_syntax("2001:4860:4860::8888")


def test_has_valid_hostname_syntax_rejects_malformed_dns_labels():
    assert has_valid_hostname_syntax("bad_host.example") is False
    assert has_valid_hostname_syntax("-bad.example") is False
    assert has_valid_hostname_syntax("bad-.example") is False
    assert has_valid_hostname_syntax("bad..example") is False
    assert has_valid_hostname_syntax("example") is False
    assert has_valid_hostname_syntax("example.123") is False


def test_local_and_csv_paths_must_be_safe_relative_paths():
    manifest = valid_manifest()
    manifest["sources"][2]["path"] = "../private/report.pdf"
    manifest["sources"].append(
        {
            "source_id": "csv-1",
            "source_type": "csv",
            "title": "Rows",
            "citation_anchor": "row id",
            "path": "/tmp/export.csv",
            "sha256": "abc",
            "schema": {"id": "string"},
        }
    )

    errors = validate_manifest(manifest)

    assert any("local-1: path must be a safe relative path" in error for error in errors)
    assert any("csv-1: path must be a safe relative path" in error for error in errors)


def test_s3_key_must_be_safe_relative_path():
    manifest = valid_manifest()
    manifest["sources"][3]["key"] = "exports/../private.json"

    errors = validate_manifest(manifest)

    assert any("s3-1: key must be a safe relative path" in error for error in errors)


def test_manifest_paths_reject_backslashes_and_control_characters():
    manifest = valid_manifest()
    manifest["sources"][2]["path"] = "docs\\report.pdf"
    manifest["sources"][3]["key"] = "prefix/object\x7f.json"

    errors = validate_manifest(manifest)

    assert any("local-1: path must be a safe relative path" in error for error in errors)
    assert any("s3-1: key must be a safe relative path" in error for error in errors)


def test_manifest_paths_reject_raw_whitespace():
    manifest = valid_manifest()
    manifest["sources"][2]["path"] = "docs/private report.pdf"
    manifest["sources"][3]["key"] = "prefix/object copy.json"
    manifest["sources"].append(
        {
            "source_id": "csv-1",
            "source_type": "csv",
            "title": "Rows",
            "citation_anchor": "row id",
            "path": "exports/rows\tcopy.csv",
            "sha256": "abc",
            "schema": {"id": "string"},
        }
    )

    errors = validate_manifest(manifest)

    assert any("local-1: path must be a safe relative path" in error for error in errors)
    assert any("s3-1: key must be a safe relative path" in error for error in errors)
    assert any("csv-1: path must be a safe relative path" in error for error in errors)


def test_manifest_paths_reject_encoded_traversal_and_separators():
    manifest = valid_manifest()
    manifest["sources"][2]["path"] = "docs/%2e%2e/report.pdf"
    manifest["sources"][3]["key"] = "prefix%2fobject.json"

    errors = validate_manifest(manifest)

    assert any("local-1: path must be a safe relative path" in error for error in errors)
    assert any("s3-1: key must be a safe relative path" in error for error in errors)


def test_url_fields_must_be_absolute_http_urls():
    manifest = valid_manifest()
    manifest["sources"][0]["web_url"] = "docs.google.com/document/d/1abc"
    manifest["sources"][1]["url"] = "https://user:token@youtube.com/watch?v=abc123"
    manifest["sources"][4]["pdf_url"] = "file:///tmp/paper.pdf"
    manifest["sources"].append(
        {
            "source_id": "ticket-1",
            "source_type": "ticket",
            "title": "Bug",
            "citation_anchor": "ticket id",
            "system": "jira",
            "ticket_id": "BUG-1",
            "url": "https://tickets.example.com/browse/BUG-1\x7f",
        }
    )

    errors = validate_manifest(manifest)

    assert any("gdoc-1: web_url must be an absolute http(s) URL" in error for error in errors)
    assert any("yt-1: url must be an absolute http(s) URL" in error for error in errors)
    assert any("arxiv-1: pdf_url must be an absolute http(s) URL" in error for error in errors)
    assert any("ticket-1: url must be an absolute http(s) URL" in error for error in errors)
