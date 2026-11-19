/* Después de cambiar datos.js, ejecuta: node tareas/version-datos.js
   Pone en index.html la huella de datos.js (datos.js?v=xxxx) para que el iPhone descargue la versión nueva. */
const fs=require('fs'),crypto=require('crypto'),path=require('path');
const raiz=path.join(__dirname,'..'),d=fs.readFileSync(path.join(raiz,'datos.js'));
const h=crypto.createHash('sha1').update(d).digest('hex').slice(0,8);
const f=path.join(raiz,'index.html');let s=fs.readFileSync(f,'utf8');
const n=s.replace(/datos\.js\?v=[0-9a-f]+/,'datos.js?v='+h);
if(n===s&&!s.includes('datos.js?v='+h)){console.error('No encontré datos.js?v= en index.html');process.exit(1)}
fs.writeFileSync(f,n);console.log('datos.js?v='+h);
