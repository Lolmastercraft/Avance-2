# Tabla de decisiones del pipeline

El pipeline evalúa un Marketplace que almacena usuarios y pedidos y permite publicar imágenes. Cada etapa protege una parte de ese flujo. Todas se ejecutan aunque una falle, y el único veredicto final es `PERMITIR` o `BLOQUEAR`. Cualquier error de herramienta, reporte ausente o formato inválido bloquea. El despliegue exige el veredicto verde y un hash coincidente de las fuentes que se van a transferir.

| Etapa | Riesgo del Marketplace | Umbral de bloqueo | Justificación |
|---|---|---|---|
| Secretos Gitleaks y patrones adicionales | Una clave AWS o contraseña permitiría leer imágenes, usuarios y pedidos | Cero secretos reconocidos en código/configuración/documentación escaneada | No existe una credencial aceptable en texto dentro del repositorio, ni de prueba. Se registra ubicación, nunca el valor |
| SAST Bandit | Una búsqueda de catálogo que lance comandos o manipule SQL abre ejecución remota o fuga de datos | Cero hallazgos MEDIUM o HIGH; errores de análisis bloquean; LOW se registra | Los hallazgos de mayor impacto son incompatibles con un proceso que tiene acceso a S3 y RDS. LOW requiere lectura contextual y queda visible |
| IaC Checkov | RDS pública/sin cifrado, metadatos inseguros y acceso administrativo desde Internet | Cero fallos de los siete controles seleccionados; cero errores de parseo; al menos 15 comprobaciones efectivas | Se revisan riesgos de exposición y credenciales concretos del laboratorio; no se equipara pasar este perfil con pasar todo Checkov |
| Configuración específica | S3 público/sin cifrar, contenedor root, puerto de notificaciones expuesto, imagen sin versión | Deben pasar los 16 controles del proyecto | Complementa Checkov para los recursos S3 separados y las condiciones mínimas de Docker exigidas por la actividad |
| SCA pip-audit | Dependencias de HTTP, imágenes o DB vulnerables procesan entradas de compradores y vendedores | Cero vulnerabilidades publicadas en las dependencias de producción; cero dependencias omitidas | La API recibe archivos no confiables; se mantiene un conjunto pequeño y actualizable. Sin CVSS uniforme en la fuente de pip-audit no se inventa una clasificación HIGH/CRITICAL |
| Pruebas pytest | Precio manipulado, pedido de otro usuario, stock negativo, CSRF, aviso duplicado o gate permisivo | Cero pruebas fallidas y suite ejecutada | Estos errores lógicos pueden no aparecer en SAST, pero alteran compras, inventario y privacidad |
| SBOM CycloneDX | No poder identificar qué librería desplegada necesita corregirse | JSON CycloneDX validado por el generador y al menos 20 componentes del runtime | Conserva trazabilidad de dependencias directas/transitivas; se excluyen deliberadamente las herramientas de desarrollo |
| Integración live | API aparentemente sana con RDS o S3 inaccesibles | `/salud` HTTP 200, API/RDS/S3 en `ok` y certificado TLS validado | El Marketplace depende de ambos servicios reales. Si Academy está apagado o expira la CA, el control falla en lugar de simular disponibilidad |

## Perfil de Checkov

- `CKV_AWS_16`: cifrado de RDS.
- `CKV_AWS_17`: RDS sin acceso público.
- `CKV_AWS_23`: descripciones de reglas de seguridad.
- `CKV_AWS_24` y `CKV_AWS_25`: restricciones de SSH y RDP públicos.
- `CKV_AWS_41`: credenciales no embebidas en el proveedor AWS.
- `CKV_AWS_79`: IMDSv2 requerido.

El número de resultados puede superar siete porque un control se aplica a varios recursos. El perfil actual produce 21 comprobaciones aprobadas y ninguna omitida. El resto de reglas de Checkov está fuera del perfil; no se oculta como si hubiese pasado. Los controles específicos S3 son estáticos y conservadores, no un evaluador general de HCL arbitrario.

## Corrida roja y corrección

`pipeline/demostrar.py` crea una copia temporal del candidato y añade `app/unsafe_probe.py`, una búsqueda insegura que concatena texto externo en `subprocess.check_output(..., shell=True)`. No ejecuta esa función ni la despliega. Bandit encuentra `B602 HIGH` y el gate termina BLOQUEAR con salida 1. El archivo exacto queda en `reportes/roja/candidato_inseguro.txt`.

La corrección es eliminar esa alternativa de búsqueda: el código entregado busca con `Product.name.ilike()` y parámetros de SQLAlchemy. El mismo pipeline se ejecuta sobre las fuentes corregidas y termina PERMITIR con salida 0. No cambia el umbral entre corridas ni se aplica un `nosec` para obtener verde. Los reportes conservan timestamps, versiones, salidas completas y hashes de fuentes.

## Controles que no se cubren

No se incluye un escáner de vulnerabilidades de paquetes del sistema operativo de las imágenes, un pentest DAST completo, análisis de licencias ni firma/procedencia de imágenes. Se entregan bases con versión fija, hashes de dependencias, SAST y pruebas funcionales, pero eso no cubre todos los CVE de Docker/Nginx/Linux. Gitleaks se ejecuta sobre una copia del árbol fuente; la revisión final de Git añade un escaneo del commit para evitar secretos en los archivos entregados, pero no se afirma una auditoría de otros repositorios del usuario.

No se habilitan Multi-AZ, replicación entre regiones, claves KMS propias, ALB/WAF ni NAT Gateway para reducir consumo y evitar permisos fuera del Lab. Su ausencia es una decisión documentada y no un defecto silenciado en los umbrales. El rate limiting en memoria protege el proceso único actual; producción requiere almacenamiento compartido.

## Alcance del bloqueo

El gate devuelve un código distinto de cero y `scripts/deploy.py` rechaza el despliegue si falta el reporte verde o el hash no coincide. Un administrador puede modificar scripts o reportes; para un entorno productivo se requerirían artefactos firmados, protección de ramas y credenciales de despliegue solo accesibles desde CI. No se publican credenciales de AWS en GitHub Actions.
