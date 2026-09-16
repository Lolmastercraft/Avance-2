FROM python:3.12.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /srv
RUN groupadd --gid 10001 market && useradd --uid 10001 --gid market --no-create-home market
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
COPY --chown=market:market app ./app
COPY --chown=market:market deploy/rds-ca-bundle.crt /srv/certs/rds-ca-bundle.crt
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=8)"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--worker-tmp-dir", "/tmp", "--access-logfile", "-", "app.web:create_app()"]
