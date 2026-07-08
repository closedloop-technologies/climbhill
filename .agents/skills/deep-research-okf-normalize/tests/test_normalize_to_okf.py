import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.normalize_to_okf import normalize
from scripts.validate_okf import validate_bundle


class Args:
    input = None
    text = (
        "# Summary\n"
        "- OpenAI and Perplexity expose deep research-style APIs. https://example.com/source\n"
        "- This estimate may be stale and should be verified before publication.\n"
    )
    bundle_dir = None
    title = "Deepresearch the deepresearchers"
    provider = "test"
    prompt = "Find current deep research APIs."


def test_normalize_creates_okf_bundle(tmp_path: Path):
    args = Args()
    args.bundle_dir = str(tmp_path / "bundle")

    bundle_dir = normalize(args)

    assert (bundle_dir / "index.md").exists()
    assert (bundle_dir / "report.md").read_text(encoding="utf-8").startswith("---\ntype:")
    assert "https://example.com/source" in (bundle_dir / "findings.md").read_text(encoding="utf-8")
    assert "may be stale" in (bundle_dir / "uncertainties.md").read_text(encoding="utf-8")
    assert validate_bundle(bundle_dir) == []


def test_validate_bundle_reports_missing_type(tmp_path: Path):
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    for name in ["index.md", "log.md", "findings.md", "uncertainties.md", "method.md"]:
        (bundle_dir / name).write_text("# Placeholder\n", encoding="utf-8")
    (bundle_dir / "report.md").write_text("---\ntitle: Missing type\n---\n\n# Report\n", encoding="utf-8")

    errors = validate_bundle(bundle_dir)

    assert any("missing non-empty type" in error for error in errors)


def test_validate_bundle_rejects_symlinked_markdown_files(tmp_path: Path):
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    for name in [
        "index.md",
        "log.md",
        "report.md",
        "findings.md",
        "uncertainties.md",
        "method.md",
    ]:
        (bundle_dir / name).write_text(
            "---\ntype: concept\n---\n\n# Placeholder\n",
            encoding="utf-8",
        )
    outside_file = tmp_path / "outside.md"
    outside_file.write_text("---\ntype: external\n---\n\n# External\n", encoding="utf-8")
    (bundle_dir / "external.md").symlink_to(outside_file)

    errors = validate_bundle(bundle_dir)

    assert any("markdown file must not be a symlink" in error for error in errors)
