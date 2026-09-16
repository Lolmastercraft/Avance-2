resource "aws_vpc" "marketplace" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

resource "aws_internet_gateway" "marketplace" {
  vpc_id = aws_vpc.marketplace.id

  tags = {
    Name = "${local.name_prefix}-igw"
  }
}

resource "aws_subnet" "public_app" {
  vpc_id                  = aws_vpc.marketplace.id
  cidr_block              = "10.42.10.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name_prefix}-public-app"
    Tier = "public"
  }
}

resource "aws_subnet" "private_db_a" {
  vpc_id            = aws_vpc.marketplace.id
  cidr_block        = "10.42.20.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name = "${local.name_prefix}-private-db-a"
    Tier = "private"
  }
}

resource "aws_subnet" "private_db_b" {
  vpc_id            = aws_vpc.marketplace.id
  cidr_block        = "10.42.21.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = {
    Name = "${local.name_prefix}-private-db-b"
    Tier = "private"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.marketplace.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.marketplace.id
  }

  tags = {
    Name = "${local.name_prefix}-public-rt"
  }
}

resource "aws_route_table_association" "public_app" {
  subnet_id      = aws_subnet.public_app.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.marketplace.id

  tags = {
    Name = "${local.name_prefix}-private-rt"
  }
}

resource "aws_route_table_association" "private_db_a" {
  subnet_id      = aws_subnet.private_db_a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_db_b" {
  subnet_id      = aws_subnet.private_db_b.id
  route_table_id = aws_route_table.private.id
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.marketplace.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.public.id, aws_route_table.private.id]

  tags = {
    Name = "${local.name_prefix}-s3-endpoint"
  }
}

