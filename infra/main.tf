# Punto de entrada de la estructura de entrega. El despliegue existente conserva
# su estado en infra/terraform; no ejecutar apply aquí sobre la misma cuenta.
module "marketplace" {
  source = "./terraform"
}
