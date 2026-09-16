# Mercado Nube

## Qué hace

Un usuario se registra o inicia sesión, explora productos con imágenes almacenadas en S3, agrega unidades al carrito y confirma un pedido. El servidor calcula el precio y descuenta existencias dentro de una transacción. Un segundo contenedor consume las notificaciones pendientes y registra en RDS un aviso de confirmación. La sección Vender permite publicar un producto propio con imagen JPG, PNG o WebP.

No hay pasarela de pagos: el pedido es una compra simulada. Tampoco se envía correo real. El mensaje mostrado en el pedido constituye la pieza técnica distintiva del tema Marketplace.

## Abrir la aplicación

1. Inicia AWS Academy Learner Lab y verifica que EC2 y RDS estén encendidas.
2. Abre https://100.24.2.141. El certificado es autofirmado para el laboratorio; su copia pública está en `deploy/lab-server.crt`.
3. Crea una cuenta propia con una contraseña de al menos 12 caracteres.
4. Agrega un producto, entra al carrito y confirma. Actualiza el pedido si el notificador aún aparece pendiente.
5. Publica otro producto desde Vender para demostrar la escritura real en S3.

La prueba automática creó una cuenta de demostración con contraseña aleatoria que no se publica. Crea una cuenta nueva para grabar el video.

## Servicios y datos

| Servicio | Tecnología | Función |
|---|---|---|
| api | Python 3.12, Flask, Gunicorn | HTML, sesiones, catálogo, imágenes, carrito y pedidos |
| notifications | Python 3.12, Flask, Gunicorn | Worker de outbox; confirma cada pedido una vez |
| proxy | Nginx sin root | HTTPS 443, redirección desde HTTP 80 |
| RDS | PostgreSQL 16.14 | Usuarios, productos, carrito, pedidos, partidas y avisos |
| S3 products | Bucket privado | Imágenes del catálogo y publicaciones |
| S3 evidence | Bucket privado | Paquetes de despliegue y reserva de evidencias |
| SSM | Systems Manager | Administración sin SSH y secreto inicial SecureString |

Los servicios propios `api` y `notifications` se construyen con el mismo Dockerfile endurecido y ejecutan programas distintos. El notificador no publica puertos al host. Nginx es un tercer contenedor auxiliar. `/salud` de la API consulta RDS y S3; el del worker comprueba RDS y su latido.

## Seguridad aplicada

Contraseñas con scrypt, consultas parametrizadas mediante SQLAlchemy, formularios protegidos contra CSRF, sesiones HttpOnly/SameSite/Secure, límites de intentos de autenticación y encabezados CSP. Los pedidos se filtran por propietario; precio y existencias se calculan del lado servidor. El stock se bloquea en PostgreSQL y el pedido y su aviso pendiente se confirman en una sola transacción.

Las imágenes subidas se validan por contenido, tamaño y dimensiones y se recodifican como JPEG sin metadatos. El bucket no se publica: la API transmite el objeto autorizado del catálogo. Los seis SVG iniciales son ilustraciones estáticas del proyecto; no se aceptan SVG subidos por usuarios.

RDS exige TLS y el cliente valida la CA de Amazon y el hostname con `verify-full`. La aplicación usa `marketplace_runtime`, con permisos en el esquema `market`; no usa la cuenta administradora en ejecución. Los contenedores usan UID 10001, sistema de archivos de solo lectura, límites de memoria y capacidades eliminadas. Los secretos de AWS provienen del perfil de instancia de Academy, sin claves estáticas en el código.

## Preparación y pruebas locales

Requisitos: Git, Python 3.12, uv, Docker Compose y Gitleaks 8.30.1. AWS CLI y Terraform son necesarios para infraestructura/despliegue.

```powershell
uv venv .runtime --python 3.12
uv pip sync --python .runtime\Scripts\python.exe requirements.txt
uv venv .venv --python 3.12
uv pip sync --python .venv\Scripts\python.exe requirements-dev.txt
uv pip install --python .venv\Scripts\python.exe Flask==3.1.3 Flask-WTF==1.3.0 Flask-Limiter==4.1.1 SQLAlchemy==2.0.54 psycopg[binary]==3.3.5 Pillow==12.3.0
$env:GITLEAKS_BIN = 'C:\ruta\gitleaks.exe'
.venv\Scripts\python.exe -m pytest -q tests
.venv\Scripts\python.exe pipeline\demostrar.py --runtime-python .runtime\Scripts\python.exe
```

