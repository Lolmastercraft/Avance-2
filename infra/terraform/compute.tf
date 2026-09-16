resource "aws_instance" "marketplace" {
  ami                    = data.aws_ssm_parameter.amazon_linux_2023.value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public_app.id
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = data.aws_iam_instance_profile.lab.name

  associate_public_ip_address = true
  user_data                   = file("${path.module}/user_data.sh")
  user_data_replace_on_change = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
    instance_metadata_tags      = "enabled"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 10
    encrypted             = true
    delete_on_termination = true
  }

  credit_specification {
    cpu_credits = "standard"
  }

  tags = {
    Name = "${local.name_prefix}-app"
  }

  depends_on = [aws_internet_gateway.marketplace]
}
