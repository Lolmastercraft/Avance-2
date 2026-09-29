terraform {
  required_version = ">= 1.8.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

data "aws_instance" "qa" {
  instance_id = "i-06f5d7a26aa4f1498"
}

resource "aws_instance" "production" {
  ami                         = data.aws_instance.qa.ami
  instance_type               = "t3.micro"
  subnet_id                   = data.aws_instance.qa.subnet_id
  vpc_security_group_ids      = data.aws_instance.qa.vpc_security_group_ids
  iam_instance_profile        = "LabInstanceProfile"
  associate_public_ip_address = true
  user_data                   = file("${path.module}/../terraform/user_data.sh")

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }
  root_block_device {
    volume_size           = 10
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }
  credit_specification {
    cpu_credits = "standard"
  }
  tags = {
    Name        = "entrega-final-marketplace-production"
    Environment = "production-academic"
    Project     = "LSCA2314-EntregaFinal"
  }
}

output "instance_id" {
  value = aws_instance.production.id
}
output "public_ip" {
  value = aws_instance.production.public_ip
}
