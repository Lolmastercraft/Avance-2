"""Recoge datos reales de AWS y SSM, sin credenciales ni contenido de usuarios."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.final_lab import session, QA

OUT = ROOT / "reportes/final"
PROD = "i-02be4a02d659f23c3"


def command(ssm, instance, commands):
    cid = ssm.send_command(InstanceIds=[instance], DocumentName="AWS-RunShellScript", Parameters={"commands": commands})["Command"]["CommandId"]
    for _ in range(30):
        time.sleep(2)
        try:
            result = ssm.get_command_invocation(InstanceId=instance, CommandId=cid)
        except ssm.exceptions.InvocationDoesNotExist:
            continue
        if result["Status"] not in {"Pending", "InProgress", "Delayed"}:
            if result["Status"] != "Success":
                raise RuntimeError(f"SSM {cid}: {result['Status']}")
            return result["StandardOutputContent"], cid
    raise TimeoutError(cid)


def main():
    aws = session()
    ssm = aws.client("ssm")
    instances = []
    for env, instance in (("qa", QA), ("production", PROD)):
        raw = aws.client("ec2").describe_instances(InstanceIds=[instance])["Reservations"][0]["Instances"][0]
        item = {k: raw[k] for k in ("InstanceId", "State", "PublicIpAddress", "PrivateIpAddress", "InstanceType", "LaunchTime", "Tags", "VpcId", "SubnetId")}
        item["environment"] = env
        instances.append(item)
        cert, _ = command(ssm, instance, ["cat /opt/marketplace/deploy/tls/server.crt"])
        (OUT / f"{env}-server.crt").write_text(cert, encoding="ascii")
        commands = ["set -eu", "cd /opt/marketplace", "date -u", "cat release-final.json", "docker compose ps --format json", "docker compose exec -T api id",
                    "docker compose exec -T api python -c \"from app.models import database; from sqlalchemy import text; e,_=database(); c=e.connect(); print(dict(c.execute(text('SELECT current_database() AS database, current_user AS role, ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')).mappings().one()))\"",
                    "docker compose exec -T api python -c \"import json,urllib.request; r=json.load(urllib.request.urlopen('http://mailpit:8025/api/v1/messages')); print('SMTP_SANDBOX_TOTAL:',r['total']); print('SUBJECTS:',[x['Subject'] for x in r.get('messages',[])])\""]
        output, cid = command(ssm, instance, commands)
        (OUT / f"estado_{env}.txt").write_text(f"AWS Systems Manager | {instance} | command {cid}\n" + output, encoding="utf-8")
    data = {"utc": datetime.now(timezone.utc).isoformat(), "region": "us-east-1", "instances": instances}
    (OUT / "aws_instances.json").write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print("Evidencia real de ambas instancias, contenedores, TLS y bases separadas guardada")


if __name__ == "__main__":
    main()
