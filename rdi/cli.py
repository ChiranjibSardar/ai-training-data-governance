"""CLI entry point for the RDI Framework.

Provides ``rdi run`` and ``rdi validate-ledger`` commands built with click.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from rdi.models import PipelineConfig
from rdi.pipeline import Pipeline
from rdi.provenance_ledger import ProvenanceLedger


@click.group()
def main() -> None:
    """Responsible Data Infrastructure (RDI) — AI training-data governance."""


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(), help="Input directory or file path.")
@click.option("--output", "output_path", required=True, type=click.Path(), help="Output directory path.")
@click.option("--threshold-toxicity", default=0.8, type=float, show_default=True, help="Toxicity threshold.")
def run(input_path: str, output_path: str, threshold_toxicity: float) -> None:
    """Run the RDI pipeline on text files."""
    inp = Path(input_path)
    out = Path(output_path)

    # Validate input path exists
    if not inp.exists():
        click.echo(f"Error: Input path '{input_path}' does not exist.", err=True)
        sys.exit(1)

    # Validate text files are present
    if inp.is_dir():
        txt_files = list(inp.glob("*.txt"))
        if not txt_files:
            click.echo(f"Error: No text files found in '{input_path}'.", err=True)
            sys.exit(1)
    elif not inp.is_file():
        click.echo(f"Error: Input path '{input_path}' does not exist.", err=True)
        sys.exit(1)

    # Validate output directory is writable
    try:
        out.mkdir(parents=True, exist_ok=True)
        test_file = out / ".rdi_write_test"
        test_file.write_text("", encoding="utf-8")
        test_file.unlink()
    except OSError:
        click.echo(f"Error: Cannot write to output directory '{output_path}'.", err=True)
        sys.exit(1)

    config = PipelineConfig(toxicity_threshold=threshold_toxicity)
    pipeline = Pipeline(config=config)
    report = pipeline.run(inp, out)

    click.echo(f"Pipeline complete. Processed {report.dataset_summary['total_records']} record(s).")
    click.echo(f"Risk level: {report.risk_level}")
    click.echo(f"Report written to {out / 'risk_report.json'}")



@main.command("validate-ledger")
@click.option("--ledger", required=True, type=click.Path(), help="Path to the JSONL ledger file.")
def validate_ledger(ledger: str) -> None:
    """Validate the integrity of a provenance ledger."""
    ledger_path = Path(ledger)

    if not ledger_path.exists():
        click.echo(f"Error: Ledger file '{ledger}' does not exist.", err=True)
        sys.exit(1)

    provenance = ProvenanceLedger(path=ledger_path)
    valid, index, description = provenance.verify()

    if valid:
        entry_count = len(provenance.entries)
        click.echo(f"Ledger is valid. {entry_count} entry(ies) verified.")
    else:
        click.echo(f"Ledger is CORRUPTED at entry {index}: {description}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
