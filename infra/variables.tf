variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ri-platform"
}

# ── VPC ──

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (RDS)"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

# ── EC2 ──

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "ec2_key_pair_name" {
  description = "Name of existing EC2 key pair for SSH access"
  type        = string
}

variable "ec2_volume_size" {
  description = "EBS root volume size in GB"
  type        = number
  default     = 30
}

variable "admin_ssh_cidr" {
  description = "CIDR allowed for SSH access (e.g. your office IP/32)"
  type        = string
}

# ── RDS ──

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "ri_platform"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "ripadmin"
  sensitive   = true
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "db_storage_gb" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_storage_gb" {
  description = "Max autoscaling storage in GB"
  type        = number
  default     = 100
}

# ── CloudFront / Domain ──

variable "domain_name" {
  description = "Custom domain name (leave empty to use CloudFront default)"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone ID (required if domain_name is set)"
  type        = string
  default     = ""
}
