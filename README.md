# Privacy Budget Accountant Laplace

A local Laplace-mechanism demonstrator with session-scoped epsilon accounting, accompanied by the repository's existing Python task-audit service.

## What works

The **browser calculator** in [`web/index.html`](web/index.html) runs without a server or Python. It adds Laplace noise to a numeric query result you supply, tracks a fixed epsilon budget across releases in the current tab, rejects over-budget releases, and exports only the noisy results as CSV. Randomness comes from the browser's Web Crypto API; the app uses no external resources, network requests, cookies or persistent storage.

The **Python accountant** (`dp_laplace_budget.accountant`) provides:
- `PrivacyBudget(total_epsilon)` with basic sequential epsilon composition (pure DP, delta = 0)
- `laplace_noise(scale)` with OS-backed random sampling
- Global sensitivity helpers for unweighted counts and fixed-size, bounded means
- Validation of finite parameters and rejection of releases that exceed the budget

The existing `agents/` task-audit system remains available via the main CLI and FastAPI. It evaluates configurable-style **legacy thresholds**, records a process-local HMAC audit trail, and applies basic regex screening to select identifier formats. That audit system is distinct from the Laplace privacy accountant and is **not** an automated privacy/compliance certification system.

## Browser usage

Open `web/index.html` in a modern browser, or use the repository's GitHub Pages deployment if enabled. Set the total epsilon budget, select a count or bounded-mean query, supply its exact numeric result and epsilon allocation, and generate a noisy release. The table shows each disclosure and budget expenditure.

The sensitivity conventions are:

| Query | Neighboring datasets | Global sensitivity |
| --- | --- | --- |
| Unweighted count | Add or remove one record | 1 |
| Mean of `n` bounded values in `[lower, upper]` | Replace one record with dataset size fixed at `n` | `(upper - lower) / n` |

Noise is sampled from `Laplace(0, sensitivity / epsilon)`. Under **basic sequential composition**, epsilons of multiple releases are added.

**Privacy limitation:** These formulas only apply when the sensitivity, dataset bounds, neighboring-dataset relation and query design are correct. The calculator accepts an already-computed exact answer and does not inspect the underlying dataset. A new tab, browser session or CLI invocation creates a **new independent ledger**, not a legitimate reset of a real dataset's previously consumed privacy budget. Neither the browser nor the Python demo provides durable, cross-user or distributed budget enforcement. Do not use them as a production data-release gate or assume that differential privacy alone establishes HIPAA/GDPR compliance.

## Install and run Python

Requires Python 3.10 or newer.

```bash
git clone https://github.com/abusuraihsakhri/privacy-budget-accountant-laplace.git
cd privacy-budget-accountant-laplace
python -m pip install -e ".[server,test]"

# One session-local Laplace disclosure; outputs JSON
python cli.py laplace --total-epsilon 1 --epsilon 0.2 --value 25 --sensitivity 1

# Existing legacy audit workflow
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit

# Local API and browser interface at http://127.0.0.1:8000/
python cli.py serve --host 127.0.0.1 --port 8000
```

The older DP audit entry point also remains available: `dp-laplace-budget audit`. It performs legacy threshold triage; it does not generate Laplace noise. The default installed `privacy-budget-accountant-laplace` command maps to the main `cli.py`.

## API

The optional FastAPI server exposes `GET /` (browser demo), `GET /health`, `GET /metrics`, `POST /api/audit`, `POST /api/chat`, and `GET /api/audit/logs`. These endpoints belong to the legacy task-audit service. There is no persistent epsilon-ledger API.

For container usage, set a strong secret in `AUDIT_SECRET_KEY`, then run `docker compose up --build` or build and run the Docker image directly. Do not publicly expose the audit API or logs without your own access controls.

## Security and privacy notes

- The browser demo keeps entries in memory and does not communicate with a server. Its CSV export includes noisy results and epsilon metadata, not exact inputs.
- The HMAC audit trail verifies individual signatures and their chain links. Logs are in-memory and not durable across restarts. When `AUDIT_SECRET_KEY` is absent, a random ephemeral development key is used with a warning; configure a strong stable key for controlled deployments.
- Regex identifier checks are incomplete and do **not** ensure all protected health information has been detected or de-identified.
- The mock supervisory chat does not provide independent scientific verification; other model-provider labels currently resolve to the same mock implementation.
- The enrichment modules (`enrichment.py`) are threshold-based placeholders, **not** implementations of RDP, Byzantine resilience, budget recycling or compliance checks.

## Tests

```bash
python -m pytest -q
node --check web/app.js
node --test tests/laplace_web.test.cjs
```

The GitHub Actions workflow runs Python tests across supported interpreters and checks the static JavaScript. This repository also contains a separate Pages workflow for publishing `web/`; its live status depends on the repository's GitHub Pages configuration.

## Technology and license

Python standard library (Laplace accountant), Pydantic 2 / FastAPI (legacy audit API), and vanilla browser JavaScript/HTML/CSS (static demo). Browser features require Web Crypto API and modern JavaScript support. Licensed under [MIT](LICENSE).
