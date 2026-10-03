# The identity the pipeline uses to publish notes-api releases. No user, no
# access key: GitHub Actions presents a signed OIDC token, and AWS trades it
# for one-hour credentials of the role below.

resource "aws_s3_bucket" "releases" {
  bucket = "notes-api-releases"
}

resource "aws_s3_bucket_versioning" "releases" {
  bucket = aws_s3_bucket.releases.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "releases" {
  bucket                  = aws_s3_bucket.releases.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "releases" {
  bucket = aws_s3_bucket.releases.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.notes_api.arn
    }
  }
}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

# Who may assume the role: github-oidc-trust.json, reviewed as a file. Only a
# token issued for a push on main of acme/notes-api matches.
resource "aws_iam_role" "ci_deploy" {
  name                 = "notes-api-ci-deploy"
  assume_role_policy   = file("${path.module}/github-oidc-trust.json")
  max_session_duration = 3600
}

resource "aws_iam_role_policy" "ci_deploy" {
  name = "publish-releases"
  role = aws_iam_role.ci_deploy.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject"]
      Resource = "${aws_s3_bucket.releases.arn}/*"
    }]
  })
}
