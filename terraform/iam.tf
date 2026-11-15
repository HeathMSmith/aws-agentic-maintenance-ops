
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    sid     = "AllowLambdaService"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_execution" {
  name = "agentic-maintenance-ops-lambda-role"

  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  permissions_boundary = "arn:aws:iam::291634988692:policy/agentic-maintenance-ops-lambda-boundary"

  tags = {
    Project   = "aws-agentic-maintenance-ops"
    ManagedBy = "Terraform"
  }
}

data "aws_iam_policy_document" "lambda_logging" {
  statement {
    sid    = "AllowLambdaLogWrites"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.lambda.arn}:*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_logging" {
  name   = "agentic-maintenance-ops-logging"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_logging.json
}

data "aws_caller_identity" "current" {}

locals {
  bedrock_model_id = "anthropic.claude-haiku-4-5-20251001-v1:0"

  bedrock_inference_profile_arn = "arn:aws:bedrock:us-east-1:${data.aws_caller_identity.current.account_id}:inference-profile/global.${local.bedrock_model_id}"

  bedrock_regional_model_arn = "arn:aws:bedrock:us-east-1::foundation-model/${local.bedrock_model_id}"

  bedrock_global_model_arn = "arn:aws:bedrock:::foundation-model/${local.bedrock_model_id}"
}

data "aws_iam_policy_document" "lambda_bedrock" {
  statement {
    sid     = "AllowInferenceProfileInvocation"
    effect  = "Allow"
    actions = ["bedrock:InvokeModel"]

    resources = [
      local.bedrock_inference_profile_arn,
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = ["us-east-1"]
    }
  }

  statement {
    sid     = "AllowRegionalModelViaInferenceProfile"
    effect  = "Allow"
    actions = ["bedrock:InvokeModel"]

    resources = [
      local.bedrock_regional_model_arn,
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = ["us-east-1"]
    }

    condition {
      test     = "StringEquals"
      variable = "bedrock:InferenceProfileArn"
      values   = [local.bedrock_inference_profile_arn]
    }
  }

  statement {
    sid     = "AllowGlobalModelViaInferenceProfile"
    effect  = "Allow"
    actions = ["bedrock:InvokeModel"]

    resources = [
      local.bedrock_global_model_arn,
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = ["unspecified"]
    }

    condition {
      test     = "StringEquals"
      variable = "bedrock:InferenceProfileArn"
      values   = [local.bedrock_inference_profile_arn]
    }
  }
}

resource "aws_iam_role_policy" "lambda_bedrock" {
  name   = "agentic-maintenance-ops-bedrock"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_bedrock.json
}
