# Guion para una demostración de cuatro minutos

Antes de grabar, inicia el laboratorio y confirma que https://100.24.2.141/salud responde. Acepta de antemano la advertencia del certificado del laboratorio. Abre el Marketplace, AWS Console en us-east-1 y una terminal conectada a la instancia mediante Systems Manager. Deja preparadas las dos corridas del pipeline y no muestres archivos con secretos.

| Tiempo | Pantalla y acción | Explicación breve |
|---|---|---|
| 0:00 a 1:20 | Registro/login, catálogo, agregar al carrito, confirmar y actualizar pedido | “Este es Mercado Nube. El precio se calcula en el servidor, el pedido se guarda en RDS y otro contenedor registra su confirmación simulada.” |
| 1:20 a 1:50 | Systems Manager: `cd /opt/marketplace` y `docker compose ps` | “API y notificaciones son dos servicios propios; Nginx es el proxy HTTPS. Los tres están saludables.” |
| 1:50 a 2:45 | AWS Console: S3 products, objetos y permisos/cifrado; RDS, conectividad y cifrado | “Las imágenes están realmente en S3 privado. PostgreSQL está cifrado, no tiene acceso público y solo acepta la EC2.” |
| 2:45 a 3:50 | Terminal local: ejecutar `pipeline/demostrar.py` o mostrar las dos salidas completas ya ejecutadas y sus veredictos | “Este candidato usa shell=True con texto externo; Bandit lo bloquea. La implementación parametrizada pasa los mismos umbrales. El gate consolida todas las etapas.” |
| 3:50 a 4:15 | Repositorio: tabla de decisiones, SBOM y declaración de IA | “Cada umbral responde a un riesgo del Marketplace; aquí se documentan también los límites y el uso de IA.” |

Comando para ejecutar nuevamente las corridas desde PowerShell:

```powershell
$env:GITLEAKS_BIN = 'C:\ruta\gitleaks.exe'
.venv\Scripts\python.exe pipeline\demostrar.py --runtime-python .runtime\Scripts\python.exe
```

Las corridas se ejecutan en torno a un minuto en el entorno probado, pero dependen de red y herramientas. Haz un ensayo para ajustar la duración total a 3–5 minutos. La versión roja se crea en una carpeta temporal y nunca se despliega.

Al terminar, sube el video a un lugar accesible al docente y reemplaza el contenido de `docs/enlace_video.txt` por el enlace real. Verifica sus permisos de lectura. No pongas contraseñas, tokens, `.env` ni contenido de Terraform state en pantalla.
