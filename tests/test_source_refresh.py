from datetime import date
from math import inf

import pytest

from awesome_deep_research import source_refresh


def test_parse_source_entries_reads_skill_rows():
    text = """# Provider Source Index

| Skill | Source |
| --- | --- |
| `deep-research-openai` | https://example.com/openai |
| `deep-research-okf-normalize` | docs/okf-normalization.md |
"""

    entries = source_refresh.parse_source_entries(text)

    assert [entry.skill for entry in entries] == [
        "deep-research-openai",
        "deep-research-okf-normalize",
    ]
    assert entries[1].source == "docs/okf-normalization.md"


def test_parse_refreshed_date_reads_iso_date():
    assert source_refresh.parse_refreshed_date("Last refreshed: 2026-06-23.") == date(
        2026, 6, 23
    )


def test_parse_refreshed_date_rejects_invalid_iso_date():
    assert source_refresh.parse_refreshed_date("Last refreshed: 2026-99-99.") is None


def test_source_index_checker_passes_current_index():
    results = source_refresh.check_source_index(today=date(2026, 6, 23))

    assert results
    assert all(result.ok for result in results), source_refresh.format_results(results)


def test_source_index_checker_uses_selected_index_parent_for_expected_skills(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert all(result.ok for result in results), source_refresh.format_results(results)


def test_source_index_checker_requires_canonical_table_header(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Name | Source |
| --- | --- |
| `example-skill` | https://example.com |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "source index table must include Skill and Source header" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_link_checker_resolves_local_paths_from_selected_index_repo_root(tmp_path):
    skills_root = tmp_path / "skills"
    docs_root = tmp_path / "docs"
    (skills_root / "example-skill").mkdir(parents=True)
    docs_root.mkdir()
    (docs_root / "source.md").write_text("source", encoding="utf-8")
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_links(index_path)

    assert all(result.ok for result in results), source_refresh.format_results(results)


def test_link_checker_resolves_local_paths_with_fragments(tmp_path):
    skills_root = tmp_path / "skills"
    docs_root = tmp_path / "docs"
    (skills_root / "example-skill").mkdir(parents=True)
    docs_root.mkdir()
    (docs_root / "source.md").write_text("# Heading\n", encoding="utf-8")
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs/source.md#heading |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_links(index_path)

    assert all(result.ok for result in results), source_refresh.format_results(results)


def test_source_index_checker_fails_duplicate_skill_rows(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com |
| `example-skill` | https://example.com |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "duplicate source index rows: example-skill -> https://example.com"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_duplicate_sources_across_skills(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    (skills_root / "other-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com |
| `other-skill` | https://example.com |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "duplicate source index sources: https://example.com" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_unknown_skill_rows(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com |
| `example-skil` | https://example.com/typo |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "unknown source index skills: example-skil" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_invalid_skill_row_names(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `Example Skill` | https://example.com |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "Example Skill: skill name must be lowercase hyphen-case" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_untrimmed_skill_row_names(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| ` example-skill ` | https://example.com |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and " example-skill : skill name must be lowercase hyphen-case" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_invalid_skill_directory_names(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example_skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example_skill` | https://example.com |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "skill directories must be lowercase hyphen-case: example_skill" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_normalized_skill_directory_collisions(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    (skills_root / "Example Skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com |
| `Example Skill` | https://example.com/other |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "skill directories collide after normalization: example-skill" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_blank_skill_rows(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `` | https://example.com |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "source index row has a blank skill name" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_blank_source_rows(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` |   |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "example-skill: source must be non-empty" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_unsupported_source_schemes(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | ftp://example.com/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: ftp://example.com/source.md has unsupported URL scheme"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_http_urls_without_hosts(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https:///source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "example-skill: https:///source.md must include a host" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_invalid_bracketed_remote_urls(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://[::1/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: https://[::1/source.md must be a valid URL" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_plain_http_sources(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | http://example.com/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "example-skill: http://example.com/source.md must use HTTPS"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_sources_with_embedded_credentials(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://user:token@example.com/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://user:token@example.com/source.md "
            "must not include credentials"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_https_hosts_with_trailing_dots(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com./source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: https://example.com./source.md host must not end with a dot"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_percent_encoded_hosts(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example%2ecom/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: https://example%2ecom/source.md host must not contain percent encoding"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_invalid_dns_hosts(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)

    for source in (
        "https://example_com/source.md",
        "https://localhost/source.md",
        "https://example.123/source.md",
        "https://-example.com/source.md",
        "https://example-.com/source.md",
    ):
        index_path = skills_root / "provider-source-index.md"
        index_path.write_text(
            f"""# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | {source} |
""",
            encoding="utf-8",
        )

        results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

        assert any(
            not result.ok
            and f"{source} host must be a valid DNS name or IP address" in result.message
            for result in results
        ), source_refresh.format_results(results)


@pytest.mark.parametrize(
    "source",
    [
        "https://example.com:bad/source.md",
        "https://example.com:0/source.md",
        "https://example.com:/source.md",
    ],
)
def test_source_index_checker_fails_malformed_remote_ports(tmp_path, source):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        f"""# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | {source} |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            f"example-skill: {source} URL port must be numeric and in range"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_non_global_ip_hosts(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://192.0.2.10/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://192.0.2.10/source.md "
            "IP host must be globally routable"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_parent_directory_paths(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/%2e%2e/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/%2e%2e/source.md "
            "URL path must not contain parent directory references"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_current_directory_paths(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/%2e/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/%2e/source.md "
            "URL path must not contain current directory references"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_encoded_path_separators(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/docs%5Csource.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/docs%5Csource.md "
            "URL path must not encode path separators"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_nested_encoded_path_separators(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/docs%252Fsource.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/docs%252Fsource.md "
            "URL path must not encode path separators"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_encoded_query_fragment_markers(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/docs%23source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/docs%23source.md "
            "URL path must not encode query or fragment markers"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_nested_encoded_query_fragment_markers(
    tmp_path,
):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/docs%2523source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/docs%2523source.md "
            "URL path must not encode query or fragment markers"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_encoded_path_aliases(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/source%41.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/source%41.md "
            "URL path must not contain percent-encoded aliases"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_backslash_path_separators(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/docs\\source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/docs\\source.md "
            "URL must use forward slashes"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_backslash_authorities(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com\\source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com\\source.md "
            "URL must use forward slashes"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_remote_repeated_path_separators(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/docs//source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/docs//source.md "
            "URL path must not contain repeated separators"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_encoded_control_characters(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs/source%00.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: docs/source%00.md must not contain encoded control characters"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_sources_with_whitespace(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/bad path |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: https://example.com/bad path must not contain whitespace"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_sources_with_encoded_whitespace(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/bad%20path |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: https://example.com/bad%20path must not contain encoded whitespace"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_sources_with_malformed_percent_encoding(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com/bad%zzpath |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: https://example.com/bad%zzpath "
            "must not contain malformed percent encoding"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_link_checker_rejects_remote_encoded_path_aliases_before_http(monkeypatch):
    def fail_get(*args, **kwargs):
        raise AssertionError("HTTP should not be requested for encoded path aliases")

    monkeypatch.setattr(source_refresh.requests, "get", fail_get)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/%68elp"),
    )

    assert not result.ok
    assert (
        result.message
        == "example-skill: https://example.com/%68elp URL path must not contain percent-encoded aliases"
    )


def test_source_index_checker_fails_absolute_local_source_paths(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    absolute_source = tmp_path / "docs" / "source.md"
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        f"""# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | {absolute_source} |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and f"example-skill: {absolute_source} must be repo-relative" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_parent_directory_source_paths(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | ../docs/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: ../docs/source.md must not contain parent directory references"
            in result.message
        )
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_encoded_parent_directory_source_paths(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | %2e%2e/docs/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: %2e%2e/docs/source.md must not contain parent directory references"
            in result.message
        )
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_encoded_current_directory_source_paths(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | %2e/docs/source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: %2e/docs/source.md must not contain current directory references"
            in result.message
        )
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_source_paths_with_queries(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs/source.md?download=1 |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: docs/source.md?download=1 "
            "local source must not include query parameters"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_fragment_only_sources(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | #heading |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "example-skill: #heading local source must include a path"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_source_paths_with_backslashes(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs\\source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: docs\\source.md local source must use forward slashes"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_source_paths_with_encoded_slashes(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs%2Fsource.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: docs%2Fsource.md local source must not encode path separators"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_source_paths_with_nested_encoded_slashes(
    tmp_path,
):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs%252Fsource.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and "example-skill: docs%252Fsource.md local source must not encode path separators"
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_source_paths_with_encoded_markers(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs/source%3Fdownload.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: docs/source%3Fdownload.md "
            "local source must not encode query or fragment markers"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_source_paths_with_nested_encoded_markers(
    tmp_path,
):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs/source%253Fdownload.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: docs/source%253Fdownload.md "
            "local source must not encode query or fragment markers"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_source_paths_with_encoded_aliases(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs/sourc%65.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: docs/sourc%65.md "
            "local source must not contain percent-encoded aliases"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_source_paths_with_malformed_percent_encoding(
    tmp_path,
):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs/source%.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: docs/source%.md "
            "must not contain malformed percent encoding"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_local_source_paths_with_repeated_separators(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-23.

| Skill | Source |
| --- | --- |
| `example-skill` | docs//source.md |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok
        and (
            "example-skill: docs//source.md "
            "local source must not contain repeated separators"
        )
        in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_source_index_checker_fails_stale_index():
    results = source_refresh.check_source_index(max_age_days=30, today=date(2026, 8, 1))

    assert any(not result.ok and "Last refreshed" in result.message for result in results)


def test_source_index_checker_rejects_negative_max_age_days():
    results = source_refresh.check_source_index(
        max_age_days=-1,
        today=date(2026, 6, 23),
    )

    assert results == [
        source_refresh.CheckResult(False, "max_age_days must be a non-negative integer")
    ]


def test_source_index_checker_rejects_non_integer_max_age_days():
    results = source_refresh.check_source_index(
        max_age_days=True,
        today=date(2026, 6, 23),
    )

    assert results == [
        source_refresh.CheckResult(False, "max_age_days must be a non-negative integer")
    ]


def test_source_index_checker_fails_future_refresh_dates(tmp_path):
    skills_root = tmp_path / "skills"
    (skills_root / "example-skill").mkdir(parents=True)
    index_path = skills_root / "provider-source-index.md"
    index_path.write_text(
        """# Provider Source Index

Last refreshed: 2026-06-24.

| Skill | Source |
| --- | --- |
| `example-skill` | https://example.com |
""",
        encoding="utf-8",
    )

    results = source_refresh.check_source_index(index_path, today=date(2026, 6, 23))

    assert any(
        not result.ok and "Last refreshed 2026-06-24 is in the future" in result.message
        for result in results
    ), source_refresh.format_results(results)


def test_local_source_link_rejects_path_outside_repo(tmp_path):
    outside_doc = tmp_path.parent / "outside.md"
    outside_doc.write_text("outside", encoding="utf-8")

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "../outside.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain parent directory references" in result.message


def test_local_source_link_rejects_absolute_path_outside_repo(tmp_path):
    outside_doc = tmp_path.parent / "outside.md"
    outside_doc.write_text("outside", encoding="utf-8")

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", str(outside_doc.resolve())),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must be repo-relative" in result.message


def test_local_source_link_rejects_absolute_path_inside_repo(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    source = docs_dir / "source.md"
    source.write_text("source", encoding="utf-8")

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", str(source.resolve())),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must be repo-relative" in result.message


def test_local_source_link_rejects_encoded_parent_directory_sources(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "%2e%2e/outside.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain parent directory references" in result.message


def test_local_source_link_rejects_current_directory_sources(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "./docs/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain current directory references" in result.message


def test_local_source_link_rejects_encoded_current_directory_sources(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "%2e/docs/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain current directory references" in result.message


def test_local_source_link_rejects_repeated_path_separators(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs//source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not contain repeated separators" in result.message


def test_local_source_link_rejects_symlinked_files(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    target = docs_dir / "target.md"
    target.write_text("source", encoding="utf-8")
    (docs_dir / "source.md").symlink_to(target)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not contain symlinks" in result.message


def test_local_source_link_rejects_symlinked_directories(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    linked_dir = tmp_path / "linked-docs"
    linked_dir.symlink_to(docs_dir, target_is_directory=True)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "linked-docs/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not contain symlinks" in result.message


@pytest.mark.parametrize("source", ["docs/.source.md", ".docs/source.md"])
def test_local_source_link_rejects_hidden_path_components(tmp_path, source):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", source),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not contain hidden path components" in result.message


@pytest.mark.parametrize("source", ["docs/-source.md", "-docs/source.md"])
def test_local_source_link_rejects_flag_like_path_components(tmp_path, source):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", source),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not contain flag-like path components" in result.message


def test_source_link_rejects_unsupported_url_schemes(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "ftp://example.com/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "unsupported URL scheme" in result.message


def test_source_link_rejects_plain_http_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "http://example.com/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must use HTTPS" in result.message


def test_source_link_rejects_invalid_bracketed_urls_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://[::1/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must be a valid URL" in result.message


def test_source_link_rejects_invalid_timeout_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    for timeout in (0, -1, True, "10", inf):
        result = source_refresh.check_link(
            source_refresh.SourceEntry("example-skill", "https://example.com/source.md"),
            repo_root=tmp_path,
            timeout=timeout,
        )

        assert result == source_refresh.CheckResult(
            False,
            "timeout must be a positive number",
        )


def test_source_link_rejects_credentialed_urls_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://user:token@example.com/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not include credentials" in result.message


def test_source_link_rejects_trailing_dot_hosts_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com./source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "host must not end with a dot" in result.message


def test_source_link_rejects_percent_encoded_hosts_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example%2ecom/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "host must not contain percent encoding" in result.message


def test_source_link_rejects_invalid_dns_hosts_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    for source in (
        "https://example_com/source.md",
        "https://localhost/source.md",
        "https://example.123/source.md",
        "https://-example.com/source.md",
        "https://example-.com/source.md",
    ):
        result = source_refresh.check_link(
            source_refresh.SourceEntry("example-skill", source),
            repo_root=tmp_path,
        )

        assert result.ok is False
        assert "host must be a valid DNS name or IP address" in result.message


def test_source_link_rejects_malformed_remote_ports_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    for source in (
        "https://example.com:bad/source.md",
        "https://example.com:0/source.md",
    ):
        result = source_refresh.check_link(
            source_refresh.SourceEntry("example-skill", source),
            repo_root=tmp_path,
        )

        assert result.ok is False
        assert "URL port must be numeric and in range" in result.message


def test_source_link_rejects_non_global_ip_hosts_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    for source in (
        "https://10.0.0.1/source.md",
        "https://[2001:db8::1]/source.md",
    ):
        result = source_refresh.check_link(
            source_refresh.SourceEntry("example-skill", source),
            repo_root=tmp_path,
        )

        assert result.ok is False
        assert "IP host must be globally routable" in result.message


def test_source_link_rejects_remote_encoded_path_separators_before_request(
    monkeypatch, tmp_path
):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/docs%2Fsource.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "URL path must not encode path separators" in result.message


def test_source_link_rejects_remote_nested_encoded_path_separators_before_request(
    monkeypatch, tmp_path
):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/docs%252Fsource.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "URL path must not encode path separators" in result.message


def test_source_link_rejects_remote_encoded_query_markers_before_request(
    monkeypatch, tmp_path
):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/docs%3Fsource.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "URL path must not encode query or fragment markers" in result.message


def test_source_link_rejects_remote_nested_encoded_query_markers_before_request(
    monkeypatch, tmp_path
):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/docs%253Fsource.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "URL path must not encode query or fragment markers" in result.message


def test_source_link_rejects_remote_current_directory_paths_before_request(
    monkeypatch, tmp_path
):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/%2e/source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "URL path must not contain current directory references" in result.message


def test_source_link_rejects_whitespace_urls_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/bad path"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain whitespace" in result.message


def test_source_link_rejects_encoded_whitespace_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/bad%20path"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain encoded whitespace" in result.message


def test_source_link_rejects_malformed_percent_encoding_before_request(
    monkeypatch, tmp_path
):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/source%.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain malformed percent encoding" in result.message


def test_source_link_rejects_remote_backslash_paths_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/docs\\source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "URL must use forward slashes" in result.message


def test_source_link_rejects_remote_backslash_authorities_before_request(
    monkeypatch, tmp_path
):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com\\source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "URL must use forward slashes" in result.message


def test_source_link_rejects_remote_repeated_path_separators_before_request(
    monkeypatch, tmp_path
):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/docs//source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "URL path must not contain repeated separators" in result.message


def test_source_link_rejects_encoded_control_characters_before_request(monkeypatch, tmp_path):
    def fail_request(*_args, **_kwargs):
        raise AssertionError("HTTP request should not run")

    monkeypatch.setattr(source_refresh.requests, "get", fail_request)

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "https://example.com/source%7f.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain encoded control characters" in result.message


def test_local_source_link_rejects_directory_sources(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local path must be a file" in result.message


def test_local_source_link_rejects_fragment_only_sources(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "#heading"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must include a path" in result.message


def test_local_source_link_rejects_query_parameters(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "source.md").write_text("source", encoding="utf-8")

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs/source.md?download=1"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not include query parameters" in result.message


def test_local_source_link_rejects_backslashes(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs\\source.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must use forward slashes" in result.message


def test_local_source_link_rejects_encoded_path_separators(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs%5Csource.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not encode path separators" in result.message


def test_local_source_link_rejects_nested_encoded_path_separators(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs%255Csource.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not encode path separators" in result.message


def test_local_source_link_rejects_encoded_fragment_markers(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs/source%23heading.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not encode query or fragment markers" in result.message


def test_local_source_link_rejects_nested_encoded_fragment_markers(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs/source%2523heading.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not encode query or fragment markers" in result.message


def test_local_source_link_rejects_encoded_path_aliases(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "source.md").write_text("source", encoding="utf-8")

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs/sourc%65.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "local source must not contain percent-encoded aliases" in result.message


def test_local_source_link_rejects_encoded_whitespace(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "source file.md").write_text("source", encoding="utf-8")

    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs/source%20file.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain encoded whitespace" in result.message


def test_local_source_link_rejects_malformed_percent_encoding(tmp_path):
    result = source_refresh.check_link(
        source_refresh.SourceEntry("example-skill", "docs/source%.md"),
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert "must not contain malformed percent encoding" in result.message
