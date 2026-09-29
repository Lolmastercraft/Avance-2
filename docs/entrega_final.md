# Entrega final del marketplace

Esta entrega continúa el Avance 2 y demuestra el ciclo del parche docente de reenvío de confirmación. Los documentos y reportes anteriores se conservan como evidencia histórica.

## Entregables

- [Documento para la plataforma](../entrega/Evidencias_EntregaFinal_Mercado_Nube.docx), basado en la plantilla del profesor.
- [Clasificación del hallazgo](clasificacion_hallazgo.md).
- [Contención y prevención](respuesta_incidente.md).
- [Promoción a Producción y capturas](evidencia_produccion.md).
- [Declaración de IA](declaracion_ia.md).
- [Pipeline original que no detectó la falla](../reportes/final/baseline/pipeline_original.txt).
- [Corrida bloqueada completa](../reportes/pipeline_bloqueado.txt) y [corrida verde completa](../reportes/pipeline_verde.txt).
- [Diff de remediación](https://github.com/Lolmastercraft/Avance-2/commit/b0b127b).
- [Infraestructura de la nueva instancia](../infra/final/main.tf).

## Secuencia comprobable

1. `41e10c0`: integración del parche original en el candidato aislado de QA. El pipeline original pasa y deja constancia de la cobertura insuficiente.
2. `9bdb8d6`: se agregan pruebas de propiedad y autenticación. El pipeline de QA bloquea: dos fallos y 18 pruebas aprobadas.
3. `b0b127b`: se corrige la consulta y se exige sesión antes de enviar. Se conserva el reenvío SMTP al buzón de prueba. Pipeline de QA: 23 pruebas aprobadas y las ocho etapas en verde.
4. Promoción del contenido aprobado a la nueva EC2 y pruebas HTTP, RDS, TLS, SMTP y UI.

No se reutilizó la demostración artificial `unsafe_probe.py` del Avance 2 para esta entrega. No se exige un video nuevo en los materiales de la entrega final recibidos.

## Repetir las pruebas

Las pruebas unitarias se ejecutan con `python -m pytest -q tests`. Para un pipeline completo en Linux se construye `deploy/Dockerfile.qa`; el registro requiere herramientas, conexión saliente y la URL/CA vigentes de QA. `MARKETPLACE_URL` y `MARKETPLACE_CA` permiten seleccionar esas rutas sin desactivar la comprobación TLS.

`pipeline/run.py --label verde --runtime-python /opt/runtime/bin/python --report-root reportes/final --report-name pipeline_verde.txt` ejecuta las ocho etapas. No se debe sobrescribir la evidencia original si se repite después de la entrega; utilizar otro directorio de reportes.

`scripts/final_promote.py` exige veredicto verde y coincidencia del hash. Las credenciales se leen del archivo externo indicado en `scripts/final_lab.py`, nunca se incluyen en el repositorio. `scripts/final_e2e.py` crea cuentas/pedidos de prueba y envía únicamente al buzón privado: ejecutarlo solo en estos ambientes autorizados.
