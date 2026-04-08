# Upstream by Design: A Framework for Responsible AI Training Data Governance

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Status: POC Complete](https://img.shields.io/badge/Status-POC%20Complete-green.svg)]()
[![Tests: 67 passed](https://img.shields.io/badge/Tests-67%20passed-brightgreen.svg)]()
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()

> **Responsible Data Infrastructure (RDI) Framework** — A design-science framework for embedding governance into AI training data pipelines at the point of ingestion, not after the fact.

---

## The Problem

Foundation models are statistical artifacts of their training corpora. Defects in data provenance, licensing, privacy, representational balance, quality, and adversarial integrity get absorbed into model parameters and reproduced across every downstream use. Yet the field's governance energy remains concentrated on post-training controls - alignment, red-teaming, evaluation benchmarks, and deployment guardrails. Training data governance is the most consequential and least-addressed gap in the AI safety lifecycle.

## What This Repo Contains

This repository hosts the **Responsible Data Infrastructure (RDI) Framework**, a research-driven, practice-grounded governance architecture for AI training data pipelines. The framework treats training data pipelines as enterprise risk and decision-support systems rather than purely technical infrastructure.

| Resource | Description |
|----------|-------------|
| [`rdi/`](rdi/) | Python package implementing Layers 1 & 2 of the RDI pipeline |
| [`tests/`](tests/) | 67 unit tests covering all implemented components |
| [`samples/`](samples/) | Sample text files for demo and testing |
| [`docs/framework-overview.md`](docs/framework-overview.md) | Full description of the four-layer RDI architecture |
| [`docs/risk-taxonomy.md`](docs/risk-taxonomy.md) | Taxonomy of upstream risks: copyright, bias, poisoning, privacy, multimodal gaps |
| [`docs/evaluation-checklist.md`](docs/evaluation-checklist.md) | Practical checklist for evaluating AI training data governance |
| [`docs/spec/`](docs/spec/) | Requirements, design, and implementation task documents |
| [`reports/`](reports/) | POC status report (.docx) |
| [`assets/`](assets/) | Architecture diagrams and visual assets |
| [`paper/`](paper/) | Working paper draft, not for citation |


## The RDI Framework at a Glance

The framework organizes governance across **four sequential layers** of the training data lifecycle, with a cross-cutting risk overlay and a governance spine:

![Architecture Diagram](assets/governance-framework-diagram.svg)


### Layer 1: Ingestion (Trust Entry Gate)
Gatekeeping layer where data first enters the pipeline. Enforces provenance validation, rights classification, and PII detection before any data reaches training infrastructure.

- C2PA content credential validation
- ML-based license classification
- PII scanning and redaction
- Provenance ledger with cryptographic audit trail

### Layer 2: Validation & Risk Scoring
Scores incoming data across quality, safety, and representational dimensions. Introduces the **Cross-Modal Diversity Index (CMDI)** — a novel composite metric for measuring representational fairness across demographic, geographic, linguistic, and contextual dimensions of multimodal corpora.

- ML quality scoring (coherence, factuality)
- Multimodal bias detection
- Toxicity filtering
- Deduplication pipeline

### Layer 3: Curation & Decision Engine
The decision layer where governance controls determine what enters training and under what conditions. Threshold-based filtering with human-in-the-loop escalation for edge cases.

- Threshold-based filtering engine
- Automated remediation workflows
- Data versioning with immutable audit logs
- Cross-jurisdictional compliance mapping (EU AI Act, NIST AI RMF, US Copyright)

### Layer 4: Monitoring & Feedback Loop
Continuous post-curation monitoring with a feedback loop back to ingestion — critical for the design-science framing of governance as an iterative, self-correcting system.

- Dataset composition drift detection
- Post-training data attribution tracing
- Incident telemetry and anomaly detection
- Regulatory alert system

## POC Implementation

The POC implements Layers 1 and 2 as a working Python package (`rdi`), with all components using exclusively open-source models, tools, and public datasets.

### Implemented Components

| Component | Description | Technology |
|-----------|-------------|------------|
| PII Scanner | Detects and redacts names, emails, phones, addresses, SSNs | Presidio + spaCy `en_core_web_lg` |
| Provenance Ledger | Tamper-evident SHA-256 hash-chained append-only audit log | Python `hashlib` |
| Toxicity Filter | Multi-category scoring (toxic, obscene, threat, insult, identity hate) | Detoxify (`unitary/toxic-bert`) |
| Deduplicator | Near-duplicate detection via MinHash + Locality-Sensitive Hashing | datasketch |
| Risk Report | Structured JSON report with risk level assessment | Python dataclasses |
| Pipeline & CLI | End-to-end orchestration with `rdi run` and `rdi validate-ledger` | click + tqdm |

### Stubbed for Phase 2

| Component | Planned Technology |
|-----------|-------------------|
| License Classifier | HuggingFace Transformers (distilbert / bart-large-mnli) |
| Quality Scorer | GPT-2 perplexity measurement |
| CMDI Calculator | langdetect + gensim LDA + spaCy NER |
| C2PA Validator | c2patool CLI wrapper |

### Test Results

- 67 unit tests across 7 test files
- 100% pass rate
- Covers: PII detection, hash-chain integrity, toxicity scoring, deduplication clustering, risk report serialization, pipeline orchestration, CLI error handling

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/ChiranjibSardar/ai-training-data-governance.git
cd ai-training-data-governance
pip install -e '.[dev]'
python -m spacy download en_core_web_lg
```

### Run the Pipeline

```bash
# Process a directory of text files
rdi run --input samples/ --output output/

# Process a single file
rdi run --input document.txt --output results/

# Validate the provenance ledger
rdi validate-ledger --ledger output/provenance_ledger.jsonl
```

### Run the Demo

```bash
./demo.sh
```

### Use as a Python Library

```python
from pathlib import Path
from rdi.pipeline import Pipeline
from rdi.models import PipelineConfig

pipeline = Pipeline(config=PipelineConfig(toxicity_threshold=0.8))
report = pipeline.run(Path("your_data/"), Path("output/"))
print(f"Risk level: {report.risk_level}")
```

### Use Individual Components

```python
from rdi.pii_scanner import PIIScanner
from rdi.toxicity_filter import ToxicityFilter
from rdi.deduplicator import Deduplicator

scanner = PIIScanner()
result = scanner.scan("Contact john@example.com for details.")
print(result.redacted_text)  # "Contact [EMAIL] for details."

toxicity = ToxicityFilter()
scores = toxicity.score("Some text to analyze")
print(scores.scores)  # {'toxic': 0.01, 'severe_toxic': 0.0, ...}
```

### Run Tests

```bash
python -m pytest tests/ -v
```

## Six Gaps This Framework Addresses

The RDI Framework is motivated by six critical gaps identified in the literature:

| # | Gap | RDI Response |
|---|-----|-------------|
| 1 | Downstream dominance over upstream governance | Entire upstream-first architecture (Layers 1–4) |
| 2 | Documentation without continuous operational control | Ingestion gates + change-control processes |
| 3 | Weak operationalization of provenance and rights | C2PA credentials + License ML + Provenance Ledger |
| 4 | Inadequate multimodal governance metrics | Cross-Modal Diversity Index (CMDI) |
| 5 | Missing decision-support for governance trade-offs | Governance Spine decision-support model |
| 6 | Limited enterprise implementation research | Full four-layer repeatable operating capability |

## Key References

This work draws on and extends research across responsible AI governance, foundation-model transparency, dataset documentation, and adversarial robustness. Key influences include:

- **NIST AI RMF** (2023) and **Generative AI Profile** (2024) - lifecycle risk management
- **EU AI Act** (Regulation 2024/1689) - GPAI model obligations on training data
- **Longpre et al.** (2024) - large-scale audits of dataset licensing, consent, and pretraining data effects
- **Bommasani et al.** (2023, 2024) - Foundation Model Transparency Index
- **Gebru et al.** (2021) - Datasheets for Datasets
- **Bender & Friedman** (2018) - Data Statements for NLP
- **OWASP** (2025) - LLM04:2025 Data and Model Poisoning
- **U.S. Copyright Office** (2025) - Part III report on generative AI training

See the [working paper](paper/) for the full literature review and citation list.


## Related Resources

- **Working Paper**: [Upstream by Design: A Framework for Responsible AI Training Data Governance](paper/training-data-governance-framework.pdf) *(draft — not for citation)*
- **Practical Checklist**: [Evaluating AI Training Data Governance](docs/evaluation-checklist.md)
- **POC Status Report**: [RDI Framework POC Status Report](reports/RDI_Framework_POC_Status_Report.docx)
- **Spec Documents**: [Requirements](docs/spec/requirements.md) · [Design](docs/spec/design.md) · [Tasks](docs/spec/tasks.md)

## Authors

**Chiranjib Sardar**
Senior Technical Program Manager, Amazon AGI
[GitHub](https://github.com/ChiranjibSardar) · [LinkedIn](https://www.linkedin.com/in/chiranjibsardar/) 



## Contributing

This is an active research project. We welcome contributions in the following areas:

- **Literature pointers**: Papers, reports, or policy documents relevant to training data governance
- **Framework feedback**: Critiques, extensions, or alternative framings of the RDI layers
- **Metric development**: Ideas for operationalizing the Cross-Modal Diversity Index (CMDI)
- **Industry case studies**: Real-world examples of training data governance practices (anonymized)

To contribute, please open an issue describing your proposed contribution, or submit a pull request with a clear description of changes.

## Citation

If you reference this work, please cite:

```bibtex
@misc{sardar2026rdi,
  title={Upstream by Design: A Framework for Responsible AI Training Data Governance},
  author={Sardar, Chiranjib},
  year={2026},
  note={Working paper, draft v0.1. Available at \url{https://github.com/ChiranjibSardar/ai-training-data-governance}}
}
```

## License

This work is licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

You are free to share and adapt this material for any purpose, provided you give appropriate attribution.

---

*This repository is part of an ongoing research collaboration. The framework is a working draft and will evolve as the research progresses. Feedback and engagement are welcome.*
