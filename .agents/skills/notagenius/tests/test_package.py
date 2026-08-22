from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE = REPO_ROOT / ".agents" / "skills" / "notagenius"
MIRROR = REPO_ROOT / "skills" / "notagenius"
PACKAGE_FILES = (
    "SKILL.md",
    "references/PLAYBOOK.md",
    "references/PLAN.md",
)


def test_package_has_one_portable_playbook_and_one_climbhill_adapter() -> None:
    skill = (SOURCE / "SKILL.md").read_text()
    playbook = (SOURCE / "references" / "PLAYBOOK.md").read_text()
    plan = (SOURCE / "references" / "PLAN.md").read_text()

    assert "references/PLAYBOOK.md" in skill
    assert "references/PLAN.md" in skill
    assert "ClimbHill" not in playbook
    assert "ClimbHill" in plan


def test_plan_preserves_climbhill_control_semantics() -> None:
    plan = (SOURCE / "references" / "PLAN.md").read_text()

    assert "attempt | evaluate | promote | spawn_run | stop" in plan
    assert "authorization" in plan
    assert "eligibility" in plan
    assert "atomic" in plan
    assert "Evidence Snapshot" in plan


def test_plugin_mirror_matches_canonical_skill() -> None:
    for relative_path in PACKAGE_FILES:
        assert (MIRROR / relative_path).read_bytes() == (
            SOURCE / relative_path
        ).read_bytes()
