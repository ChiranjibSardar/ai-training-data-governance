"""Tests for the Pipeline orchestrator."""

from pathlib import Path

from rdi.models import PipelineConfig, RiskReport
from rdi.pipeline import Pipeline


class TestPipeline:
    """Unit tests for Pipeline.run()."""

    def test_run_with_single_file(self, tmp_path: Path) -> None:
        """Pipeline processes a single .txt file and produces a report."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("Hello world, this is a test document.", encoding="utf-8")
        output_dir = tmp_path / "output"

        config = PipelineConfig()
        pipeline = Pipeline(config=config)
        report = pipeline.run(input_file, output_dir)

        assert isinstance(report, RiskReport)
        assert report.dataset_summary["total_records"] == 1
        assert len(report.records) == 1
        assert report.records[0].record_id == "input.txt"
        assert report.risk_level in {"low", "medium", "high"}

        # Report JSON was written
        report_path = output_dir / "risk_report.json"
        assert report_path.exists()

        # Provenance ledger was written
        ledger_path = output_dir / "provenance_ledger.jsonl"
        assert ledger_path.exists()
        lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

    def test_run_with_directory(self, tmp_path: Path) -> None:
        """Pipeline processes all .txt files in a directory."""
        input_dir = tmp_path / "corpus"
        input_dir.mkdir()
        for i in range(3):
            (input_dir / f"doc_{i}.txt").write_text(
                f"Document number {i} with some content.", encoding="utf-8"
            )
        output_dir = tmp_path / "output"

        pipeline = Pipeline()
        report = pipeline.run(input_dir, output_dir)

        assert report.dataset_summary["total_records"] == 3
        assert len(report.records) == 3
        record_ids = {r.record_id for r in report.records}
        assert record_ids == {"doc_0.txt", "doc_1.txt", "doc_2.txt"}

    def test_run_creates_output_directory(self, tmp_path: Path) -> None:
        """Pipeline creates the output directory if it doesn't exist."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("Some text.", encoding="utf-8")
        output_dir = tmp_path / "nested" / "output"

        pipeline = Pipeline()
        pipeline.run(input_file, output_dir)

        assert output_dir.exists()
        assert (output_dir / "risk_report.json").exists()

    def test_run_empty_directory(self, tmp_path: Path) -> None:
        """Pipeline handles an empty directory (no .txt files)."""
        input_dir = tmp_path / "empty"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        pipeline = Pipeline()
        report = pipeline.run(input_dir, output_dir)

        assert report.dataset_summary["total_records"] == 0
        assert len(report.records) == 0

    def test_collect_files_single_file(self, tmp_path: Path) -> None:
        """_collect_files returns a single-element list for a file path."""
        f = tmp_path / "single.txt"
        f.write_text("content", encoding="utf-8")

        result = Pipeline._collect_files(f)
        assert result == [f]

    def test_collect_files_directory(self, tmp_path: Path) -> None:
        """_collect_files returns sorted .txt files from a directory."""
        d = tmp_path / "docs"
        d.mkdir()
        (d / "b.txt").write_text("b", encoding="utf-8")
        (d / "a.txt").write_text("a", encoding="utf-8")
        (d / "c.csv").write_text("c", encoding="utf-8")  # not .txt

        result = Pipeline._collect_files(d)
        assert [p.name for p in result] == ["a.txt", "b.txt"]
