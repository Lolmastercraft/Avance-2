resource "random_password" "database" {
  length           = 24
  special          = true
  override_special = "!#$%&*+-_=?"
}

resource "aws_db_subnet_group" "marketplace" {
  name = "${local.name_prefix}-db-subnets"
  subnet_ids = [
    aws_subnet.private_db_a.id,
    aws_subnet.private_db_b.id
  ]

  tags = {
    Name = "${local.name_prefix}-db-subnets"
  }
}

resource "aws_db_instance" "marketplace" {
  identifier = "${local.name_prefix}-postgres"

  engine         = "postgres"
  engine_version = "16.14"
  instance_class = var.db_instance_class

  db_name  = "marketplace"
  username = "marketadmin"
  password = random_password.database.result
  port     = 5432

  allocated_storage      = 20
  storage_type           = "gp3"
  storage_encrypted      = true
  publicly_accessible    = false
  multi_az               = false
  db_subnet_group_name   = aws_db_subnet_group.marketplace.name
  vpc_security_group_ids = [aws_security_group.database.id]

  backup_retention_period    = 1
  backup_window              = "07:00-07:30"
  maintenance_window         = "sun:08:00-sun:08:30"
  auto_minor_version_upgrade = true

  performance_insights_enabled = false
  monitoring_interval          = 0
  deletion_protection          = false
  skip_final_snapshot          = true
  copy_tags_to_snapshot        = true
  apply_immediately            = true

  tags = {
    Name = "${local.name_prefix}-postgres"
  }
}

