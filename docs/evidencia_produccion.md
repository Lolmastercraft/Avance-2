# Evidencia de promoción a Producción

## Recursos y versión

| Ambiente | Instancia EC2 | Dirección durante la evidencia | Base lógica / usuario |
|---|---|---|---|
| QA, misma del Avance 2 | `i-06f5d7a26aa4f1498` | `https://3.93.143.140` | `marketplace` / `marketplace_runtime` |
| Producción académica nueva | `i-02be4a02d659f23c3` | `https://52.87.249.158` | `marketplace_production` / `marketplace_prod` |

Infraestructura de la instancia nueva en `infra/final/main.tf`, con estado independiente del Avance 2. El plan creó una instancia y no cambió ni destruyó recursos anteriores. No se intervino la instancia ajena llamada Linux.

Commit de remediación: [`b0b127b`](https://github.com/Lolmastercraft/Avance-2/commit/b0b127b). SHA-256 del contenido desplegado y aprobado en QA:

`cc80c78c97b8446838e315735adde02d891b182abffe8b02c75ab32d20ce84c6`

La corrida verde terminó el 29 de septiembre de 2026 a las 06:12:53 UTC. Los manifiestos de promoción y los `release-final.json` obtenidos por SSM permiten comparar el mismo hash en ambos ambientes. La normalización del orden de rutas en `pipeline/source_digest.py` permite que la verificación produzca el mismo resultado en Windows y Linux.

## Pruebas sobre las instancias desplegadas

En ambos ambientes se registraron cuentas de demostración, se creó un pedido real en RDS y se pidió su reenvío. Las peticiones verificaron el certificado autofirmado mediante su CA explícita. Resultados guardados en `reportes/final/e2e_qa.json` y `e2e_production.json`:

| Caso | HTTP esperado y obtenido |
|---|---|
| Comprador propietario con CSRF válido | 200, confirmación reenviada |
| Otro comprador con CSRF válido | 404, sin autorización sobre el pedido |
| Visitante sin sesión y con CSRF válido | 401 |
| Propietario sin token CSRF | 400 |

También se abrió la página real de Producción y se pulsó el botón de reenvío mediante un navegador de pruebas separado, sin controlar las pestañas del alumno. `browser_e2e.json` conserva la URL y la respuesta. Para esa captura el navegador de pruebas admitió el certificado autofirmado; la verificación TLS independiente está en las pruebas HTTP anteriores.

Los reportes `estado_qa.txt` y `estado_production.txt` incluyen las cuatro instancias de contenedor (API, notificaciones, proxy y Mailpit), usuario no root de la API, base lógica, usuario PostgreSQL y `ssl: True`. También registran el total y los asuntos capturados por el buzón SMTP privado. No se usó un proveedor externo de correo.

## Evidencias visuales y procedencia

- `docs/capturas/final/01_pipeline_bloqueado.png` y `04_pipeline_verde.png`: captura del visor compacto de los registros reales; aparecen las ocho etapas y el veredicto. Los archivos completos están en `reportes/pipeline_bloqueado.txt` y `reportes/pipeline_verde.txt`.
- `02_hallazgo.png`: salida de pytest de la corrida roja de QA.
- `03_diff_remediacion.png`: salida real de Git del cambio de autorización.
- `05_qa_identidad.png`: vista de los datos originales de DescribeInstances y SSM, identificada como exportación, no como consola AWS.
- `06_ec2_produccion_consola.png`: captura original de la consola EC2 proporcionada por el alumno; muestra la instancia nueva y su IP mientras se inicializaba.
- `07_app_produccion.png` y `08_reenvio_produccion.png`: capturas de la aplicación real y su respuesta de reenvío.

## Límites del laboratorio

La dirección pública puede cambiar cuando la instancia se detenga y vuelva a arrancar. El certificado es autofirmado y no corresponde a un dominio público. El buzón guarda los mensajes en almacenamiento temporal del contenedor; su reinicio puede eliminarlos. Se conservaron evidencias fuera de las instancias.

QA y Producción comparten servicios de infraestructura para ahorrar crédito, pero no la base lógica ni la clave de sesión de la aplicación. Esto no se presenta como una arquitectura de alta disponibilidad ni como aislamiento completo de producción. La vida final de la nueva instancia se registra en `reportes/final/cierre_produccion.json` cuando se confirme el cierre.
