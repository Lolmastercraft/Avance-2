"""Digest del contenido que se despliega; no incluye secretos ni reportes."""
import hashlib
from pathlib import Path


def deployment_digest(root):
    root = Path(root)
    paths = [p for p in (root / "app").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    paths += [root / p for p in ("Dockerfile", "docker-compose.yml", "requirements.txt", "deploy/nginx.conf", "deploy/rds-ca-bundle.crt", "scripts/remote_setup.sh")]
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()
