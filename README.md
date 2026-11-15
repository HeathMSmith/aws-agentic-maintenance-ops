
# AWS Agentic Maintenance Operations


A simulation of an agentic AI workflow for investigating industrial equipment alerts, gathering maintenance evidence, and evaluating proposed actions against deterministic operational policies.

The project explores how Amazon Bedrock's Converse API and tool-use capabilities can support maintenance investigations without giving a language model direct authority to approve operational actions.

The workflow can run locally using scripted Bedrock responses or in AWS using a Python 3.13 Lambda function that invokes Claude Haiku 4.5 through Amazon Bedrock. Terraform manages the Lambda function, its IAM permissions, and CloudWatch logging.

Both execution environments use simulated maintenance data. No real equipment is controlled, and proposed maintenance actions are not executed automatically.

The offline demonstration does not require AWS resources or incur Bedrock inference charges.


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


## AWS Deployment

The investigation workflow also runs as an AWS Lambda function using Amazon Bedrock for live model inference. Terraform manages the Lambda function, its execution role, Bedrock permissions, and CloudWatch logging.

The deployed environment uses the same simulated maintenance datasets as the offline demonstration. It does not connect to industrial control systems or execute maintenance actions.

### Infrastructure

The Terraform configuration in `terraform/` creates:

- A Python 3.13 Lambda function named `agentic-maintenance-ops`.
- A dedicated Lambda execution role with scoped CloudWatch Logs and Bedrock permissions.
- A CloudWatch log group with seven-day retention.

The Lambda function runs outside a customer-managed VPC. It invokes Claude Haiku 4.5 through the global Bedrock inference profile `global.anthropic.claude-haiku-4-5-20251001-v1:0`.

Terraform state is stored in an existing S3 bucket using a dedicated state key and native S3 locking. The state bucket is managed separately from this repository.

### Build the Lambda Package

From the repository root:

```bash
bash scripts/build_lambda.sh
```

The script installs Python 3.13-compatible Linux x86_64 dependencies, copies the application code and simulation datasets, removes Python cache files, and creates:

```text
build/lambda/aws-agentic-maintenance-lambda.zip
```

The generated ZIP is excluded from Git. File timestamps are normalized to make repeated builds reproducible within the same build environment.

### Deploy with Terraform

The deployment requires AWS credentials with permission to manage Lambda, IAM, CloudWatch Logs, and the configured S3 Terraform backend.

Initialize Terraform:

```bash
AWS_PROFILE=portfolio terraform -chdir=terraform init
```

Build the Lambda package before planning or applying infrastructure changes.

Set the artifact path:

```bash
export TF_VAR_lambda_zip_path="$(pwd)/build/lambda/aws-agentic-maintenance-lambda.zip"
```

Review the planned changes:

```bash
AWS_PROFILE=portfolio terraform -chdir=terraform plan
```

Apply the configuration after reviewing the plan:

```bash
AWS_PROFILE=portfolio terraform -chdir=terraform apply
```

The `portfolio` profile is used for this project's deployment environment. Other environments can use their own AWS credential configuration.

Amazon Bedrock inference and AWS infrastructure usage may incur charges.

### Invoke the Investigation

Invoke the deployed Lambda function using the simulated alert:

```bash
AWS_PROFILE=portfolio aws lambda invoke \
  --function-name agentic-maintenance-ops \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload '{
    "alert_id": "ALERT-0001",
    "reference_timestamp": "2026-11-10T18:00:00Z"
  }' \
  --cli-read-timeout 180 \
  /tmp/agentic-maintenance-response.json
```

Inspect the response:

```bash
python -m json.tool /tmp/agentic-maintenance-response.json
```

A successful investigation returns an `evaluated` status, maintenance-window assessment, authorization assessment, and proposed action.

The model-generated proposal is marked `model_generated_unverified`. The authorization assessment is produced through deterministic policy evaluation rather than accepting the model's narrative as operational authority.

### Validate the Deployment

The AWS deployment was verified through:

- A successful Terraform deployment and subsequent no-change plan.
- An AWS Lambda configuration and deployment artifact hash check.
- A controlled invalid-input invocation.
- A live Bedrock investigation of `ALERT-0001`.
- CloudWatch execution logs and Lambda resource metrics.

The live investigation completed successfully and returned a permitted expert-review request. This validates the tested workflow, not every possible maintenance scenario.

The initial deployment uses 512 MB of Lambda memory and a 120-second timeout. These are starting settings rather than performance-tested production requirements.


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

- Simulated industrial equipment alerts, asset records, maintenance history, and production schedules.
- Maintenance evidence retrieval through defined tools.
- Structured evidence validation and SHA-256 integrity checking.
- Bedrock Converse API tool orchestration.
- A scripted offline investigation demonstration.
- Live investigation execution using AWS Lambda and Amazon Bedrock.
- Structured maintenance-action proposals.
- Deterministic policy evaluation that remains separate from model-generated recommendations.
- Consumer-facing responses that distinguish proposed actions from authorization decisions.
- Terraform-managed Lambda infrastructure, IAM permissions, and CloudWatch logging.
- Reproducible Lambda packaging through a local build script.
- Automated regression tests.

The AWS deployment has been validated using a simulated equipment alert and live Bedrock inference. The implementation does not connect to real industrial equipment, execute maintenance actions, or provide a production maintenance-management service.

## Future Development

Potential next steps include:

- Persisting investigation results and evidence records in durable storage.
- Adding authenticated evidence provenance and protected audit records.
- Introducing structured application logging and operational metrics for investigation outcomes.
- Expanding integration tests to cover additional live Bedrock responses and failure scenarios.
- Adding CI/CD automation for testing, packaging, and Terraform deployment.
- Evaluating Lambda memory allocation, execution duration, and Bedrock inference costs using additional measurements.

The next development priorities are improving operational visibility, deployment automation, and evidence persistence while preserving the separation between model-generated proposals and deterministic authorization.
