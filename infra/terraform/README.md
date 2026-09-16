# Infraestructura del Marketplace

Esta configuración crea recursos aislados para el Avance 2:

- una VPC `10.42.0.0/16`;
- una subred pública para EC2 y dos privadas en zonas distintas para RDS;
- una instancia EC2 pequeña con Amazon Linux 2023, Docker, Compose e IMDSv2;
- acceso administrativo mediante Systems Manager, sin abrir SSH;
- PostgreSQL RDS cifrado, privado y accesible solamente desde el grupo de seguridad de EC2;
- dos buckets S3 privados, cifrados, versionados y con bloqueo total de acceso público;
- un endpoint de VPC gratuito para el tráfico hacia S3.

La contraseña de RDS se genera automáticamente y queda marcada como sensible. El estado local de Terraform y cualquier archivo `.env` están excluidos de Git.

> Nota del Learner Lab: su política institucional bloquea la lectura de la
> configuración Object Lock. Por ello, Terraform crea los nombres base de S3
> mediante una llamada idempotente a AWS CLI y administra declarativamente el
> cifrado, versionado, propiedad, ciclo de vida, política TLS y bloqueo público.

## Uso

```powershell
$env:AWS_PROFILE = "avance2-lab"
terraform init
terraform plan -out marketplace.tfplan
terraform apply marketplace.tfplan
```

Antes de cerrar definitivamente el Learner Lab, los recursos pueden retirarse con:

```powershell
terraform destroy
```

La destrucción es deliberadamente manual para evitar eliminar evidencia o datos por accidente.
