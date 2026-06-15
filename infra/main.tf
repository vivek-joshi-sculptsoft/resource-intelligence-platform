provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ri-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
