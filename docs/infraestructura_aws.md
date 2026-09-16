# Infraestructura AWS del Marketplace

Fecha de verificación: 16 de septiembre de 2026  
Región: `us-east-1`  
Administración: Terraform 1.16.2 con perfil temporal `avance2-lab`

## Arquitectura desplegada

```text
Internet
   |
   | HTTP/HTTPS (80/443)
   v
EC2 t3.micro - subred pública
   |-- Docker + Docker Compose
   |-- Administración por Systems Manager (sin SSH público)
   |-- Acceso privado a S3 mediante VPC Endpoint
   |
   | PostgreSQL 5432, autorizado por grupo de seguridad
   v
RDS PostgreSQL - dos subredes privadas en zonas distintas
```

La base de datos utiliza una sola zona para reducir el consumo de créditos del laboratorio. El grupo de subredes conserva dos zonas de disponibilidad, como exige RDS.

## Recursos principales

| Componente | Recurso | Configuración relevante |
|---|---|---|
| VPC | `vpc-09bf9d8984b710e22` | `10.42.0.0/16`, DNS habilitado |
| EC2 | `i-06f5d7a26aa4f1498` | `t3.micro`, Amazon Linux 2023, volumen gp3 cifrado |
| Aplicación | `https://100.24.2.141` | Marketplace desplegado; certificado autofirmado del laboratorio |
| RDS | `avance2-marketplace-postgres` | PostgreSQL 16.14, `db.t3.micro`, 20 GiB gp3 cifrados |
| RDS endpoint | `avance2-marketplace-postgres.cmsubt4q9m7q.us-east-1.rds.amazonaws.com` | Privado, puerto 5432 |
| S3 productos | `avance2-marketplace-products-468504542046` | Privado, cifrado AES-256, versionado |
| S3 evidencia | `avance2-marketplace-evidence-468504542046` | Privado, cifrado AES-256, versionado |

## Controles de seguridad verificados

- RDS no tiene acceso público.
- El puerto 5432 acepta tráfico solamente desde el grupo de seguridad de EC2.
- EC2 no expone el puerto 22; la administración se realiza con Systems Manager.
- EC2 exige IMDSv2 y utiliza almacenamiento cifrado.
- Los buckets tienen bloqueo total de acceso público, cifrado predeterminado y versionado.
- Las políticas de los buckets rechazan conexiones sin TLS.
- Las versiones antiguas de objetos expiran a los 30 días y las cargas incompletas a los 7 días.
- La VPC incluye un endpoint Gateway para S3, sin costo horario de NAT Gateway.
- Terraform terminó con `No changes`; la infraestructura real coincide con la configuración.
- La EC2 confirmó Docker 25.0.14, Docker Compose 2.35.1 y conectividad privada hacia RDS.

## Restricción documentada del Learner Lab

La política institucional deniega `s3:GetBucketObjectLockConfiguration`. El recurso general `aws_s3_bucket` consulta esa API aunque Object Lock no se use. Para mantener Terraform funcional, la creación base de los nombres S3 se realiza mediante una llamada idempotente a AWS CLI desde `terraform_data`; los controles de cifrado, versionado, propiedad, ciclo de vida, política TLS y bloqueo público permanecen administrados por recursos declarativos de Terraform.

No se guardan claves ni contraseñas en este documento. La contraseña de RDS fue generada automáticamente y permanece marcada como sensible dentro del estado local excluido de Git.