En Linux, sustituye `Scripts/python.exe` por `bin/python`. Gitleaks debe estar en PATH. Las pruebas usan SQLite temporal y almacenamiento en memoria; la evidencia de integración independiente utiliza RDS/S3 reales. La etapa live necesita el laboratorio activo y el certificado público vigente. Un laboratorio apagado bloquea esa etapa; no se interpreta como pase.

El entorno de herramientas está separado del runtime porque Checkov limita su propia versión de boto3. `requirements.txt` fija las dependencias de producción y sus hashes; `requirements-dev.txt` fija las herramientas. El SBOM se genera exclusivamente del entorno `.runtime`.

## Infraestructura y despliegue

La configuración aplicada y su estado existente están en `infra/terraform`. `infra/main.tf` expone el módulo para la estructura de la entrega; no ejecutes un segundo apply desde `infra/`, pues intentaría administrar los mismos recursos con otro estado.

```powershell
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform plan
.venv\Scripts\python.exe pipeline\run.py --label verde --runtime-python .runtime\Scripts\python.exe
.runtime\Scripts\python.exe scripts\deploy.py
```

`scripts/deploy.py` exige un veredicto PERMITIR y compara el hash de las fuentes desplegables con el analizado. El archivo de veredicto y los scripts forman parte del límite de confianza del repositorio: no hay firma de artefactos ni control externo obligatorio de aprobación. El despliegue transfiere un paquete sin credenciales a S3, verifica SHA-256 en EC2 y ejecuta Compose por Systems Manager. Reutiliza el estado del laboratorio y la configuración inicial guardada en SSM.

Para recrear en otra cuenta, primero aplica Terraform en `infra/terraform`, ajusta los identificadores de laboratorio en los scripts y actualiza la URL/CA de la etapa live. El primer bootstrap requiere una sesión de aprovisionamiento: el gate live valida un entorno QA ya desplegado, no resuelve por sí solo el arranque inicial de una cuenta vacía.

En EC2, `/opt/marketplace/.env` contiene los valores de ejecución. `.bootstrap.json` y el parámetro SecureString son material administrativo; no se copian al repositorio. No muestres `docker inspect`, `.env`, `terraform output -json` ni el estado completo en el video: pueden revelar secretos. El estado de Terraform contiene la contraseña de RDS en texto plano y debe protegerse; la carpeta de trabajo está en OneDrive, por lo que su exclusión de Git no evita la sincronización de OneDrive.

## Operación y límites

La IP pública cambia al detener/iniciar EC2. Actualiza la URL del smoke test y regenera el certificado para la IP nueva antes de repetir el video. Las credenciales temporales del laboratorio se renuevan en el perfil local `avance2-lab`; no se guardan en archivos versionados.

El certificado autofirmado no ofrece confianza pública sin verificación manual. No se incluyeron dominio, certificado público, ALB, NAT Gateway, Multi-AZ, autoscaling, recuperación de contraseñas ni pagos. El limitador usa memoria y un proceso de API: ampliar el número de réplicas requeriría un backend compartido. El perfil LabRole tiene permisos definidos por Academy, más amplios que un rol productivo de mínimo privilegio.

La adaptación de S3 conserva la creación idempotente por AWS CLI porque Academy deniega la consulta Object Lock usada por el recurso general del proveedor. Terraform administra todos los controles S3 declarativos. `terraform destroy` no elimina los buckets base creados por `terraform_data`; su limpieza debe hacerse explícitamente tras respaldar la evidencia. RDS está configurada sin snapshot final ni protección de borrado por ser un laboratorio: revisa y respalda antes de destruir.

## Entrega y fuentes

Consulta el [ADR](ADR-001-decisiones-tecnicas.md), la [tabla de decisiones](tabla_decisiones_pipeline.md), la [declaración de IA](declaracion_uso_ia.md) y el [guion del video](guion_video.md).

Fuentes técnicas: [seguridad de Flask](https://flask.palletsprojects.com/web-security/), [healthchecks y orden de Compose](https://docs.docker.com/compose/how-tos/startup-order/), [TLS de RDS PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.SSL.html), [CycloneDX](https://cyclonedx.org/specification/overview/).
