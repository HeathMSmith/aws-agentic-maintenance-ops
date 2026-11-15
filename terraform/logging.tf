
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/agentic-maintenance-ops"
  retention_in_days = 7

  tags = {
    Project   = "aws-agentic-maintenance-ops"
    ManagedBy = "Terraform"
  }
}
