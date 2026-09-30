# Mercado Nube

Marketplace individual de la Entrega Final de LSCA2314. Backend Python con Flask, catálogo, publicación de productos, carrito y pedidos. La entrega final añade reenvío autorizado por SMTP a un buzón privado de pruebas.

**Entrega final:** [documento, clasificación, pipeline rojo/verde y Producción](docs/entrega_final.md). La instancia anterior es QA; la nueva instancia de Producción solo recibió el código corregido. Los reportes del Avance 2 se conservan como históricos.

- **Repositorio:** https://github.com/Lolmastercraft/Avance-2
- **Aplicación QA del laboratorio:** https://3.93.143.140
- **Salud QA:** https://3.93.143.140/salud
- **Guía completa:** [docs/README.md](docs/README.md)
- **Documento de evidencias:** [entrega/Evidencias_Avance2_Mercado_Nube.docx](entrega/Evidencias_Avance2_Mercado_Nube.docx)
- **Arquitectura:** [diagrama](docs/diagrama_arquitectura.png)
- **Pipeline:** [decisiones](docs/tabla_decisiones_pipeline.md), [corrida roja](reportes/corrida_roja.txt), [corrida verde](reportes/corrida_verde.txt), [SBOM](reportes/sbom_cyclonedx.json)

El sitio usa un certificado autofirmado de laboratorio. Para la demostración, abre la dirección y acepta la advertencia solo para esta instancia. No se realizan pagos ni envíos reales. La IP depende de la sesión de EC2; si cambia, consulta Systems Manager o Terraform y actualiza el certificado/URL.
