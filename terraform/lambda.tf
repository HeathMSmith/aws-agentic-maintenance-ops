
resource "aws_lambda_function" "maintenance_investigation" {
  function_name = "agentic-maintenance-ops"

  role    = aws_iam_role.lambda_execution.arn
  handler = "lambda_handler.lambda_handler"

  runtime       = "python3.13"
  architectures = ["x86_64"]

  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  memory_size = 512
  timeout     = 120

  depends_on = [
    aws_iam_role_policy.lambda_logging,
    aws_iam_role_policy.lambda_bedrock,
    aws_cloudwatch_log_group.lambda,
  ]

  tags = {
    Project   = "aws-agentic-maintenance-ops"
    ManagedBy = "Terraform"
  }
}
