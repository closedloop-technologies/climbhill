# Testing

Current checks for this transitional repository:

```bash
pytest tests/test_cli.py
git diff --check
```

For landing page changes, also run a local static server and verify the page and hero asset load:

```bash
python -m http.server 8000
curl -I http://127.0.0.1:8000/
curl -I http://127.0.0.1:8000/assets/hero-research-harness.png
```

When Chrome is available, capture representative screenshots:

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --window-size=1440,1000 \
  --screenshot=/tmp/climbhill-desktop.png \
  http://127.0.0.1:8000/

google-chrome --headless=new --no-sandbox --disable-gpu \
  --window-size=320,844 \
  --screenshot=/tmp/climbhill-mobile.png \
  http://127.0.0.1:8000/
```

Future ClimbHill implementation work should add tests for:

- Policy path matching and protected-surface checks.
- SQLite registry migrations and data integrity.
- MCP tool request and response schemas.
- CLI init, inspect, align, report, and reflect commands.
- Markdown report generation.
- Historical sampling and candidate comparison logic.
