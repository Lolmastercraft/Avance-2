"""S3 privado: el servidor transmite imágenes; nunca publica el bucket."""
import io
import os
import uuid

import boto3
from PIL import Image, UnidentifiedImageError


class Storage:
    def __init__(self):
        self.bucket = os.environ["PRODUCT_BUCKET"]
        self.client = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))

    def put_image(self, data):
        if len(data) > 2 * 1024 * 1024:
            raise ValueError("La imagen no puede superar 2 MB.")
        try:
            with Image.open(io.BytesIO(data)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Usa una imagen JPG, PNG o WebP.")
                if source.width * source.height > 16_000_000:
                    raise ValueError("La imagen tiene demasiados píxeles.")
                source.load()
                source.thumbnail((1200, 1200))
                image = source.convert("RGB")
                target = io.BytesIO()
                image.save(target, format="JPEG", quality=86)
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
            raise ValueError("El archivo no es una imagen válida.") from error
        key = f"products/{uuid.uuid4().hex}.jpg"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=target.getvalue(),
                               ContentType="image/jpeg", ServerSideEncryption="AES256")
        return key

    def read_image(self, key):
        result = self.client.get_object(Bucket=self.bucket, Key=key)
        return result["Body"].read(), result["ContentType"]

    def healthy(self):
        self.client.head_bucket(Bucket=self.bucket)
