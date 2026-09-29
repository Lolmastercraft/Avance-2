"""Operaciones del laboratorio final. Lee credenciales externas; nunca las imprime."""
import argparse
import json
import re
import hashlib
import io
import subprocess
import tarfile
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
QA = "i-06f5d7a26aa4f1498"


def session():
    raw = Path(r"C:\Users\multi\Downloads\CLI.txt").read_text(encoding="utf-8-sig")
    values = dict(re.findall(r"(?im)^\s*(aws_access_key_id|aws_secret_access_key|aws_session_token)\s*=\s*([^\r\n]+)", raw))
    return boto3.Session(region_name="us-east-1", **{k: v.strip().strip("\"'") for k, v in values.items()})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["send", "result", "inspect", "upload", "download"])
    p.add_argument("--instance", default=QA)
    p.add_argument("--file")
    p.add_argument("--command-id")
    args = p.parse_args()
    aws = session()
    ssm = aws.client("ssm")
    if args.action == "upload":
        tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as archive:
            for name in tracked:
                if name.startswith(("reportes/", "entrega/", "docs/capturas/")) or name.endswith((".mp4", ".docx", ".png", ".pdf")):
                    continue
                archive.add(ROOT / name, arcname=name)
        payload = buf.getvalue()
        sha = hashlib.sha256(payload).hexdigest()
        key = f"final/source-{sha[:16]}.tgz"
        aws.client("s3").put_object(Bucket="avance2-marketplace-evidence-468504542046", Key=key, Body=payload, ServerSideEncryption="AES256")
        print(json.dumps({"key": key, "sha256": sha, "bytes": len(payload)}))
    elif args.action == "download":
        target = ROOT / "reportes" / "final"
        target.mkdir(parents=True, exist_ok=True)
        payload = aws.client("s3").get_object(Bucket="avance2-marketplace-evidence-468504542046", Key=args.file)["Body"].read()
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
            archive.extractall(target, filter="data")
        print("Reportes de QA descargados")
    elif args.action == "send":
        commands = Path(args.file).read_text(encoding="utf-8").splitlines()
        result = ssm.send_command(InstanceIds=[args.instance], DocumentName="AWS-RunShellScript",
                                 Parameters={"commands": commands, "executionTimeout": ["3600"]},
                                 Comment="Entrega final marketplace")
        print(result["Command"]["CommandId"])
    elif args.action == "result":
        result = ssm.get_command_invocation(InstanceId=args.instance, CommandId=args.command_id)
        print(json.dumps({k: result[k] for k in ("Status", "ResponseCode", "StandardOutputContent", "StandardErrorContent")}, ensure_ascii=False))
    else:
        instance = aws.client("ec2").describe_instances(InstanceIds=[args.instance])["Reservations"][0]["Instances"][0]
        print(json.dumps({k: instance.get(k) for k in ("InstanceId", "ImageId", "InstanceType", "SubnetId", "VpcId", "SecurityGroups", "IamInstanceProfile", "PublicIpAddress", "State")}, default=str))


if __name__ == "__main__":
    main()
