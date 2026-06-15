# Infrastructure — Terraform

Terraform configs for provisioning the RI Platform on AWS (ap-south-1).

## Architecture

```
CloudFront (HTTPS)
├── /* → S3 (React frontend, cached)
└── /api/* → EC2 (FastAPI, no cache)

EC2 (t3.small) ── Docker Compose
├── Nginx (reverse proxy)
├── FastAPI (uvicorn, 2 workers)
├── Celery worker
└── Redis 7

RDS PostgreSQL 16 (db.t4g.micro, private subnet)
```

Estimated cost: ~$36/mo (see `techstack/cost-estimate.md`).

## Prerequisites

- [Terraform >= 1.5](https://developer.hashicorp.com/terraform/install)
- AWS CLI configured with credentials (`aws configure`)
- An EC2 key pair created in ap-south-1 (`aws ec2 create-key-pair --key-name ri-platform-prod --region ap-south-1`)

## First-Time Setup

### 1. Initialize (local state)

```bash
cd infra
terraform init
```

### 2. Review and apply

```bash
# Dev environment
terraform plan -var-file=envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars

# Production
terraform plan -var-file=envs/prod.tfvars
terraform apply -var-file=envs/prod.tfvars
```

### 3. Migrate to remote state

After the first apply creates the S3 bucket and DynamoDB table:

1. Open `backend.tf`
2. Uncomment the `terraform { backend "s3" { ... } }` block
3. Run `terraform init -migrate-state`
4. Confirm the migration

### 4. Deploy the application

After infrastructure is provisioned:

```bash
# SSH into EC2
ssh -i ~/.ssh/ri-platform-prod.pem ec2-user@$(terraform output -raw ec2_public_ip)

# On the EC2 instance
cd /opt/ri-platform
git clone <your-repo-url> .
docker compose -f docker-compose.dev.yml up -d

# Deploy frontend to S3
cd frontend && npm run build
aws s3 sync dist/ s3://$(terraform output -raw frontend_bucket) --delete
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

## Environment-Specific Configs

| File | Environment | Notes |
|------|-------------|-------|
| `envs/dev.tfvars` | Development | Open SSH, smaller storage |
| `envs/staging.tfvars` | Staging | Same specs as dev |
| `envs/prod.tfvars` | Production | Restricted SSH, deletion protection on RDS |

**Important:** Update `db_password` and `admin_ssh_cidr` in tfvars before applying. Never commit real passwords — use `terraform.tfvars` locally (gitignored) or a secrets manager.

## Outputs

After `terraform apply`, key outputs:

| Output | Description |
|--------|-------------|
| `ec2_public_ip` | Elastic IP for SSH and direct access |
| `rds_endpoint` | PostgreSQL connection endpoint |
| `cloudfront_domain` | Application URL (HTTPS) |
| `frontend_bucket` | S3 bucket name for frontend deploys |
| `cloudfront_distribution_id` | For cache invalidation |

View all: `terraform output`

## Teardown

```bash
terraform destroy -var-file=envs/dev.tfvars
```

Production has `deletion_protection = true` on RDS. Disable it first:
```bash
terraform apply -var-file=envs/prod.tfvars -var="db_password=..." -target=aws_db_instance.main
# Then destroy
terraform destroy -var-file=envs/prod.tfvars
```

## Custom Domain (Optional)

1. Create a Route 53 hosted zone for your domain
2. Set `domain_name` and `route53_zone_id` in your tfvars
3. Apply — Terraform creates ACM cert, DNS validation, and CloudFront alias
