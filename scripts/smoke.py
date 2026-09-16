"""Consulta /salud verificando el certificado TLS del laboratorio."""
import argparse
import json
import ssl
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="https://100.24.2.141")
parser.add_argument("--ca", default="deploy/lab-server.crt")
args = parser.parse_args()
context = ssl.create_default_context(cafile=args.ca)
with urllib.request.urlopen(args.url.rstrip("/") + "/salud", context=context, timeout=20) as response:
    result = json.load(response)
if result != {"status": "ok", "service": "marketplace-api", "database": "ok", "s3": "ok"}:
    raise SystemExit("Health dependency failure")
print(json.dumps({"tls_verified": True, "url": args.url + "/salud", "response": result}))
