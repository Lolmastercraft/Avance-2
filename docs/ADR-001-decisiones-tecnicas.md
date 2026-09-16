# ADR 001 Decisiones técnicas de Mercado Nube

Estado: implementado. Fecha: 16 de septiembre de 2026. Tema: Marketplace.

## Contexto

El Avance 2 requiere una aplicación Python con dos contenedores propios, S3 y RDS reales, registro/login y un pipeline con decisión integrada. El Learner Lab tiene recursos limitados y políticas institucionales que no pueden modificarse libremente.

## Decisiones

**Flask con HTML de servidor.** Permite mostrar el ciclo completo de compra sin añadir un frontend compilado. Jinja escapa contenido y Flask-WTF valida CSRF. Se descartó una SPA porque no aporta al requisito distintivo y duplicaría validación, autenticación y despliegue.

**Dinero en centavos enteros.** Los precios se leen del catálogo servidor y se copian a las partidas. Se evita la pérdida de precisión de floats y la manipulación de totales enviados desde el navegador. El checkout usa transacción y bloqueo de filas en PostgreSQL. La clave de solicitud única evita duplicar un pedido antes de rotar el formulario.

**Outbox en RDS y servicio propio.** La transacción escribe pedido y aviso pendiente juntos. Un proceso separado consulta cada dos segundos con `FOR UPDATE SKIP LOCKED`, guarda el mensaje y marca su envío simulado en la misma transacción. Un rollback conserva el pendiente y permite reintentar. Se descartan llamadas síncronas al notificador, pues un reinicio podría dejar una compra confirmada sin aviso. No se requiere correo externo ni otro servicio de colas para este tema.

**S3 privado a través de la API.** La API valida, recodifica y escribe imágenes, y sirve los objetos del catálogo. No hay ACL pública ni credenciales en el navegador. La contrapartida es consumir ancho de banda y CPU de EC2; en producción se evaluaría CDN y URLs firmadas.

**RDS privada, TLS y usuario específico.** RDS está en dos subredes privadas, usa almacenamiento cifrado y acepta 5432 exclusivamente desde el grupo de EC2. El proceso de aplicación utiliza un usuario limitado al esquema `market`, distinto del administrador. El cliente verifica la CA oficial de Amazon y el hostname.

**EC2 pequeña y Compose.** API y notificador se construyen desde fuentes propias, con UID no root, HEALTHCHECK, dependencias fijas, filesystem de solo lectura y límites de recursos. Nginx termina HTTPS como tercer contenedor auxiliar. Se descartó Kubernetes por memoria y complejidad no necesarias para la rúbrica.

**Certificado autofirmado.** No se recibió un dominio. HTTPS mantiene el cifrado y cookies Secure, pero el navegador exige validar la excepción. El smoke test verifica explícitamente el certificado público exportado de la EC2; no desactiva la validación de TLS. Antes de producción es necesario un dominio/certificado confiable y una estrategia de renovación.

**Terraform adaptado al laboratorio.** Se conserva el estado existente en `infra/terraform`. La creación base de S3 usa una operación idempotente, ya que Academy deniega `GetBucketObjectLockConfiguration`. Los controles de cifrado, privacidad y TLS son recursos Terraform y se escanean. Esta adaptación no elimina los buckets en destroy, y el código documenta ese límite.

## Consecuencias y riesgos aceptados

Se utiliza una sola instancia EC2 y una sola RDS; una interrupción afecta la disponibilidad. No se hacen afirmaciones de alta disponibilidad, producción o auditoría completa. Los mensajes son simulados y no existe cobro real. No se modificó el rol institucional compartido; el mínimo privilegio de AWS queda restringido por la configuración de Academy. El estado local contiene secretos aunque Git lo ignore.

## Verificación

Las pruebas automatizadas cubren autenticación, CSRF, precios, propiedad de pedidos, inventario, rollback, validación de imágenes, publicación, idempotencia del notificador y el gate final. La prueba de navegador registra un pedido y sube un producto reales. `reportes/aws/containers_rds.txt` demuestra UID 10001, contenedores saludables y conexión TLS 1.3 con `marketplace_runtime`.
