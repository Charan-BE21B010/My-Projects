from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

# Allow running without install: python -m importer_engine.cli
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_engine.models import DiscoveryRequest
from importer_engine.pipeline import run_discovery

app = typer.Typer(add_completion=False, help="AI-powered importer discovery engine", invoke_without_command=True)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    product: str = typer.Option(None, "--product", "-p", help="Product niche"),
    country: str = typer.Option(None, "--country", "-c", help="Target country"),
    top_n: int = typer.Option(8, "--top-n", "-n", help="Number of importers"),
    out: Path = typer.Option(None, "--out", "-o", help="Optional JSON output path"),
    exporter_context: str = typer.Option(
        None, "--context", help="Optional note about the Indian exporter"
    ),
):
    """Discover and rank relevant importer companies."""
    if ctx.invoked_subcommand is not None:
        return
    if not product or not country:
        console.print(
            "Usage: python discover.py -p \"Ceramic Tiles\" -c Germany -n 8"
        )
        raise typer.Exit(code=1)
    _run_discover(product, country, top_n, out, exporter_context)


def _run_discover(
    product: str,
    country: str,
    top_n: int,
    out: Path | None,
    exporter_context: str | None,
):
    console.print(
        f"[bold]Discovering importers[/bold] for [cyan]{product}[/cyan] "
        f"in [cyan]{country}[/cyan] ..."
    )
    result = run_discovery(
        DiscoveryRequest(
            product=product,
            country=country,
            top_n=top_n,
            exporter_context=exporter_context,
        )
    )

    table = Table(title=f"Top importers: {product} -> {country}")
    table.add_column("#", justify="right")
    table.add_column("Company")
    table.add_column("Score", justify="right")
    table.add_column("Email")
    table.add_column("Website")
    table.add_column("Why")

    for row in result.importers:
        table.add_row(
            str(row.rank),
            row.company_name,
            f"{row.relevance_score:.1f}",
            row.contact_email or "-",
            row.website or "-",
            (row.match_reason[:80] + "...")
            if len(row.match_reason) > 80
            else row.match_reason,
        )

    console.print(table)
    console.print(f"Mode: {result.mode}")
    for note in result.notes:
        console.print(f"[dim]- {note}[/dim]")

    if out is None:
        safe = f"{product}_{country}".lower().replace(" ", "_")
        out = ROOT / "results" / f"{safe}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"Saved JSON to [green]{out}[/green]")


@app.command("discover")
def discover_cmd(
    product: str = typer.Option(..., "--product", "-p", help="Product niche"),
    country: str = typer.Option(..., "--country", "-c", help="Target country"),
    top_n: int = typer.Option(8, "--top-n", "-n", help="Number of importers"),
    out: Path = typer.Option(None, "--out", "-o", help="Optional JSON output path"),
    exporter_context: str = typer.Option(
        None, "--context", help="Optional note about the Indian exporter"
    ),
):
    """Discover and rank relevant importer companies."""
    _run_discover(product, country, top_n, out, exporter_context)


@app.command("run-samples")
def run_samples(
    live: bool = typer.Option(
        False,
        "--live",
        help="Also run live web search (slower, noisier). Default is seed_only.",
    ),
):
    """Regenerate the three sample product-country result files."""
    samples = [
        ("Ceramic Tiles", "Germany", 8),
        ("Basmati Rice", "UAE", 8),
        ("Cotton Textiles", "USA", 8),
    ]
    sample_dir = ROOT / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for product, country, n in samples:
        console.print(f"Running {product} / {country} ...")
        result = run_discovery(
            DiscoveryRequest(product=product, country=country, top_n=n),
            seed_only=not live,
        )
        path = sample_dir / f"{product.lower().replace(' ', '_')}_{country.lower()}.json"
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"  -> {path} ({len(result.importers)} importers)")


if __name__ == "__main__":
    app()