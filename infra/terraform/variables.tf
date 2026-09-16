variable "aws_region" {
  description = "AWS Region used by the Learner Lab."
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "Local AWS CLI profile containing the temporary lab credentials."
  type        = string
  default     = "avance2-lab"
}

variable "project_name" {
  description = "Short project name used in AWS resource names and tags."
  type        = string
  default     = "avance2-marketplace"
}

variable "vpc_cidr" {
  description = "CIDR block for the isolated project VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "instance_type" {
  description = "Small EC2 instance type suitable for the Learner Lab."
  type        = string
  default     = "t3.micro"
}

variable "db_instance_class" {
  description = "Small single-AZ RDS instance class suitable for the Learner Lab."
  type        = string
  default     = "db.t3.micro"
}

variable "instance_profile_name" {
  description = "Pre-created AWS Academy instance profile."
  type        = string
  default     = "LabInstanceProfile"
}

