# Uncomment after creating the S3 bucket and DynamoDB table for state storage.
# First run: use local backend, then migrate with `terraform init -migrate-state`.
#
# terraform {
#   backend "s3" {
#     bucket         = "ri-platform-tfstate"
#     key            = "infra/terraform.tfstate"
#     region         = "ap-south-1"
#     dynamodb_table = "ri-platform-tflock"
#     encrypt        = true
#   }
# }

# Bootstrap resources for remote state — run once, then uncomment the backend above.

resource "aws_s3_bucket" "tfstate" {
  bucket = "${var.project_name}-tfstate"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tflock" {
  name         = "${var.project_name}-tflock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
