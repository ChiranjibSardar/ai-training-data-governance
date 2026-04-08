"""Tests for the RDI CLI."""

from pathlib import Path

from click.testing import CliRunner

from rdi.cli import main


class TestCLIRun:
    """Tests for the ``rdi run`` command."""

    def test_run_with_valid_input(self, tmp_path: Path) -> None:
        """rdi run with valid input produces a report and exits 0."""
        input_dir = tmp_path / "corpus"
        input_dir.mkdir()
        (input_dir / "doc.txt").write_text("Hello world.", encoding="utf-8")
        output_dir = tmp_path / "output"

        runner = CliRunner()
        result = runner.invoke(main, ["run", "--input", str(input_dir), "--output", str(output_dir)])

        assert result.exit_code == 0
        assert "Pipeline complete" in result.output
        assert "1 record(s)" in result.output
        assert (output_dir / "risk_report.json").exists()

    def test_run_nonexistent_input_path(self, tmp_path: Path) -> None:
        """rdi run with non-existent input path exits with code 1."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "run",
            "--input", str(tmp_path / "does_not_exist"),
            "--output", str(tmp_path / "output"),
        ])

        assert result.exit_code == 1
        assert "does not exist" in result.output or "does not exist" in (result.stderr or "")

    def test_run_no_text_files(self, tmp_path: Path) -> None:
        """rdi run with directory containing no .txt files exits with code 1."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(main, [
            "run",
            "--input", str(empty_dir),
            "--output", str(tmp_path / "output"),
        ])

        assert result.exit_code == 1
        assert "No text files found" in result.output or "No text files found" in (result.stderr or "")


class TestCLIValidateLedger:
    """Tests for the ``rdi validate-ledger`` command."""

    def test_validate_valid_ledger(self, tmp_path: Path) -> None:
        """rdi validate-ledger on a valid ledger exits 0."""
        # Create a valid ledger by running the pipeline first
        input_dir = tmp_path / "corpus"
        input_dir.mkdir()
        (input_dir / "a.txt").write_text("Some text.", encoding="utf-8")
        output_dir = tmp_path / "output"

        runner = CliRunner()
        runner.invoke(main, ["run", "--input", str(input_dir), "--output", str(output_dir)])

        ledger_path = output_dir / "provenance_ledger.jsonl"
        assert ledger_path.exists()

        result = runner.invoke(main, ["validate-ledger", "--ledger", str(ledger_path)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_nonexistent_ledger(self, tmp_path: Path) -> None:
        """rdi validate-ledger on non-existent file exits with code 1."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "validate-ledger",
            "--ledger", str(tmp_path / "missing.jsonl"),
        ])

        assert result.exit_code == 1
        assert "does not exist" in result.output or "does not exist" in (result.stderr or "")
