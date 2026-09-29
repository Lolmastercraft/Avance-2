# Respuesta al hallazgo de reenvío no autorizado

## Contención inmediata

El parche se mantuvo en `/opt/marketplace-final-qa` dentro de la instancia QA existente. Las solicitudes inseguras se reprodujeron mediante el cliente de pruebas Flask en un contenedor sin publicar puertos. El servicio web anterior siguió funcionando sin el endpoint vulnerable. No se desplegó el parche en Producción.

El primer pipeline no detectó la falla, por lo que se suspendió la promoción, se conservó esa evidencia y se añadieron pruebas de autorización. La corrida roja posterior bloqueó el candidato. No se modificaron los umbrales para conseguir el bloqueo.

Para futuras incidencias se implementó `RESEND_ENABLED=false`: desactiva el reenvío con HTTP 503 antes de consultar o enviar. La prueba `test_resend_containment_flag_blocks_all_delivery` comprueba que no sale ningún mensaje. Es una contención temporal, no la corrección de la causa raíz. No se afirma que esta bandera existiera antes del análisis.

## Prevención y remediación

El commit `b0b127b` exige sesión y filtra por propietario en RDS antes del efecto de envío. La funcionalidad no se borró, comentó ni revirtió. La UI conserva el botón para el comprador. Las regresiones de usuario ajeno, anónimo, CSRF, pedido inexistente y destinatario manipulado se ejecutan en el pipeline.

Se añadieron límite de frecuencia y tratamiento seguro del error SMTP. El limitador actual usa memoria y un único proceso de API: no es suficiente para un despliegue distribuido. En un sistema real se requeriría almacenamiento compartido, auditoría de reenvíos, alertas y límites persistentes por pedido.

## Verificación y promoción

El pipeline completo se ejecutó en QA. El despliegue lee el veredicto verde y compara el SHA-256 de los archivos desplegables antes de transferirlos. La transferencia se verifica de nuevo mediante SHA-256 en la instancia destino. QA y Producción registran el mismo hash del contenido desplegado en `release-final.json`.

Las evidencias incluyen el candidato original que pasó sin detectar el riesgo, la corrida bloqueada, la corrida corregida y pruebas HTTP/SMTP sobre ambas instancias. El código vulnerable permanece solamente en el historial y en el artefacto privado de QA para trazabilidad.

## Alcance de los datos

Las pruebas usan cuentas y pedidos de demostración. El reenvío utiliza SMTP real, pero termina en Mailpit, accesible solo desde la red interna de Docker. No se envía correo a proveedores externos ni se expone la interfaz del buzón al público.

Producción usa otra base lógica y otro usuario de PostgreSQL en el RDS existente; comparte VPC, grupo de seguridad, instancia RDS y bucket de imágenes con QA. Esta separación académica no equivale a aislamiento productivo por cuenta AWS o servidor independiente. Los roles Academy conservan las restricciones y permisos del laboratorio.
