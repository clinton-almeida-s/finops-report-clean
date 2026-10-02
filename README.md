# FinOps Boardroom Report

AI-augmented GCP cost analysis that generates boardroom-ready PDF reports.

## What It Does

The FinOps Boardroom Agent fetches your real GCP billing data across **all services** (Compute Engine, Cloud SQL, Cloud Storage, BigQuery, Cloud Pub/Sub, GKE, Cloud Run, Vertex AI, and more), runs it through an AI analysis layer, and produces a polished executive report — PDF and HTML — complete with cost drivers, savings opportunities, risk ratings, and Terraform snippets for the top recommendations.

It's designed for FinOps practitioners, platform engineers, and consultants who need to turn raw billing exports into a narrative that non-technical stakeholders can act on.

### Report Contents

- **Executive Summary** — plain-English spend narrative for C-suite
- **Cost Drivers** — breakdown by service and project with trends across all GCP services
- **Prioritized Recommendations** — rightsizing, committed use, spot migration, each with estimated monthly savings and risk level
- **Terraform Snippets** — ready-to-paste IaC for the top-3 fixes
- **Export Formats** — print-ready PDF (ReportLab) + shareable HTML (Jinja2)

## Architecture

```
GCP Billing API (all services)
        ↓
  BillingCollector (real cost data)
        ↓
  VM Metrics API (utilization data)
        ↓
  AgentOrchestrator (Gemini first, Claude fallback)
        ↓
  ReportGenerator (Jinja2 → HTML, ReportLab → PDF)
        ↓
  FinOps_Report_YYYY-MM-DD.pdf  +  .html
```

## Why AI Keys Are Needed

The core value of this tool is the AI layer that interprets billing data and writes human-readable analysis. Without it, you'd just have a spreadsheet with numbers.

- **`ANTHROPIC_API_KEY`** or **`ANTHROPIC_AUTH_TOKEN`** — Primary analysis provider (Claude Haiku). Produces structured JSON output from billing data.
- **`GEMINI_API_KEY`** — Priority provider (Gemini 3.8 Flash). Automatically engaged first for GCP data analysis due to natural fit with Google Cloud ecosystem. Falls back to Claude if unavailable.

If neither key is configured, the tool falls back to `--sample` mode (see below), which uses pre-built stub data and analysis — useful for testing, demos, and documentation without any cloud access.

## GCP Billing API Integration

The tool now fetches **real billing data from all GCP services** via the Cloud Billing API:

### Supported Services

| Service | API Coverage |
|---------|-------------|
| Compute Engine | VM instances, disks, GPUs |
| Cloud SQL | Database instances |
| Cloud Storage | Object storage |
| BigQuery | Query processing |
| Cloud Pub/Sub | Message publishing |
| GKE | Kubernetes Engine |
| Cloud Run | Serverless containers |
| Vertex AI | ML training/inference |
| Cloud Functions | Event-driven compute |
| Cloud CDN | Content delivery |
| Cloud Logging | Log storage |
| Cloud Monitoring | Metrics collection |
| Cloud Spanner | Managed database |
| Cloud Firestore | NoSQL database |
| Cloud Memorystore | Redis/cache |
| Cloud Tasks | Task queues |

### Authentication Options

The tool supports multiple GCP authentication methods:

1. **gcloud OAuth** (recommended) — Uses your local gcloud credentials automatically
2. **Service Account JSON key** — Set `GOOGLE_APPLICATION_CREDENTIALS` or pass path via API

## Installation

```bash
pip install -r requirements.txt
```

**Dependencies:** `click`, `reportlab`, `jinja2`, `google-genai`, `anthropic`, `requests`, `google-cloud-billing`

## API Key Configuration

Set at least one of these environment variables before running:

```bash
# Claude (primary fallback)
export ANTHROPIC_API_KEY=sk-ant-...

# Gemini (priority for GCP data)
export GEMINI_API_KEY=AIza...

# Optional: Anthropic proxy token
export ANTHROPIC_AUTH_TOKEN=...
```

