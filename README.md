# Privacy Budget Accountant Laplace

> **Domain:** Privacy-Preserving Healthcare & Federated Computing
> **Reference Guidelines & Standards:** `HIPAA Safe Harbor §164.514 & Differential Privacy RDP`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Privacy Budget Accountant Laplace** is an advanced analytical and computational platform implementing Global sensitivity & calibrated Laplace noise differential privacy budget manager. It provides:

- Multi-agent consensus evaluation with specialized workers for QC, safety, and protocol conformance
- Zero-PHI outbound protection with pattern-based detection and redaction
- Tamper-evident HMAC-SHA256 audit trail for all operations
- Input validation and bounds checking to prevent abuse
- REST API with FastAPI for integration with external systems

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization (ROUTINE, ELEVATED_RISK, CRITICAL_STAT_PANIC) with automated action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking, length limits, and character validation to prevent injection attacks.
- **PHI Protection**: Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOBs, and patient identifiers.

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/privacy-budget-accountant-laplace.git
cd privacy-budget-accountant-laplace

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## 🚀 CLI Quickstart & Usage

### 1. Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. System Chat Query
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task identifier (alphanumeric, hyphens, underscores only)
- `--target`: Target entity identifier
- `--primary`: Primary metric value (float)
- `--secondary`: Secondary metric value (float)
- `--critical`: Flag for critical priority
- `--status`: Status descriptor (NOMINAL, DISCORDANT, ANOMALY, etc.)

### Input Data Schema (CSV Batch Mode)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task identifier | Required |
| `target_identifier` | Target entity identifier | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary measurement value | Optional |
| `is_critical_flag` | Critical flag (true/false) | Optional |
| `status_descriptor` | Status descriptor | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOBs, and patient identifiers. Raises `SecurityException` on violation.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Input Validation:** Strict bounds checking on all inputs including length limits, character whitelisting, and numeric range validation.
* **Path Traversal Protection:** Batch mode validates file paths to prevent directory traversal attacks.

### Security Configuration

**IMPORTANT:** Set the `AUDIT_SECRET_KEY` environment variable in production:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key-here"

# Windows
set AUDIT_SECRET_KEY=your-secure-random-key-here
```

If not set, the system will emit a runtime warning and use a development-only fallback key.

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus-compatible metrics |
| POST | `/api/audit` | Submit task for evaluation |
| POST | `/api/chat` | Query system status |
| GET | `/api/audit/logs` | Get audit trail |

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

### Test Coverage
- PHI guard enforcement (9 tests)
- Input validation (8 tests)
- Audit trail security (5 tests)
- CLI error handling (3 tests)
- Core functionality (9 tests)

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t privacy-budget-accountant-laplace .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secure-key privacy-budget-accountant-laplace

# Or use docker-compose
AUDIT_SECRET_KEY=your-secure-key docker-compose up
```

**Note:** Always set a secure `AUDIT_SECRET_KEY` when deploying to production.

---

## 📁 Project Structure

```
privacy-budget-accountant-laplace/
├── agents/                  # Enterprise agent system (v3.0.0-ENTERPRISE)
│   ├── __init__.py
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # PHI guard, audit trail, security
│   ├── learning.py         # Bayesian calibration engine
│   ├── llm_factory.py      # LLM provider abstraction
│   ├── metrics.py          # Prometheus metrics exporter
│   ├── models.py           # Pydantic data models with validation
│   ├── streamer.py         # WebSocket telemetry broadcaster
│   ├── supervisor.py       # Master orchestrator
│   └── workers.py          # Specialized domain workers
├── dp_laplace_budget/       # DP-Laplace budget engine (v2.0.0-FRONTIER)
│   ├── __init__.py
│   ├── agents.py           # Distributed component coordination
│   ├── cli.py              # CLI for DP-Laplace module
│   ├── engine.py           # Core algorithmic engine
│   ├── models.py           # Data models
│   └── server.py           # FastAPI server for DP-Laplace
├── tests/                   # Test suite
│   ├── test_privacy_budget_accountant_laplace.py
│   ├── test_dp_laplace_budget.py
│   ├── test_enrichment.py
│   └── test_security_and_validation.py
├── cli.py                   # Main CLI entry point
├── dp_laplace_budget_app.py # DP-Laplace app entry point
├── enrichment.py            # Enrichment feature modules
├── simulator.py             # High-throughput simulation
├── web/index.html           # Operations console UI
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
