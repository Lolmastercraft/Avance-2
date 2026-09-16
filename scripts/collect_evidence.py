"""Exporta evidencia real y no sensible de AWS y de los contenedores."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reportes/aws"
OUT.mkdir(parents=True, exist_ok=True)
session = boto3.Session(profile_name="avance2-lab", region_name="us-east-1")
ssm = session.client("ssm")
instance_id = "i-06f5d7a26aa4f1498"


def command(commands):
    command_id = ssm.send_command(InstanceIds=[instance_id], DocumentName="AWS-RunShellScript",
                                  Parameters={"commands": commands}, Comment="Read-only marketplace evidence")["Command"]["CommandId"]
    for _ in range(30):
        time.sleep(2)
        result = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        if result["Status"] not in {"Pending", "InProgress", "Delayed"}:
            if result["Status"] != "Success":
                raise RuntimeError(result["StandardErrorContent"])
            return result["StandardOutputContent"]
    raise TimeoutError("SSM command pending")


def main():
    certificate = command(["cat /opt/marketplace/deploy/tls/server.crt"])
    (ROOT / "deploy/lab-server.crt").write_text(certificate, encoding="ascii")
    containers = command(["cd /opt/marketplace", "docker compose ps --format json",
                          "docker compose exec -T api id", "docker compose exec -T notifications id",
                          "docker compose exec -T api python -c \"from app.models import database; from sqlalchemy import text; e,_=database(); c=e.connect(); print('RDS_TLS_AND_ROLE:',dict(c.execute(text('SELECT current_user, ssl, version FROM pg_stat_ssl WHERE pid=pg_backend_pid()')).mappings().one())); print('DATA_COUNTS:',dict(c.execute(text('SELECT (SELECT count(*) FROM users) AS users, (SELECT count(*) FROM products) AS products, (SELECT count(*) FROM orders) AS orders, (SELECT count(*) FROM notifications WHERE status=\\\'enviada\\\') AS confirmations')).mappings().one()))\""])
    (OUT / "containers_rds.txt").write_text(containers, encoding="utf-8")
    ec2 = session.client("ec2")
    instance = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]
    db = session.client("rds").describe_db_instances(DBInstanceIdentifier="avance2-marketplace-postgres")["DBInstances"][0]
    s3 = session.client("s3")
    buckets = []
    for purpose in ("products", "evidence"):
        name = f"avance2-marketplace-{purpose}-468504542046"
        objects = s3.list_objects_v2(Bucket=name, Prefix="products/").get("Contents", []) if purpose == "products" else []
        buckets.append({"name": name, "public_access": s3.get_public_access_block(Bucket=name)["PublicAccessBlockConfiguration"],
                        "encryption": s3.get_bucket_encryption(Bucket=name)["ServerSideEncryptionConfiguration"],
                        "versioning": s3.get_bucket_versioning(Bucket=name).get("Status"),
                        "policy": json.loads(s3.get_bucket_policy(Bucket=name)["Policy"]),
                        "product_objects": [{"Key": x["Key"], "Size": x["Size"]} for x in objects]})
    evidence = {"utc": datetime.now(timezone.utc).isoformat(), "region": "us-east-1",
                "instance": {k: instance[k] for k in ("InstanceId", "InstanceType", "VpcId", "State", "PublicIpAddress", "MetadataOptions", "SecurityGroups")},
                "rds": {k: db[k] for k in ("DBInstanceIdentifier", "EngineVersion", "DBInstanceStatus", "StorageEncrypted", "PubliclyAccessible", "Endpoint", "VpcSecurityGroups", "DBSubnetGroup")},
                "buckets": buckets,
                "security_groups": ec2.describe_security_groups(GroupIds=[x["GroupId"] for x in instance["SecurityGroups"]] + [x["VpcSecurityGroupId"] for x in db["VpcSecurityGroups"]])["SecurityGroups"]}
    (OUT / "infraestructura.json").write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print("Evidence saved: containers, RDS TLS/runtime role, S3 objects and security controls.")


if __name__ == "__main__":
    main()
