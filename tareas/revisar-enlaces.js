/* Revisa cada noche que los enlaces oficiales de la app abran (Vatican News, vatican.va, ACI Prensa).
   Falla (y GitHub avisa por correo) solo si una página ya no existe (404/410) o el sitio no responde.
   Un 403 u otro bloqueo a robots se muestra como aviso, porque en el iPhone sí abre. */
const fs=require('fs');
const html=fs.readFileSync(__dirname+'/../index.html','utf8');
const urls=new Set();
const hoy=new Date();
for(let i=0;i<8;i++){const d=new Date(hoy.getTime()+i*864e5);const y=d.getFullYear(),m=String(d.getMonth()+1).padStart(2,'0'),dd=String(d.getDate()).padStart(2,'0');
  urls.add(`https://www.vaticannews.va/es/evangelio-de-hoy/${y}/${m}/${dd}.html`)}
for(const m of html.matchAll(/https:\/\/(?:www\.)?(?:vatican\.va|aciprensa\.com)\/[^'"\s<]+/g))urls.add(m[0]);
(async()=>{
  let malos=0,avisos=0;
  for(const u of urls){
    let r;try{r=await fetch(u,{redirect:'follow',headers:{'user-agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1'},signal:AbortSignal.timeout(20000)})}catch(e){r=null}
    const st=r?r.status:'sin respuesta';
    if(r&&r.ok)console.log('✓',u);
    else if(r&&(r.status===404||r.status===410)){malos++;console.log('✗',st,u)}
    else if(!r){malos++;console.log('✗',st,u)}
    else{avisos++;console.log('·',st,'(aviso)',u)}
  }
  console.log(`\n${urls.size} enlaces · ${malos} rotos · ${avisos} avisos`);
  process.exit(malos?1:0);
})();
