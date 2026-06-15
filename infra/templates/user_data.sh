#!/bin/bash
set -euo pipefail

# Log everything for debugging
exec > /var/log/user-data.log 2>&1

echo "=== RI Platform EC2 Bootstrap ==="
echo "Environment: ${environment}"

# Install Docker
dnf update -y
dnf install -y docker git
systemctl enable docker
systemctl start docker

# Install Docker Compose v2
DOCKER_CONFIG=/usr/local/lib/docker
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Create app directory
mkdir -p /opt/ri-platform
cd /opt/ri-platform

# Write environment file for Docker Compose
cat > .env <<'ENVFILE'
APP_NAME=Resource Intelligence Platform
DEBUG=false
DATABASE_URL=postgresql+asyncpg://${db_username}:${db_password}@${db_host}:${db_port}/${db_name}
DATABASE_ECHO=false
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_REFRESH_SECRET_KEY=$(openssl rand -hex 32)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["https://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"]
SENTRY_DSN=
ENVFILE

echo "=== Bootstrap complete ==="
echo "Clone the repo and run docker compose to start the application."
