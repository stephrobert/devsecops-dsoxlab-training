terraform {
  required_version = ">= 1.11"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# The API is reached through the load balancer of the VPC, never directly from
# the Internet. There is no SSH: an administrator opens a session through the
# cloud provider's session manager, which is logged.
resource "aws_security_group" "notes_api" {
  name        = "notes-api"
  description = "Acces a notes-api depuis le load balancer"

  ingress {
    description = "API, depuis le VPC"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

# One key for the data of notes-api, rotated every year.
resource "aws_kms_key" "notes_api" {
  description         = "notes-api data"
  enable_key_rotation = true
}

resource "aws_s3_bucket" "exports" {
  bucket = "notes-api-exports"
}

resource "aws_s3_bucket_public_access_block" "exports" {
  bucket                  = aws_s3_bucket.exports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "exports" {
  bucket = aws_s3_bucket.exports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.notes_api.arn
    }
  }
}
