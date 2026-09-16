output "vpc_id" {
  description = "ID of the isolated marketplace VPC."
  value       = aws_vpc.marketplace.id
}

output "instance_id" {
  description = "EC2 instance running the marketplace containers."
  value       = aws_instance.marketplace.id
}

output "application_public_ip" {
  description = "Current public IP of the marketplace EC2 instance."
  value       = aws_instance.marketplace.public_ip
}

output "application_url" {
  description = "HTTP URL reserved for the marketplace application."
  value       = "http://${aws_instance.marketplace.public_dns}"
}

output "product_bucket_name" {
  description = "Private S3 bucket used by the application for product media."
  value       = local.bucket_names.products
}

output "evidence_bucket_name" {
  description = "Private S3 bucket reserved for generated evidence and reports."
  value       = local.bucket_names.evidence
}

output "database_endpoint" {
  description = "Private PostgreSQL endpoint, reachable only from the app security group."
  value       = aws_db_instance.marketplace.address
}

output "database_port" {
  description = "PostgreSQL port."
  value       = aws_db_instance.marketplace.port
}

output "database_name" {
  description = "Initial PostgreSQL database name."
  value       = aws_db_instance.marketplace.db_name
}

output "database_username" {
  description = "PostgreSQL administrator username."
  value       = aws_db_instance.marketplace.username
  sensitive   = true
}

output "database_password" {
  description = "Generated PostgreSQL password. Never commit or print this value."
  value       = random_password.database.result
  sensitive   = true
}
