"""Verificador propio de estructura; no sustituye el script del docente."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sin-video", action="store_true")
    args = parser.parse_args()
    required = ["app/web.py", "app/notifications.py", "Dockerfile", "docker-compose.yml", "infra/main.tf",
                "pipeline/run.py", "reportes/corrida_roja.txt", "reportes/corrida_verde.txt",
                "reportes/sbom_cyclonedx.json", "docs/README.md", "docs/diagrama_arquitectura.png",
                "docs/ADR-001-decisiones-tecnicas.md", "docs/tabla_decisiones_pipeline.md",
                "docs/declaracion_uso_ia.md", "docs/enlace_video.txt",
                "entrega/Evidencias_Avance2_Mercado_Nube.docx"]
    errors = [f"Falta {name}" for name in required if not (ROOT / name).is_file()]
    for label, expected in [("roja", "BLOQUEAR"), ("verde", "PERMITIR")]:
        try:
            value = json.loads((ROOT / f"reportes/{label}/veredicto.json").read_text(encoding="utf-8"))
            if value["verdict"] != expected:
                errors.append(f"Veredicto incorrecto: {label}")
        except (OSError, ValueError, KeyError):
            errors.append(f"Evidencia no verificable: {label}")
    if not args.sin_video and "PENDIENTE" in (ROOT / "docs/enlace_video.txt").read_text(encoding="utf-8"):
        errors.append("El estudiante debe grabar y enlazar el video")
    print("\n".join(errors) if errors else "Archivos y veredictos presentes. Revisar acceso del evaluador y plantilla oficial antes de entregar.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
