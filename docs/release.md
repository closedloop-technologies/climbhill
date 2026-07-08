# Release Runbook

This repo ships three public surfaces:

- `https://climbhill.ai/` through GitHub Pages.
- `climbhill-ai` on PyPI.
- A Codex plugin and portable skills under `.codex-plugin/`, `.mcp.json`, and `skills/`.

## Preflight

Run these checks before creating a release:

```bash
git status --short
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
pytest
python3 /home/gibson/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
python3 /home/gibson/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugin/climbhill-ai
climbhill --help
climbhill-mcp-smoke
```

## PyPI

PyPI publishing uses GitHub Trusted Publishing. Configure PyPI with:

- Project name: `climbhill-ai`
- Owner/repository: `closedloop-technologies/climbhill`
- Workflow: `publish.yml`
- Environment: `pypi`

Create a GitHub release to publish:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Then create a GitHub Release for the tag. The release triggers `.github/workflows/publish.yml`, builds `dist/`, checks the artifacts with Twine, and publishes with `pypa/gh-action-pypi-publish`.

Verify the package after the workflow completes:

```bash
python -m pip install --upgrade climbhill-ai
climbhill --help
climbhill-mcp-smoke
```

## GitHub Pages

The Pages workflow deploys on every push to `main`. DNS for `climbhill.ai` should point the apex domain at GitHub Pages and `www` at the organization Pages domain:

```text
A     @     185.199.108.153
A     @     185.199.109.153
A     @     185.199.110.153
A     @     185.199.111.153
AAAA  @     2606:50c0:8000::153
AAAA  @     2606:50c0:8001::153
AAAA  @     2606:50c0:8002::153
AAAA  @     2606:50c0:8003::153
CNAME www   closedloop-technologies.github.io
```

Verify DNS:

```bash
dig climbhill.ai +noall +answer -t A
dig climbhill.ai +noall +answer -t AAAA
dig www.climbhill.ai +noall +answer
```

Enable `Enforce HTTPS` in GitHub Pages once the certificate is available.

## Codex Plugin And Skills

Validate the root plugin and standalone plugin package:

```bash
python3 /home/gibson/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
python3 /home/gibson/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugin/climbhill-ai
```

Use these install paths after the repository rename has propagated:

```text
/plugins marketplace add closedloop-technologies/climbhill
npx skills add closedloop-technologies/climbhill
```

Keep `skills/` and `.agents/skills/` mirrored until the package is split into dedicated single-skill repositories.
