"""Inicializa esquema/usuario runtime sin imprimir secretos; se ejecuta una vez."""
import json
import os
from pathlib import Path

import boto3
import psycopg
from psycopg import sql
from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.models import Base, Product, database


def bootstrap():
    config = json.loads(Path("/run/bootstrap.json").read_text())
    admin = make_url(config["admin_url"])
    runtime = make_url(config["DATABASE_URL"])
    connection = psycopg.connect(host=admin.host, dbname=admin.database, user=admin.username,
                                password=admin.password, sslmode="verify-full",
                                sslrootcert="/srv/certs/rds-ca-bundle.crt", autocommit=True)
    with connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (runtime.username,))
        if not cursor.fetchone():
            cursor.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(runtime.username), sql.Literal(runtime.password)))
        cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(admin.database), sql.Identifier(runtime.username)))
        cursor.execute("CREATE SCHEMA IF NOT EXISTS market")
        cursor.execute(sql.SQL("GRANT USAGE, CREATE ON SCHEMA market TO {}").format(sql.Identifier(runtime.username)))
        cursor.execute(sql.SQL("ALTER ROLE {} SET search_path TO market").format(sql.Identifier(runtime.username)))
    os.environ.update({key: value for key, value in config.items() if key != "admin_url"})
    engine, sessions = database()
    Base.metadata.create_all(engine)
    client = boto3.client("s3", region_name=config["AWS_REGION"])
    products = [
        ("Audífonos Pulse", "Tu música, sin distracciones. Diseño cómodo y sonido envolvente.", "Tecnología", 129900, "headphones"),
        ("Teclado Studio", "Compacto, mecánico y listo para tus mejores ideas.", "Tecnología", 89900, "keyboard"),
        ("Lámpara Forma", "Luz cálida para leer, crear y darle calma a tu escritorio.", "Escritorio", 64900, "lamp"),
        ("Taza Terracota", "Una pausa bien merecida. Cerámica con acabado artesanal.", "Escritorio", 24900, "mug"),
        ("Bolso Diario", "Ligero, versátil y con espacio para todos tus planes.", "Accesorios", 45900, "bag"),
        ("Cámara Mini", "Lleva tus recuerdos contigo. Un clásico en versión compacta.", "Tecnología", 219900, "camera"),
    ]
    with sessions.begin() as db:
        for name, description, category, price, artwork in products:
            if db.scalar(select(Product).where(Product.name == name)):
                continue
            key = f"products/seed/{artwork}.svg"
            client.put_object(Bucket=config["PRODUCT_BUCKET"], Key=key,
                              Body=Path(f"/srv/app/assets/{artwork}.svg").read_bytes(),
                              ContentType="image/svg+xml", ServerSideEncryption="AES256")
            db.add(Product(name=name, description=description, category=category,
                           price_cents=price, stock=30, image_key=key))
    print("Schema, runtime role and six S3-backed products ready.")


if __name__ == "__main__":
    bootstrap()
