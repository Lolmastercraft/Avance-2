resource "aws_security_group" "app" {
  name        = "${local.name_prefix}-app-sg"
  description = "Public HTTP access for the marketplace application"
  vpc_id      = aws_vpc.marketplace.id

  tags = {
    Name = "${local.name_prefix}-app-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "app_http" {
  security_group_id = aws_security_group.app.id
  description       = "Marketplace HTTP"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "app_https" {
  security_group_id = aws_security_group.app.id
  description       = "Marketplace HTTPS"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  description       = "Required outbound access for updates, S3, RDS and SSM"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group" "database" {
  name        = "${local.name_prefix}-db-sg"
  description = "PostgreSQL accessible only from the marketplace EC2 security group"
  vpc_id      = aws_vpc.marketplace.id

  tags = {
    Name = "${local.name_prefix}-db-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "database_from_app" {
  security_group_id            = aws_security_group.database.id
  description                  = "PostgreSQL from application instances only"
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.app.id
}

resource "aws_vpc_security_group_egress_rule" "database_all" {
  security_group_id = aws_security_group.database.id
  description       = "RDS managed outbound traffic"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

