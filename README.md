
# AWS Agentic Maintenance Operations

A local-first simulation of an agentic AI workflow for investigating industrial equipment alerts, gathering maintenance evidence, and evaluating proposed actions against deterministic operational policies.

The project explores how Amazon Bedrock's Converse API and tool-use capabilities can support maintenance investigations without giving a language model direct authority to approve operational actions.

The current implementation runs locally using scripted Bedrock responses and simulated maintenance data. No AWS resources are required to run the offline demonstration.

## Problem Statement

Equipment alerts often require information from several systems before an engineer can decide what to do. An elevated vibration reading, for example, may need to be evaluated alongside asset criticality, maintenance history, production schedules, and available maintenance windows.

This project simulates that investigation process.

Rather than relying on a model's response alone, the workflow retrieves structured evidence through defined tools, validates the returned data, and submits a proposed maintenance action for separate policy evaluation.

## Architecture

The workflow separates evidence collection, action proposal generation, and policy evaluation.

1. An equipment alert initiates an investigation.
2. The Bedrock Converse conversation loop requests maintenance evidence through defined tools.
3. Local tools retrieve data from simulated maintenance records.
4. Tool responses are validated and captured as evidence records.
5. The model produces an investigation summary and submits a structured action proposal.
6. A deterministic policy evaluator determines whether the proposed action is permitted or requires approval.

The workflow includes five evidence-retrieval tools:

- `get_equipment_alert`
- `get_asset_context`
- `get_maintenance_history`
- `get_production_schedule`
- `get_maintenance_window_status`

A separate `evaluate_proposed_maintenance_action` tool supports policy evaluation. Policy enforcement is handled independently of the model's narrative response.

### Authorization Boundary

A model-generated statement is not treated as operational authorization.

For example, the model may suggest an immediate equipment shutdown, but the deterministic policy evaluator can still return `requires_approval`.

Incomplete investigations are rejected before action-proposal generation or policy evaluation.

## Running the Offline Demonstration

The offline demonstration executes the investigation workflow using a scripted Bedrock-compatible client. It does not make AWS API calls.

### Prerequisites

- Python 3.13
- Git

### Installation

Clone the repository:

```bash
git clone https://github.com/HeathMSmith/aws-agentic-maintenance-ops.git
cd aws-agentic-maintenance-ops
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

### Run the Investigation

From the repository root:

```bash
python -m examples.run_offline_investigation
```

The demonstration investigates `ALERT-0001`, an equipment anomaly involving conveyor motor `CONV-MTR-042`.

Its output includes the investigation summary, evidence-tool execution trace, validated evidence records, structured action proposal, and policy decision.

The sample uses a fixed reference timestamp for repeatability.

### Run the Tests

```bash
python -m pytest -q
```

The tests cover local tools, evidence validation, Bedrock conversation handling, investigation workflow behavior, action proposals, and policy enforcement.

## Evidence Auditability and Integrity

Successful evidence-tool executions produce structured evidence records containing:

- `tool_name`: The tool that returned the evidence.
- `tool_use_id`: The identifier associated with the model's tool request.
- `identifiers`: The asset or alert identifiers associated with the request.
- `result`: The validated evidence payload.
- `sha256`: A deterministic SHA-256 digest of the record content.

The digest is calculated over the record's tool name, tool-use ID, identifiers, and evidence payload. The digest field itself is excluded from the calculation.

Records are serialized using canonicalized JSON key ordering to produce consistent digests for equivalent content.

The workflow also retains successfully validated evidence when a conversation stops unexpectedly or reaches its configured model-call limit.

### Integrity Limitations

SHA-256 provides a means of checking whether recorded content matches an expected digest. It does not establish the authenticity of the evidence source or prevent an attacker from changing both a record and its digest.

Evidence records are currently returned in memory. The project does not implement durable evidence storage, digital signatures, or an immutable audit log.

These would require additional design work before the system could be considered suitable for production maintenance operations.

## Current Scope

The repository currently implements:

- Simulated industrial equipment and maintenance datasets.
- Local maintenance evidence retrieval tools.
- Structured evidence validation.
- Bedrock Converse-style tool orchestration.
- A scripted offline investigation demonstration.
- Structured maintenance-action proposals.
- Deterministic policy evaluation.
- Evidence capture and SHA-256 integrity checking.
- Automated regression tests.

## Future Development

Potential next steps include:

- Running investigations against an actual Amazon Bedrock model.
- Provisioning the required AWS infrastructure with Terraform.
- Persisting investigation records in durable storage.
- Adding authenticated evidence provenance and protected audit records.
- Implementing appropriate IAM boundaries, monitoring, and operational safeguards.

The current focus is on understanding and validating the agentic workflow locally before introducing deployment complexity and AWS costs.
