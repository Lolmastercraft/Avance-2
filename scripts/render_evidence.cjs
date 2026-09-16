// Renderiza exclusivamente evidencia registrada; no imita la consola de AWS.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const sharp = require('sharp');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const table = (headers, rows) => `<table><thead><tr>${headers.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(x=>`<td>${esc(x)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
async function main() {
  await sharp(path.join(root,'docs/diagrama_arquitectura.svg')).png().toFile(path.join(root,'docs/diagrama_arquitectura.png'));
  const aws = JSON.parse(read('reportes/aws/infraestructura.json'));
  const raw = read('reportes/aws/containers_rds.txt');
  const containers = raw.split('\n').filter(x=>x.startsWith('{')).map(x=>JSON.parse(x));
  const red = JSON.parse(read('reportes/roja/veredicto.json'));
  const green = JSON.parse(read('reportes/verde/veredicto.json'));
  const reports = [
    ['06_aws_s3_rds','Recursos reales de AWS',`<p>Consulta de AWS API · ${esc(aws.utc)} · ${esc(aws.region)}</p><h2>RDS PostgreSQL</h2>${table(['Control','Valor observado'],[['Instancia',aws.rds.DBInstanceIdentifier],['Estado',aws.rds.DBInstanceStatus],['StorageEncrypted',aws.rds.StorageEncrypted],['PubliclyAccessible',aws.rds.PubliclyAccessible],['Acceso 5432','Solo SG de la EC2, sin rangos IP públicos'],['Subredes privadas',aws.rds.DBSubnetGroup.Subnets.length]])}<h2>Amazon S3</h2>${table(['Bucket','Cifrado','Bloqueo público','Versionado','Objetos products/'],aws.buckets.map(b=>[b.name,b.encryption.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm,Object.values(b.public_access).every(Boolean),b.versioning,b.product_objects.length]))}<p>Ambos buckets rechazan transporte sin TLS. Imagen subida por el formulario: ${esc(aws.buckets[0].product_objects.find(x=>x.Key.endsWith('.jpg')).Key)}</p><p class="source">Fuente íntegra: reportes/aws/infraestructura.json. Esta es una visualización de datos consultados por API, no una captura de la consola AWS.</p>`],
    ['07_contenedores','Contenedores y persistencia real',`<p>Salida de AWS Systems Manager desde EC2 ${esc(aws.instance.InstanceId)}</p>${table(['Servicio','Imagen','Estado','Salud'],containers.map(c=>[c.Service,c.Image,c.State,c.Health]))}<h2>Usuarios de ejecución y conexión a RDS</h2><pre>${esc(raw.split('\n').filter(x=>!x.startsWith('{')).join('\n'))}</pre><p>API y notificaciones son dos contenedores propios. El tercero termina HTTPS. Los dos servicios propios no publican puertos directamente en el host.</p><p class="source">Fuente íntegra: reportes/aws/containers_rds.txt. La confirmación se procesa mediante el servicio de notificaciones y queda persistida en RDS.</p>`],
    ['08_pipeline','Pipeline integrado de seguridad',`<p>Mismo conjunto de controles y umbrales en ambos candidatos.</p>${table(['Etapa','Candidato rojo','Fuentes corregidas'],Object.keys(green.stages).map(k=>[k,red.stages[k].ok?'PASS':'FAIL',green.stages[k].ok?'PASS':'FAIL']))}<h2>Decisión roja: ${esc(red.verdict)} · Decisión verde: ${esc(green.verdict)}</h2><p>Bandit detectó una llamada a shell con entrada concatenada en un candidato temporal aislado. Ese candidato no se ejecutó ni se desplegó. La versión segura no incluye ese código; el buscador usa consultas parametrizadas.</p><p>Roja UTC: ${esc(red.utc)}<br>Verde UTC: ${esc(green.utc)}</p><p class="source">Fuentes completas: reportes/corrida_roja.txt, reportes/corrida_verde.txt y reportes/{roja,verde}/. No se cambiaron umbrales entre corridas.</p>`]
  ];
  const browser = await chromium.launch({channel:'msedge',headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
  for(const [name,title,body] of reports) {
    await page.setContent(`<!doctype html><html lang="es"><meta charset="utf-8"><style>body{font:22px/1.45 Arial;color:#1f302a;background:#f5f7f6;margin:0;padding:55px 65px}h1{font-size:40px;margin:0 0 18px}h2{font-size:27px;margin:27px 0 14px}p{margin:18px 0}table{width:100%;border-collapse:collapse;background:white;font-size:20px}td,th{border:1px solid #cbd8d0;padding:15px;text-align:left;overflow-wrap:anywhere}th{background:#174c3c;color:white}pre{white-space:pre-wrap;font-size:20px;background:white;padding:24px;border:1px solid #cbd8d0}.source{font-size:18px;color:#496357}small{letter-spacing:2px;color:#496357}</style><small>MERCADO NUBE · EVIDENCIA VERIFICABLE</small><h1>${esc(title)}</h1>${body}</html>`);
    await page.screenshot({path:path.join(root,'docs/capturas',name+'.png'),fullPage:true});
  }
  await browser.close();
}
main().catch(e=>{console.error(e);process.exit(1)});
