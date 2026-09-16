// End-to-end real sobre la aplicación propia desplegada en AWS.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const sharp = require(process.env.SHARP_MODULE || 'sharp');

(async () => {
  const root = path.resolve(__dirname, '..');
  const out = path.join(root, 'docs', 'capturas');
  fs.mkdirSync(out, {recursive:true});
  fs.mkdirSync(path.join(root, '.work'), {recursive:true});
  const browser = await chromium.launch({headless:true,channel:'msedge'});
  // Certificado autofirmado del laboratorio; la API se verifica por CA en smoke.py.
  const context = await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1440,height:1060},locale:'es-MX'});
  const page = await context.newPage();
  const errors=[];
  page.on('pageerror', e=>errors.push(e.message));
  const base='https://100.24.2.141';
  await page.goto(base,{waitUntil:'networkidle'});
  await page.screenshot({path:path.join(out,'01_catalogo.png'),fullPage:true});
  if(await page.locator('.product').count()<6) throw new Error('Catalog incomplete');
  await page.getByRole('link',{name:'Crear cuenta'}).click();
  await page.getByLabel('Nombre',{exact:true}).fill('Luis Demo');
  const email='demo.'+Date.now()+'@example.test';
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña').fill(crypto.randomBytes(24).toString('base64url'));
  await page.getByRole('button',{name:'Crear cuenta'}).click();
  await page.waitForURL(base+'/');
  await page.getByRole('button',{name:'Agregar Audífonos Pulse',exact:true}).click();
  await page.waitForURL('**/carrito');
  await page.screenshot({path:path.join(out,'02_carrito.png'),fullPage:true});
  await page.getByRole('button',{name:'Confirmar pedido'}).click();
  await page.waitForURL(/\/pedidos\/\d+$/);
  const orderURL=page.url();
  for(let i=0;i<12;i++){
    if(await page.getByRole('heading',{name:'Confirmación enviada',exact:true}).count())break;
    await page.waitForTimeout(1000);
    await page.reload({waitUntil:'networkidle'});
  }
  if(!(await page.getByRole('heading',{name:'Confirmación enviada',exact:true}).count()))throw new Error('Worker did not deliver');
  await page.screenshot({path:path.join(out,'03_pedido_confirmado.png'),fullPage:true});
  await page.getByRole('link',{name:'Vender',exact:true}).click();
  const image=path.join(root,'.work','demo-product.png');
  await sharp(path.join(root,'app/assets/mug.svg')).png().toFile(image);
  const name='Taza de autor '+Date.now().toString().slice(-5);
  await page.getByLabel('Nombre del producto').fill(name);
  await page.getByLabel('Descripción',{exact:true}).fill('Publicación de prueba completa: imagen cargada desde el formulario y guardada en S3.');
  await page.getByLabel('Categoría').selectOption('Escritorio');
  await page.getByLabel('Precio en MXN').fill('299.00');
  await page.getByLabel('Existencias').fill('8');
  await page.getByLabel('Imagen del producto').setInputFiles(image);
  await page.screenshot({path:path.join(out,'04_publicar_producto.png'),fullPage:true});
  await page.getByRole('button',{name:'Publicar producto',exact:false}).click();
  await page.waitForURL(base+'/');
  await page.getByLabel('Buscar productos').fill(name);
  await page.getByRole('button',{name:'Buscar',exact:true}).click();
  await page.waitForLoadState('networkidle');
  if(!(await page.getByRole('heading',{name,exact:true}).count()))throw new Error('Published product missing');
  await page.screenshot({path:path.join(out,'05_producto_s3.png'),fullPage:true});
  await page.goto(base+'/salud');
  const health=JSON.parse(await page.locator('body').innerText());
  if(health.status!=='ok'||errors.length)throw new Error(JSON.stringify({health,errors}));
  fs.writeFileSync(path.join(root,'reportes/aws/e2e.json'),JSON.stringify({utc:new Date().toISOString(),base,orderURL,product:name,registration:true,checkout:true,notification:true,s3_upload:true,health,browser_errors:errors},null,2));
  await browser.close();
  console.log(JSON.stringify({e2e:'PASS',orderURL,product:name,screenshots:5}));
})().catch(e=>{console.error(e);process.exit(1)});
