# Matriz de requisitos y evidencia

| Requisito | Implementación | Evidencia |
|---|---|---|
| Marketplace Python | Flask: catálogo, carrito, publicación y pedidos | app/web.py y capturas 01 a 05 |
| Dos contenedores propios | API y notificaciones con programas separados | docker-compose.yml y reportes/aws/containers_rds.txt |
| Pieza distintiva | Notificador outbox simulado e idempotente | app/notifications.py y pedido confirmado |
| S3 real privado cifrado | Lectura de catálogo y subida de nuevos productos | reportes/aws/infraestructura.json y captura 05 |
| RDS real privada cifrada | Persistencia de usuarios, catálogo, pedidos y avisos | exportación AWS y conteos SQL con TLS 1.3 |
| Registro e inicio de sesión | scrypt, sesiones y CSRF | tests/test_marketplace.py y E2E |
| /salud | Dependencias RDS/S3 y healthchecks | scripts/smoke.py y etapa live |
| Sin credenciales en código | Variables, SSM y rol de EC2 | Gitleaks y .gitignore |
| IaC | infra/main.tf y módulo infra/terraform | Checkov y políticas específicas |
| Docker endurecido | Versión fija, UID 10001 y HEALTHCHECK | Dockerfile y salida id de contenedores |
| Gate integrado rojo/verde | Ocho etapas y veredicto final | reportes/corrida_roja.txt y corrida_verde.txt |
| Umbrales y justificación | Riesgos particulares del Marketplace | tabla_decisiones_pipeline.md |
| SBOM CycloneDX | Entorno de producción con dependencias bloqueadas | reportes/sbom_cyclonedx.json |
| Documentación | README, diagrama, ADR y declaración honesta de IA | docs/ |
| Repositorio Git | Lolmastercraft/Avance-2, privado | URL del repositorio |
| Documento de evidencias | Documento preparado con los apartados exigidos | entrega/Evidencias_Avance2_Mercado_Nube.docx |
| Plantilla institucional exacta | No incluida en los ZIP recibidos | Pendiente cotejar cuando se proporcione |
| Video | Lo graba el alumno | Guion preparado; enlace pendiente |

Las capturas de la aplicación son del navegador conectado a AWS. Las capturas de infraestructura y contenedores representan resultados exportados por API/SSM, identificados como tales; no se presentan como capturas de la consola AWS. En el video deben mostrarse los recursos en la consola, en el orden que pide la actividad.
