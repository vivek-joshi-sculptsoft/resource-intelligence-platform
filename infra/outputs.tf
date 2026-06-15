output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "ec2_public_ip" {
  description = "EC2 Elastic IP"
  value       = aws_eip.ec2.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "rds_endpoint" {
  description = "RDS endpoint (host:port)"
  value       = "${aws_db_instance.main.address}:${aws_db_instance.main.port}"
}

output "rds_database_url" {
  description = "Full DATABASE_URL for backend .env"
  value       = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${var.db_name}"
  sensitive   = true
}

output "frontend_bucket" {
  description = "S3 bucket for frontend deployment"
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain" {
  description = "CloudFront domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "app_url" {
  description = "Application URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "tfstate_bucket" {
  description = "S3 bucket for Terraform state"
  value       = aws_s3_bucket.tfstate.id
}

output "tflock_table" {
  description = "DynamoDB table for Terraform state locking"
  value       = aws_dynamodb_table.tflock.name
}
