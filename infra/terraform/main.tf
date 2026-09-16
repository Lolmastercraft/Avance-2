data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ssm_parameter" "amazon_linux_2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

data "aws_iam_instance_profile" "lab" {
  name = var.instance_profile_name
}

locals {
  name_prefix = lower(var.project_name)

  common_tags = {
    Project     = "Avance 2 Marketplace"
    Environment = "LearnerLab"
    ManagedBy   = "Terraform"
    Owner       = "student"
  }

  bucket_names = {
    products = "${local.name_prefix}-products-${data.aws_caller_identity.current.account_id}"
    evidence = "${local.name_prefix}-evidence-${data.aws_caller_identity.current.account_id}"
  }
}