**Where to get them:**
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com) → API Keys
- **Google AI**: [aistudio.google.com](https://aistudio.google.com) → API Keys

## GCP Billing Account Setup

To pull real billing data, you need two things:

### 1. GCP Billing Account ID

Find it in the Google Cloud Console:
- Go to **Billing** → **Manage billing accounts**
- The ID looks like `0136FF-F52314-9FF856` (hex-fingerprint format)

Pass it via CLI flag or environment variable:

```bash
export GCP_BILLING_ACCOUNT=0136FF-F52314-9FF856
```

### 2. Service Account with Billing Reader Role

The tool uses the Google Cloud Billing API, which requires authentication. Create a service account with the **Billing Reader** role:

```bash
# Create the service account
gcloud iam service-accounts create finops-report \
    --project YOUR_PROJECT_ID

# Grant Billing Reader role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:finops-report@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/billing.billingReaders"

# Generate and download the key
gcloud iam service-accounts keys create gcp-key.json \
    --iam-account=finops-report@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set for the session
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/gcp-key.json
```

> **Note:** The tool automatically detects gcloud credentials on Windows (via `%APPDATA%/gcloud/credentials`) and Linux/macOS (via `~/.config/gcloud/credentials`). No extra setup needed if you've run `gcloud auth login`.

## Usage

### Sample Mode — No Keys, No GCP Access

The fastest way to test the tool or run a demo:

```bash
python -m finops_report generate --sample
```

This uses built-in stub billing data (Jul–Sep 2026, $3,800→$4,200 trend) and stub analysis. Produces a full PDF and HTML report with zero external dependencies.

### Real Data — With API Keys + Billing Account

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=AIza...
export GCP_BILLING_ACCOUNT=0136FF-F52314-9FF856

python -m finops_report generate --billing-account $GCP_BILLING_ACCOUNT -m 3
```

Options:
| Flag | Env Var | Description |
|------|---------|-------------|
| `--billing-account` | `GCP_BILLING_ACCOUNT` | GCP billing account ID (required without `--sample`) |
| `--project` | `GOOGLE_CLOUD_PROJECT` | Optional: restrict to a single GCP project |
| `-m N` | — | Months of billing data to analyze (default: 3) |
| `-o DIR` | — | Output directory (default: current dir) |
| `--dry-run` | — | Show data without calling AI or generating report |
| `--sample` | — | Use built-in stub data (no keys or billing access needed) |

### Dry Run — Preview Data Only

```bash
python -m finops_report generate --billing-account $GCP_BILLING_ACCOUNT --dry-run
```

Prints the fetched billing data to stdout without calling any AI provider or generating a report. Useful for validating your GCP credentials work before committing to a full run.

### Output

Reports are saved as:

```
FinOps_Report_2026-10-02.pdf   # ~43KB, print-ready
FinOps_Report_2026-10-02.html  # ~2KB, browser-viewable
```

## Features

### Real GCP Billing API Integration
- Fetches actual cost data from Cloud Billing API for all services
- SKU-level pricing breakdown where available
- Automatic fallback to resource-based estimation when billing API returns no data

### VM Utilization Analysis
- Pulls CPU and memory metrics from Cloud Monitoring API
- Identifies underutilized instances (<40% CPU or <50% memory)
- Generates rightsizing recommendations with savings estimates

### Spot Instance Detection
- Identifies development, testing, and batch workloads suitable for spot instances
- Estimates 60-80% cost savings for eligible workloads

### Multi-Provider AI Analysis
- **Gemini first** — prioritized for GCP data (natural Google ecosystem fit)
- **Claude fallback** — reliable secondary option
- Both providers return structured JSON with executive summary, cost drivers, recommendations, and Terraform snippets

### Intelligent Fallbacks
- When billing API returns 404 (no active services), falls back to resource discovery
- JSON truncation recovery handles cases where LLM output exceeds token limits
- Parallel API calls speed up multi-project analysis

## Testing

```bash
pytest tests/ -v
```

12 tests cover: CLI parsing, agent orchestration (Claude + Gemini), report generation (PDF + HTML), and end-to-end flows. All tests pass with no external dependencies — they use mock clients and stub data.

## For Consultants

This tool is the delivery mechanism for a GCP cost optimization audit. Typical engagement flow:

1. Run `--sample` first to walk the client through the report format
2. Get their GCP billing account ID and service account credentials
3. Run full analysis against their real data (all services included)
4. Deliver the PDF as part of a $2k–5k FinOps audit package
