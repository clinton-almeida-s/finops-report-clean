import click
from typing import Any, Dict

from .config import load_config
from .agent import AgentOrchestrator
from .report_generator import generate_report
from .billing_collector import BillingCollector

@click.group()
def cli():
    """FinOps Boardroom Report — AI-augmented GCP cost analysis."""
    pass


@cli.command()
@click.option("--billing-account", envvar="GCP_BILLING_ACCOUNT", required=False, default=None, help="GCP billing account ID (not needed with --sample)")
@click.option("--project", envvar="GOOGLE_CLOUD_PROJECT", default=None, help="GCP project ID (optional)")
@click.option("--months", "-m", default=3, show_default=True, help="Months of billing data to analyze")
@click.option("--output-dir", "-o", default=".", help="Output directory for reports")
@click.option("--dry-run", is_flag=True, help="Show data without calling AI or generating report")
@click.option("--sample", is_flag=True, help="Run with built-in sample data (no real billing data needed)")
def generate(billing_account: str, project: str, months: int, output_dir: str, dry_run: bool, sample: bool):
    if not sample and not billing_account:
        raise click.UsageError("Missing option '--billing-account' (or use --sample to skip)")
    """Fetch GCP billing data and generate a boardroom-ready report."""

    if sample:
        click.echo("[*] Using built-in sample data (no API keys or billing data required).")
        raw_data = {
            "2026-07": {"total_cost": 3800.00, "projects": {"project-alpha": 2100.00, "project-beta": 980.00, "project-gamma": 720.00}, "services": {"Compute Engine": 2100.00, "Cloud SQL": 980.00, "Cloud Storage": 420.00, "Cloud Logging": 180.00, "Cloud CDN": 120.00}},
            "2026-08": {"total_cost": 4050.00, "projects": {"project-alpha": 2250.00, "project-beta": 1050.00, "project-gamma": 750.00}, "services": {"Compute Engine": 2250.00, "Cloud SQL": 1050.00, "Cloud Storage": 450.00, "Cloud Logging": 180.00, "Cloud CDN": 120.00}},
            "2026-09": {"total_cost": 4200.00, "projects": {"project-alpha": 2400.00, "project-beta": 1000.00, "project-gamma": 800.00}, "services": {"Compute Engine": 2400.00, "Cloud SQL": 1000.00, "Cloud Storage": 480.00, "Cloud Logging": 200.00, "Cloud CDN": 120.00}},
        }
        vm_recs, spot_cands, savings = [], [], {"total_potential_savings": 0}
    else:
        config = load_config()
        collector = BillingCollector(billing_account_id=billing_account, project_id=project)
        click.echo(f"[*] Fetching billing data for {months} months...")
        raw_data = collector.fetch_billing_data(months_back=months)
        vm_recs = collector.get_vm_recommendations()
        spot_cands = collector.get_spot_instance_candidates()
        savings = collector.calculate_total_potential_savings()

    if dry_run:
        click.echo("[*] Dry run — skipping AI analysis and report generation.")
        latest = max(raw_data) if raw_data else "N/A"
        total = raw_data.get(latest, {}).get("total_cost", None)
        if isinstance(total, (int, float)):
            click.echo(f"    Latest month:     {latest}")
            click.echo(f"    Total cost:       ${total:,.2f}")
        else:
            click.echo(f"    Latest month:     {latest}  (total_cost: {total})")
        click.echo(f"    VM rightsizing recs: {len(vm_recs)}")
        click.echo(f"    Spot candidates:    {len(spot_cands)}")
        savings_val = savings.get("total_potential_savings", 0)
        if isinstance(savings_val, (int, float)):
            click.echo(f"    Total savings:      ${savings_val:,.2f}")
        return

    if sample:
        # Stub analysis for testing — no AI key required
        click.echo("[*] Sample mode — using stub analysis (no AI provider needed).")
        analysis = {
            "executive_summary": "Monthly spend is $4,200 with a 15% upward trend over the last 3 months.",
            "cost_drivers": [
                {"name": "Compute Engine", "amount": 2400.00},
                {"name": "Cloud SQL", "amount": 1000.00},
                {"name": "Cloud Storage", "amount": 480.00},
                {"name": "Cloud Logging", "amount": 200.00},
                {"name": "Cloud CDN", "amount": 120.00},
            ],
            "recommendations": [
                {
                    "title": "Right-size dev-worker-02",
                    "description": "CPU avg 12%, memory avg 22%. Downsize from n1-standard-4 to e2-standard-2.",
                    "estimated_monthly_savings": 120,
                    "risk_level": "low",
                    "priority": 1,
                },
                {
                    "title": "Migrate batch-processor to E2",
                    "description": "Sustained use discount applies on E2 for steady workloads.",
                    "estimated_monthly_savings": 200,
                    "risk_level": "medium",
                    "priority": 2,
                },
            ],
            "tf_snippets": [
                {
                    "code": 'resource "google_compute_instance" "worker" {\n  machine_type = "e2-standard-2"\n}',
                },
            ],
        }
    else:
        config = load_config()
        click.echo("[*] Running AI analysis...")
        orchestrator = AgentOrchestrator(config)
        analysis = orchestrator.analyze({
            "billing_data": raw_data,
            "vm_recommendations": vm_recs,
            "spot_candidates": spot_cands,
            "savings": savings,
        })

    click.echo(f"[*] Generating report in {output_dir}...")
    pdf_path, html_path = generate_report(analysis, raw_data, output_dir)
    click.echo(f"[+] PDF report: {pdf_path}")
    click.echo(f"[+] HTML report: {html_path}")