# AWS Academy explicitly denies s3:GetBucketObjectLockConfiguration. The
# standard aws_s3_bucket resource always calls that API during refresh, so the
# bucket creation itself is performed idempotently through the AWS CLI. All
# security controls remain declarative Terraform resources below.
resource "terraform_data" "s3_bucket" {
  for_each = local.bucket_names

  input = {
    bucket  = each.value
    purpose = each.key
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-NoProfile", "-Command"]
    command     = <<-EOT
      $bucket = "${each.value}"
      aws s3api head-bucket --bucket $bucket --profile "${var.aws_profile}" --region "${var.aws_region}" 2>$null
      if ($LASTEXITCODE -ne 0) {
        aws s3api create-bucket --bucket $bucket --profile "${var.aws_profile}" --region "${var.aws_region}"
        if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el bucket $bucket" }
      }
      aws s3api put-bucket-tagging --bucket $bucket --profile "${var.aws_profile}" --region "${var.aws_region}" --tagging "TagSet=[{Key=Name,Value=$bucket},{Key=Purpose,Value=${each.key}},{Key=Project,Value=Avance2Marketplace},{Key=Environment,Value=LearnerLab},{Key=ManagedBy,Value=Terraform},{Key=Owner,Value=student}]"
      if ($LASTEXITCODE -ne 0) { throw "No se pudieron etiquetar los buckets" }
    EOT
  }
}

resource "aws_s3_bucket_public_access_block" "project" {
  for_each = local.bucket_names

  bucket                  = each.value
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  depends_on = [terraform_data.s3_bucket]
}

resource "aws_s3_bucket_ownership_controls" "project" {
  for_each = local.bucket_names

  bucket = each.value

  rule {
    object_ownership = "BucketOwnerEnforced"
  }

  depends_on = [terraform_data.s3_bucket]
}

resource "aws_s3_bucket_server_side_encryption_configuration" "project" {
  for_each = local.bucket_names

  bucket = each.value

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }

  depends_on = [terraform_data.s3_bucket]
}

resource "aws_s3_bucket_versioning" "project" {
  for_each = local.bucket_names

  bucket = each.value

  versioning_configuration {
    status = "Enabled"
  }

  depends_on = [terraform_data.s3_bucket]
}

resource "aws_s3_bucket_lifecycle_configuration" "project" {
  for_each = local.bucket_names

  bucket = each.value

  rule {
    id     = "cleanup-old-versions"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  depends_on = [aws_s3_bucket_versioning.project]
}

resource "aws_s3_bucket_policy" "tls_only" {
  for_each = local.bucket_names

  bucket = each.value
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          "arn:aws:s3:::${each.value}",
          "arn:aws:s3:::${each.value}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.project]
}

