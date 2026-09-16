"""Corre un candidato inseguro aislado y luego las fuentes corregidas reales."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-python", required=True)
    args = parser.parse_args()
    runtime = str(Path(args.runtime_python).resolve())
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    env.setdefault("GITLEAKS_BIN", str(ROOT / ".tools/gitleaks/gitleaks.exe") if os.name == "nt" else "gitleaks")
    unsafe = '"""Candidato de demostración: no desplegar."""\nimport subprocess\n\ndef legacy_search(query):\n    return subprocess.check_output("find /srv/catalog -name " + query, shell=True)\n'
    with tempfile.TemporaryDirectory(prefix="mercado-nube-red-") as directory:
        target = Path(directory)
        for folder in ("app", "infra", "pipeline", "scripts", "tests", "deploy", "docs", ".github"):
            if (ROOT / folder).exists():
                shutil.copytree(ROOT / folder, target / folder, ignore=shutil.ignore_patterns(".terraform", "*.tfstate*", "*.tfplan", "__pycache__", "tls", "*.docx", "capturas"))
        for name in ("Dockerfile", "docker-compose.yml", "requirements.txt", ".env.example"):
            shutil.copy2(ROOT / name, target / name)
        (target / "app/unsafe_probe.py").write_text(unsafe, encoding="utf-8")
        result = subprocess.run([sys.executable, str(target / "pipeline/run.py"), "--label", "roja", "--runtime-python", runtime], env=env)
        shutil.copytree(target / "reportes/roja", ROOT / "reportes/roja", dirs_exist_ok=True)
        shutil.copy2(target / "reportes/corrida_roja.txt", ROOT / "reportes/corrida_roja.txt")
        (ROOT / "reportes/roja/candidato_inseguro.txt").write_text(unsafe, encoding="utf-8")
        verdict = json.loads((ROOT / "reportes/roja/veredicto.json").read_text())
        if result.returncode != 1 or verdict["verdict"] != "BLOQUEAR" or verdict["stages"]["bandit"]["ok"]:
            raise RuntimeError("La corrida roja no bloqueó el fallo deliberado")
    return subprocess.run([sys.executable, str(ROOT / "pipeline/run.py"), "--label", "verde", "--runtime-python", runtime], env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
