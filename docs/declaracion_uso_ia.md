# Declaración de uso de inteligencia artificial

Para este Avance 2 utilicé Codex como apoyo sustancial de implementación. Le proporcioné las instrucciones de la actividad, el trabajo anterior, el tema Marketplace, el repositorio y acceso temporal al laboratorio AWS.

La IA generó y ejecutó la mayor parte del código de la aplicación, las plantillas HTML/CSS, la configuración de Docker/Terraform, los scripts de despliegue, las pruebas, el pipeline y la documentación. También produjo las ilustraciones vectoriales del catálogo y reunió evidencia mediante pruebas reales de la aplicación y consultas de AWS.

Mi participación durante esta sesión consistió en elegir y confirmar el tema Marketplace, proporcionar los materiales y el laboratorio, indicar los entregables y facilitar el repositorio. No atribuyo a mi autoría manual los archivos generados por la IA ni afirmo haber corregido personalmente problemas que solucionó el asistente.

Durante la implementación el asistente corrigió, a partir de errores observados, el acceso a contexto de usuario en respuestas CSRF, la referencia del limitador en pruebas, los permisos de creación de esquema en PostgreSQL y la opción de salida del generador de SBOM. Las evidencias roja y verde fueron ejecutadas, no inventadas. El candidato inseguro de la corrida roja es intencional y está aislado de la aplicación desplegada.

Antes de entregar debo revisar el código y ser capaz de explicar el checkout transaccional, la separación del notificador, el uso real de S3/RDS, los umbrales del pipeline y los riesgos aceptados. El video queda a mi cargo. Esta declaración describe el trabajo efectivamente realizado; no sustituye mi responsabilidad de comprenderlo ni afirma una revisión personal todavía no efectuada.
