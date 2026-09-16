#!/usr/bin/env sh
# Verificador propio; la plantilla y el verificador oficiales no se recibieron.
set -eu
python scripts/verify_delivery.py "$@"
