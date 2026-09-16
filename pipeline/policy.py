"""Controles explícitos del proyecto; no sustituyen una auditoría de producción."""
import json
import re
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = ("app", "infra", "pipeline", "scripts", "tests", "deploy", ".github", "docs")
EXCLUDED = {".terraform", "__pycache__", "tls"}
EXTENSIONS = {".py", ".tf", ".yml", ".yaml", ".sh", ".ps1", ".html", ".js", ".cjs", ".toml", ".md", ".txt"}


def source_files():
    for folder in SOURCE_DIRS:
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and path.suffix in EXTENSIONS and not EXCLUDED.intersection(path.parts):
                yield path
    for name in ("Dockerfile", "docker-compose.yml", "requirements.txt", ".env.example"):
        yield ROOT / name


def secrets_scan():
    patterns = {
        "aws-access-id": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
        "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
        "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "embedded-database-password": re.compile(r"postgres(?:ql)?(?:\+psycopg)?://[^\s:'\"]+:[A-Za-z0-9_!@%+\-]{8,}@"),
        "literal-credential": re.compile(r'''(?im)^\s*(?:SECRET_KEY|AWS_SECRET_ACCESS_KEY|aws_secret_access_key|password|DB_PASSWORD)\s*=\s*["']([A-Za-z0-9+/=_!@#$%&*\-]{12,})["']'''),
    }
    findings = []
    for path in source_files():
        value = path.read_text(encoding="utf-8")
        for rule, pattern in patterns.items():
            for match in pattern.finditer(value):
                findings.append({"rule": rule, "file": path.relative_to(ROOT).as_posix(),
                                 "line": value[:match.start()].count("\n") + 1, "value": "REDACTED"})
    executable = os.environ.get("GITLEAKS_BIN", str(ROOT / ".tools/gitleaks/gitleaks.exe") if os.name == "nt" else "gitleaks")
    with tempfile.TemporaryDirectory(prefix="marketplace-secrets-") as directory:
        staging = Path(directory) / "source"
        staging.mkdir()
        for path in source_files():
            target = staging / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        report = Path(directory) / "gitleaks.json"
        result = subprocess.run([executable, "dir", str(staging), "--redact", "--report-format", "json", "--report-path", str(report), "--no-banner"], capture_output=True, timeout=90)
        if result.returncode not in (0, 1) or not report.exists():
            raise RuntimeError("Gitleaks no pudo completar el escaneo")
        leaks = json.loads(report.read_text(encoding="utf-8"))
        for leak in leaks:
            findings.append({"rule": leak["RuleID"], "file": leak["File"], "line": leak["StartLine"], "value": "REDACTED"})
    return {"findings": findings, "files_scanned": len(list(source_files())), "engine": "Gitleaks 8.30.1 + reglas del proyecto"}


def configuration_scan():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    dockerfile = (ROOT / "Dockerfile").read_text()
    storage = (ROOT / "infra/terraform/storage.tf").read_text()
    database = (ROOT / "infra/terraform/database.tf").read_text()
    security = (ROOT / "infra/terraform/security.tf").read_text()
    checks = {
        "docker_base_version_fixed": bool(re.search(r"^FROM \S+:\d+\.\d+\.\d+", dockerfile, re.M)),
        "docker_nonroot": bool(re.search(r"^USER 10001:10001$", dockerfile, re.M)),
        "docker_healthcheck": "HEALTHCHECK " in dockerfile and "/salud" in dockerfile,
        "docker_hash_locked_dependencies": "--require-hashes" in dockerfile,
        "two_own_services": all(compose["services"].get(s, {}).get("build") for s in ("api", "notifications")),
        "private_notifications": not compose["services"]["notifications"].get("ports"),
        "api_behind_tls_proxy": not compose["services"]["api"].get("ports"),
        "no_privileged_containers": all(not s.get("privileged", False) for s in compose["services"].values()),
        "runtime_readonly": all(s.get("read_only") for s in compose["services"].values()),
        "runtime_drop_caps": all("ALL" in s.get("cap_drop", []) for s in compose["services"].values()),
        "s3_four_public_blocks": all(re.search(rf"{key}\s*=\s*true", storage) for key in ("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets")),
        "s3_encryption": 'sse_algorithm = "AES256"' in storage,
        "s3_tls_policy": '"aws:SecureTransport" = "false"' in storage and 'Effect    = "Deny"' in storage,
        "rds_private": bool(re.search(r"publicly_accessible\s*=\s*false", database)),
        "rds_encrypted": bool(re.search(r"storage_encrypted\s*=\s*true", database)),
        "rds_only_app_sg": "referenced_security_group_id = aws_security_group.app.id" in security,
    }
    return {"checks": checks, "failed": [k for k, v in checks.items() if not v]}


if __name__ == "__main__":
    import sys
    result = secrets_scan() if sys.argv[1] == "secrets" else configuration_scan()
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result.get("findings") or result.get("failed")))
