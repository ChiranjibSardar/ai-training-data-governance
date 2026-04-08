# AI Training Data Governance Checklist for LLM Systems

> A structured checklist for organizations to assess their training data governance maturity, organized by the Responsible Data Infrastructure (RDI) Framework layers.

📄 A printable PDF version is available at [`assets/AI_Data_Governance_Checklist.pdf`](../assets/AI_Data_Governance_Checklist.pdf)

---

## Layer 1: Ingestion (Trust Entry Gate)

- [ ] Data sources validated against an approved allowlist
- [ ] Licensing status classified (open / restricted / unknown)
- [ ] Provenance tracked at source and document level
- [ ] PII and sensitive data automatically detected and filtered
- [ ] High-risk or ambiguous sources routed through legal review

## Layer 2: Validation (Quality & Risk Scoring)

- [ ] Quality signals computed (coherence, perplexity, structure)
- [ ] Duplicate and low-signal content removed
- [ ] Toxicity and harmful content filters applied consistently
- [ ] Bias evaluated across key demographic and contextual dimensions
- [ ] Dataset-level diversity metrics (e.g., CMDI) computed

## Layer 3: Curation (Decision & Control Engine)

- [ ] Filtering thresholds clearly defined and enforced
- [ ] Rejected data categorized and logged for analysis
- [ ] Remediation workflows defined for borderline data
- [ ] Dataset versioning with immutable audit trails
- [ ] Governance review and escalation mechanisms in place

## Layer 4: Monitoring (Continuous Feedback Loop)

- [ ] Dataset composition monitored for drift over time
- [ ] Anomalies and data poisoning signals detected
- [ ] Post-training data attribution traceable
- [ ] Incidents logged, classified, and tracked systematically
- [ ] Monitoring insights fed back into upstream pipelines

## Governance Spine: Audit, Policy & Compliance

- [ ] Centralized provenance ledger across all layers
- [ ] Policy enforcement via policy-as-code mechanisms
- [ ] All transformations captured in audit logs
- [ ] Compliance mapped to EU AI Act, NIST AI RMF, etc.
- [ ] Automated governance and audit reports generated

## Risk Domains

- [ ] Copyright and licensing violations
- [ ] Bias and fairness risks
- [ ] Data poisoning and adversarial manipulation
- [ ] Multimodal misalignment risks
- [ ] Privacy and PII exposure

## CMDI: Cross-Modal Diversity Index

- [ ] Metadata coverage across key dimensions
- [ ] Balanced distributions across attributes
- [ ] Consistency across modalities
- [ ] Statistical diversity metrics computed
- [ ] Diversity tracked over time
