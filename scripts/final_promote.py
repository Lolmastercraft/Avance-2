"""Promocion con gate y hash; no acepta el candidato rojo ni muestra secretos."""
import argparse
import hashlib
import io
import json
import secrets
import sys
import tarfile
from pathlib import Path

from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.source_digest import deployment_digest
from scripts.final_lab import session, QA


def main():
    p = argparse.ArgumentParser()
    p.add_argument("target", choices=["qa", "production"])
    args = p.parse_args()
    gate = json.loads((ROOT / "reportes/final/verde/veredicto.json").read_text())
    if gate["verdict"] != "PERMITIR" or gate["deployment_sha256"] != deployment_digest(ROOT):
        raise RuntimeError("BLOQUEAR: falta verde o las fuentes cambiaron")
    aws = session()
    ssm = aws.client("ssm")
    parameter = "/avance2-marketplace/bootstrap"
    instance = QA
    if args.target == "production":
        outputs = json.loads((ROOT / "infra/final/terraform.tfstate").read_text())["outputs"]
        instance = outputs["instance_id"]["value"]
        parameter = "/entrega-final-marketplace/production"
        try:
            ssm.get_parameter(Name=parameter)
        except ssm.exceptions.ParameterNotFound:
            config = json.loads(ssm.get_parameter(Name="/avance2-marketplace/bootstrap", WithDecryption=True)["Parameter"]["Value"])
            config["admin_url"] = make_url(config["admin_url"]).set(database="marketplace_production").render_as_string(hide_password=False)
            config["DATABASE_URL"] = make_url(config["DATABASE_URL"]).set(database="marketplace_production", username="marketplace_prod", password=secrets.token_urlsafe(36)).render_as_string(hide_password=False)
            config["SECRET_KEY"] = secrets.token_hex(48)
            ssm.put_parameter(Name=parameter, Type="SecureString", Value=json.dumps(config))
    manifest = {"environment": args.target, "instance_id": instance, "remediation_commit": "b0b127b",
                "deployment_sha256": gate["deployment_sha256"], "qa_gate_utc": gate["utc"]}
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name in ("app", ".dockerignore", "Dockerfile", "docker-compose.yml", "requirements.txt", "deploy/nginx.conf", "deploy/rds-ca-bundle.crt", "scripts/final_remote_setup.sh"):
            path = ROOT / name
            for item in path.rglob("*") if path.is_dir() else [path]:
                if item.is_file() and "__pycache__" not in item.parts:
                    archive.add(item, arcname=item.relative_to(ROOT).as_posix())
        data = json.dumps(manifest, indent=2).encode()
        info = tarfile.TarInfo("release-final.json")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    payload = buffer.getvalue()
    sha = hashlib.sha256(payload).hexdigest()
    key = f"final/releases/{args.target}-{sha[:16]}.tgz"
    bucket = "avance2-marketplace-evidence-468504542046"
    aws.client("s3").put_object(Bucket=bucket, Key=key, Body=payload, ServerSideEncryption="AES256")
    commands = ["set -eu", "umask 077", "cd /opt/marketplace",
                f"aws s3 cp s3://{bucket}/{key} final-release.tgz --only-show-errors",
                f"echo '{sha}  final-release.tgz' | sha256sum -c -", "tar -xzf final-release.tgz",
                f"bash scripts/final_remote_setup.sh {parameter}", "cat release-final.json"]
    result = ssm.send_command(InstanceIds=[instance], DocumentName="AWS-RunShellScript",
                             Parameters={"commands": commands, "executionTimeout": ["1800"]})
    record = dict(manifest, command_id=result["Command"]["CommandId"], artifact_sha256=sha, artifact_key=key)
    out = ROOT / "reportes/final" / f"promocion_{args.target}.json"
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record))


if __name__ == "__main__":
    main()
