
terraform {
  backend "s3" {
    bucket       = "hms-terraform-state-portfolio"
    key          = "aws-agentic-maintenance-ops/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
