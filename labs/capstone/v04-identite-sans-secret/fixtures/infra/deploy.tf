# The identity the pipeline uses to publish notes-api releases.

resource "aws_s3_bucket" "releases" {
  bucket = "notes-api-releases"
}

resource "aws_iam_user" "ci_deploy" {
  name = "notes-api-ci-deploy"
}

# The key pair is copied into the repository secrets AWS_ACCESS_KEY_ID and
# AWS_SECRET_ACCESS_KEY.
resource "aws_iam_access_key" "ci_deploy" {
  user = aws_iam_user.ci_deploy.name
}

resource "aws_iam_user_policy" "ci_deploy" {
  name = "publish-releases"
  user = aws_iam_user.ci_deploy.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject"]
      Resource = "${aws_s3_bucket.releases.arn}/*"
    }]
  })
}
