"""Una única decisión final. Cualquier error de herramienta también bloquea."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.policy import source_files
from pipeline.source_digest import deployment_digest


def decide(stages):
    required = {"secrets", "bandit", "checkov", "configuration", "dependencies", "tests", "sbom", "live"}
    return "PERMITIR" if set(stages) == required and all(x["ok"] is True for x in stages.values()) else "BLOQUEAR"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=["roja", "verde"])
    parser.add_argument("--runtime-python", default=sys.executable)
    args = parser.parse_args()
    output = ROOT / "reportes" / args.label
    output.mkdir(parents=True, exist_ok=True)
    log_path = ROOT / "reportes" / f"corrida_{args.label}.txt"
    stages = {}
    source_hash = hashlib.sha256()
    for path in sorted(set(source_files())):
        source_hash.update(path.relative_to(ROOT).as_posix().encode())
        source_hash.update(path.read_bytes())
    log = log_path.open("w", encoding="utf-8")

    def write(value):
        print(value, flush=True)
        log.write(value + "\n")
        log.flush()

    write("MERCADO NUBE | PIPELINE INTEGRADO")
    write("Fecha UTC: " + datetime.now(timezone.utc).isoformat())
    write("SHA256 fuentes: " + source_hash.hexdigest())
    for name in ["bandit", "checkov", "pip-audit", "pytest", "cyclonedx-bom"]:
        write(f"Herramienta {name}: {importlib.metadata.version(name)}")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", LOG_LEVEL="ERROR")
    tasks = [
        ("secrets", [sys.executable, "-m", "pipeline.policy", "secrets"], "Cero credenciales reconocidas en código/configuración"),
        ("bandit", [sys.executable, "-m", "bandit", "-r", "app", "-f", "json", "-o", str(output / "bandit.json")], "Cero MEDIUM/HIGH; LOW se registra"),
        ("checkov", [sys.executable, "-m", "checkov.main", "-d", "infra", "--framework", "terraform", "--check", "CKV_AWS_16,CKV_AWS_17,CKV_AWS_23,CKV_AWS_24,CKV_AWS_25,CKV_AWS_41,CKV_AWS_79", "--skip-download", "--compact", "--output", "json"], "Cero fallos en los siete controles seleccionados; cero errores de parseo"),
        ("configuration", [sys.executable, "-m", "pipeline.policy", "config"], "Todos los controles Docker/S3/RDS obligatorios"),
        ("dependencies", [sys.executable, "-m", "pip_audit", "-r", "requirements.txt", "--no-deps", "--disable-pip", "-f", "json", "-o", str(output / "pip-audit.json")], "Cero vulnerabilidades publicadas en dependencias de producción"),
        ("tests", [sys.executable, "-m", "pytest", "-q", "tests", "--junitxml", str(output / "tests.xml")], "Cero pruebas fallidas; todas las pruebas deben ejecutarse"),
        ("sbom", [sys.executable, "-m", "cyclonedx_py", "environment", args.runtime_python, "--output-format", "JSON", "--outfile", str(output / "sbom_cyclonedx.json")], "CycloneDX válido con componentes de ejecución"),
        ("live", [sys.executable, "scripts/smoke.py"], "HTTP 200; API, RDS y S3 sanos; certificado TLS verificado"),
    ]
    for name, command, threshold in tasks:
        write(f"\nETAPA {name} | Umbral: {threshold}")
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            raw = result.stdout + result.stderr
            (output / f"{name}.log").write_text(raw, encoding="utf-8")
            write(raw.strip())
            ok = result.returncode == 0
            if name == "bandit":
                report = json.loads((output / "bandit.json").read_text())
                ok = result.returncode in (0, 1) and not report.get("errors") and report["metrics"]["_totals"]["loc"] > 0 and not any(r["issue_severity"] in {"MEDIUM", "HIGH"} for r in report["results"])
                write(json.dumps(report["results"], ensure_ascii=False, indent=2))
            if name == "checkov":
                report = json.loads(result.stdout)
                (output / "checkov.json").write_text(result.stdout, encoding="utf-8")
                summary = report["summary"]
                ok = ok and summary["failed"] == 0 and summary["passed"] >= 15 and summary["parsing_errors"] == 0
            if name == "dependencies":
                report = json.loads((output / "pip-audit.json").read_text())
                ok = ok and len(report["dependencies"]) >= 20 and all("skip_reason" not in d and not d["vulns"] for d in report["dependencies"])
                write(json.dumps(report, ensure_ascii=False))
            if name == "sbom":
                sbom = json.loads((output / "sbom_cyclonedx.json").read_text())
                ok = ok and sbom["bomFormat"] == "CycloneDX" and len(sbom["components"]) >= 20
                write(f"SBOM: {sbom['bomFormat']} {sbom['specVersion']}, componentes: {len(sbom['components'])}")
                if ok and args.label == "verde":
                    (ROOT / "reportes/sbom_cyclonedx.json").write_text(json.dumps(sbom, indent=2), encoding="utf-8")
            stages[name] = {"ok": bool(ok), "exit_code": result.returncode, "threshold": threshold}
        except Exception as error:
            stages[name] = {"ok": False, "error": type(error).__name__, "threshold": threshold}
            write(f"Error de etapa: {type(error).__name__}: {error}")
        write("RESULTADO ETAPA: " + ("PASS" if stages[name]["ok"] else "FAIL"))
    verdict = decide(stages)
    summary = {"verdict": verdict, "source_sha256": source_hash.hexdigest(), "deployment_sha256": deployment_digest(ROOT), "stages": stages,
               "utc": datetime.now(timezone.utc).isoformat()}
    (output / "veredicto.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write("\nVEREDICTO FINAL: " + verdict)
    write("Código de salida: " + ("0" if verdict == "PERMITIR" else "1"))
    log.close()
    return 0 if verdict == "PERMITIR" else 1


if __name__ == "__main__":
    raise SystemExit(main())
