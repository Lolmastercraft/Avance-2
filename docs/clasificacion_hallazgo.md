# Clasificación del hallazgo del marketplace

## Alcance y origen

Parche docente `tema3_marketplace/reenviar_confirmacion.py`: `POST /pedidos/<pedido_id>/reenviar-confirmacion`. Se integró en el candidato aislado de la misma instancia QA del Avance 2, `i-06f5d7a26aa4f1498`. El código vulnerable no se publicó en el servicio accesible por Internet ni en Producción.

El commit `41e10c0` conserva el endpoint original y los adaptadores a los modelos. El commit `9bdb8d6` añade la detección. La remediación real está en `b0b127b`.

## Tipo y causa

Control de acceso ausente, **CWE-862**, con acceso horizontal por identificador controlado por el cliente, **CWE-639 / IDOR**. El endpoint consultaba un pedido por ID y enviaba su confirmación sin comprobar la sesión ni la relación entre el usuario y el pedido.

Los identificadores son enteros. Un usuario distinto puede sustituir el ID y provocar un reenvío al comprador original. Un visitante sin sesión también consigue activar la operación si obtiene un token CSRF válido de su propia sesión. CSRF no demuestra identidad ni propiedad del recurso.

Referencias de clasificación: [MITRE CWE-862](https://cwe.mitre.org/data/definitions/862.html) y [MITRE CWE-639](https://cwe.mitre.org/data/definitions/639.html).

## Severidad justificada

**Media en el contexto comprobado de este laboratorio.** La explotación es sencilla, no requiere privilegios y permite realizar una acción sobre pedidos ajenos, distinguir pedidos existentes y generar mensajes no solicitados. Sin embargo, el destinatario sale de RDS y no lo controla el atacante; la respuesta no devuelve los detalles del pedido. No se comprobó extracción de datos, toma de cuentas, ejecución de comandos ni alteración de precios o pagos. El buzón de prueba no entrega correo al exterior.

La severidad debe reevaluarse si la aplicación utiliza correo externo, tiene alto volumen, permite cambiar el destinatario o devuelve información adicional. No se inventa una puntuación CVSS ni se hereda la severidad crítica del ejemplo de otro tema.

## Evidencia y falso negativo inicial

El pipeline original aprobó el candidato vulnerable: `reportes/final/baseline/pipeline_original.txt`. Bandit y las 15 pruebas originales no cubrían los permisos del nuevo endpoint. Se documenta este **falso negativo**, no se presenta como una detección automática de Bandit.

Se ampliaron las pruebas de la etapa pytest. En la corrida roja de QA, el usuario ajeno y el visitante recibieron HTTP 200 y el doble de prueba de correo registró una llamada por caso. La respuesta esperada era 404 y 401, respectivamente, sin enviar. Resultado real: **2 fallidas, 18 aprobadas; BLOQUEAR, salida 1**. El doble de prueba evita mensajes externos durante la reproducción.

La corrida verde posterior conserva las pruebas de detección y añade cobertura de contención, error SMTP y límite de frecuencia: **23 aprobadas; PERMITIR, salida 0**. El flujo desplegado se comprueba por separado con SMTP real hacia Mailpit.

## Falsos positivos

Los dos fallos de autorización no son falsos positivos: se reproduce la llamada de envío antes de validar permisos. No se omitió ninguna regla ni se introdujo `nosec`, un `xfail` o una prueba que espere el comportamiento vulnerable para obtener verde. La protección CSRF existente no elimina el hallazgo, porque las solicitudes de reproducción utilizan tokens válidos.

## Corrección

Se requiere una sesión autenticada. La consulta aplica conjuntamente `Order.id == pedido_id` y `Order.user_id == g.user.id`, usando la identidad de la sesión del servidor. Un pedido ajeno y uno inexistente devuelven el mismo 404. La comprobación precede al envío SMTP. Se conserva la función de reenvío al correo guardado del comprador, sin aceptar un destinatario del formulario.

Controles adicionales: CSRF, límite de tres reenvíos por minuto, bandera de contención y HTTP 503 ante fallo SMTP sin revelar detalles internos.
