#!/bin/bash
set -euo pipefail
cd /opt/marketplace
umask 077
aws ssm get-parameter --name /avance2-marketplace/bootstrap --with-decryption --region us-east-1 --query Parameter.Value --output text > .bootstrap.json
python3 - <<'PY'
import json
from pathlib import Path
config=json.loads(Path('.bootstrap.json').read_text())
Path('.env').write_text(''.join(k+'='+v+'\n' for k,v in config.items() if k != 'admin_url'))
PY
mkdir -p deploy/tls
if [ ! -f deploy/tls/server.key ]; then
  TOKEN=$(curl -fsS -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' http://169.254.169.254/latest/api/token)
  IP=$(curl -fsS -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)
  DNS=$(curl -fsS -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-hostname)
  openssl req -x509 -nodes -newkey rsa:2048 -days 30 -keyout deploy/tls/server.key -out deploy/tls/server.crt -subj '/CN=Mercado Nube Learner Lab' -addext "subjectAltName=IP:$IP,DNS:$DNS" 2>/dev/null
fi
chmod 755 deploy deploy/tls
chown 101:101 deploy/tls/server.key
chmod 400 deploy/tls/server.key
chmod 444 deploy/tls/server.crt
docker compose build
docker run --rm --user 0 --network host -v /opt/marketplace/.bootstrap.json:/run/bootstrap.json:ro mercado-nube-api:avance2 python -m app.bootstrap
docker compose up -d --wait --wait-timeout 180
docker compose ps
echo MARKETPLACE_DEPLOYED
