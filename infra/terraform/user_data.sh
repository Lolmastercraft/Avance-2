#!/bin/bash
set -euxo pipefail

dnf update -y
dnf install -y docker git jq

systemctl enable --now docker
systemctl enable --now amazon-ssm-agent || true
usermod -aG docker ec2-user

install -d -m 0755 /usr/local/lib/docker/cli-plugins
curl --fail --location --retry 3 \
  "https://github.com/docker/compose/releases/download/v2.35.1/docker-compose-linux-x86_64" \
  --output /usr/local/lib/docker/cli-plugins/docker-compose
chmod 0755 /usr/local/lib/docker/cli-plugins/docker-compose
ln -sf /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

install -d -o ec2-user -g ec2-user -m 0750 /opt/marketplace

docker --version > /opt/marketplace/bootstrap-status.txt
docker compose version >> /opt/marketplace/bootstrap-status.txt
date --iso-8601=seconds >> /opt/marketplace/bootstrap-status.txt
chown ec2-user:ec2-user /opt/marketplace/bootstrap-status.txt

