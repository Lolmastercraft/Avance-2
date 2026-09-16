"""Despliegue AWS. Secretos por SSM SecureString; no se imprimen ni van en el tar."""
import hashlib
import io
import json
import secrets
import tarfile
import sys
from pathlib import Path
from urllib.parse import quote

import boto3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.source_digest import deployment_digest
SESSION = boto3.Session(profile_name="avance2-lab", region_name="us-east-1")


def deploy():
    gate = json.loads((ROOT / "reportes/verde/veredicto.json").read_text(encoding="utf-8"))
    if gate["verdict"] != "PERMITIR" or gate["deployment_sha256"] != deployment_digest(ROOT):
        raise RuntimeError("Despliegue bloqueado: ejecuta el pipeline sobre las fuentes actuales.")
    state = json.loads((ROOT / "infra/terraform/terraform.tfstate").read_text())
    outputs = {k: v["value"] for k, v in state["outputs"].items()}
    s3, ssm = SESSION.client("s3"), SESSION.client("ssm")
    parameter = "/avance2-marketplace/bootstrap"
    try:
        config = json.loads(ssm.get_parameter(Name=parameter, WithDecryption=True)["Parameter"]["Value"])
    except ssm.exceptions.ParameterNotFound:
        host = outputs["database_endpoint"]
        suffix = f"@{host}:5432/marketplace?sslmode=verify-full&sslrootcert=/srv/certs/rds-ca-bundle.crt"
        config = {
            "DATABASE_URL": "postgresql+psycopg://marketplace_runtime:" + quote(secrets.token_urlsafe(36), safe="") + suffix,
            "admin_url": "postgresql+psycopg://" + outputs["database_username"] + ":" + quote(outputs["database_password"], safe="") + suffix,
            "SECRET_KEY": secrets.token_hex(48), "AWS_REGION": "us-east-1",
            "PRODUCT_BUCKET": outputs["product_bucket_name"],
        }
        ssm.put_parameter(Name=parameter, Type="SecureString", Value=json.dumps(config),
                          Description="Marketplace lab bootstrap; never commit these credentials")
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name in ("app", "Dockerfile", "docker-compose.yml", "requirements.txt", "deploy/nginx.conf", "deploy/rds-ca-bundle.crt", "scripts/remote_setup.sh"):
            path = ROOT / name
            paths = path.rglob("*") if path.is_dir() else [path]
            for item in paths:
                if item.is_file() and "__pycache__" not in item.parts:
                    archive.add(item, arcname=item.relative_to(ROOT).as_posix())
    payload = buffer.getvalue()
    digest = hashlib.sha256(payload).hexdigest()
    key = f"deployment/marketplace-{digest[:16]}.tgz"
    s3.put_object(Bucket=outputs["evidence_bucket_name"], Key=key, Body=payload, ServerSideEncryption="AES256")
    commands = ["set -eu", "umask 077", "cd /opt/marketplace",
                f"aws s3 cp s3://{outputs['evidence_bucket_name']}/{key} /opt/marketplace/release.tgz --only-show-errors",
                f"echo '{digest}  release.tgz' | sha256sum -c -",
                "tar -xzf release.tgz", "bash scripts/remote_setup.sh"]
    result = ssm.send_command(InstanceIds=[outputs["instance_id"]], DocumentName="AWS-RunShellScript",
                              Parameters={"commands": commands, "executionTimeout": ["1800"]},
                              Comment="Deploy Mercado Nube application")
    print(json.dumps({"command_id": result["Command"]["CommandId"], "instance_id": outputs["instance_id"], "source_sha256": digest}))


if __name__ == "__main__":
    deploy()
