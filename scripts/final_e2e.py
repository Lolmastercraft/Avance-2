"""Comprueba compra, reenvio SMTP y denegaciones con cuentas de prueba propias."""
import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reportes/final"


def csrf(client, url):
    response = client.get(url, timeout=20)
    response.raise_for_status()
    client.headers["Referer"] = url
    return re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)


def run(env, url):
    clients = [requests.Session() for _ in range(3)]
    for client in clients:
        client.verify = str(OUT / f"{env}-server.crt")
    owner, stranger, anonymous = clients
    suffix = secrets.token_hex(5)
    for index, client in enumerate((owner, stranger)):
        r = client.post(url + "/registro", data={"csrf_token": csrf(client, url + "/registro"), "name": "Prueba Entrega Final", "email": f"final-{env}-{index}-{suffix}@example.test", "password": secrets.token_urlsafe(24)}, timeout=20, allow_redirects=False)
        assert r.status_code == 302, f"Registro {env}: HTTP {r.status_code}; {re.findall(r'<title>(.*?)</title>', r.text)}"
    r = owner.post(url + "/carrito/agregar/1", data={"csrf_token": csrf(owner, url + "/")}, timeout=20)
    r.raise_for_status()
    cart = owner.get(url + "/carrito", timeout=20).text
    r = owner.post(url + "/pedidos", data={name: re.search(f'name="{name}" value="([^"]+)"', cart).group(1) for name in ("csrf_token", "checkout_key")}, timeout=20, allow_redirects=False)
    assert r.status_code == 302
    order_path = r.headers["Location"]
    endpoint = url + order_path + "/reenviar-confirmacion"
    accepted = owner.post(endpoint, data={"csrf_token": csrf(owner, url + order_path)}, timeout=20)
    denied = stranger.post(endpoint, data={"csrf_token": csrf(stranger, url + "/")}, timeout=20)
    no_login = anonymous.post(endpoint, data={"csrf_token": csrf(anonymous, url + "/registro")}, timeout=20)
    no_csrf = owner.post(endpoint, timeout=20)
    assert (accepted.status_code, denied.status_code, no_login.status_code, no_csrf.status_code) == (200, 404, 401, 400)
    proof = {"utc": datetime.now(timezone.utc).isoformat(), "environment": env, "url": url,
             "tls_verified": True, "order_path": order_path, "owner_resend": accepted.status_code,
             "other_user": denied.status_code, "anonymous": no_login.status_code, "missing_csrf": no_csrf.status_code,
             "owner_response": accepted.json(), "email_delivery": "SMTP privado Mailpit; no correo externo"}
    (OUT / f"e2e_{env}.json").write_text(json.dumps(proof, indent=2, ensure_ascii=False), encoding="utf-8")
    # Solo sesion de prueba, fuera de Git; usada para capturar la pagina real.
    private = ROOT / ".work/final-document"
    (private / f"{env}-session.json").write_text(json.dumps({"url": url, "path": order_path, "cookies": requests.utils.dict_from_cookiejar(owner.cookies)}), encoding="utf-8")
    print(json.dumps(proof))


if __name__ == "__main__":
    run("qa", "https://3.93.143.140")
    run("production", "https://52.87.249.158")
