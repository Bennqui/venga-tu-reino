/* Venga tu Reino: funciona sin conexión. La app y sus textos se guardan en el teléfono.
   hoy.js (el Evangelio del día) se busca primero en internet y, si no hay, se usa el último guardado.
   dias/AAAA-MM-DD.js (los días preparados por adelantado) también se guardan, para que la app cambie de día sin internet. */
const V='vtr-v10';
const BASE=['./','index.html','hoy.js','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(BASE)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const r=e.request;if(r.method!=='GET')return;
  const u=new URL(r.url);
  /* Día preparado: primero internet (por si hubo una corrección); si no hay señal, o tarda más de 4 s, la copia guardada. */
  if(u.origin===location.origin&&/\/dias\/\d{4}-\d\d-\d\d\.js$/.test(u.pathname)){
    const key=u.pathname;
    e.respondWith(new Promise(ok=>{
      let listo=false;const da=x=>{if(!listo){listo=true;ok(x)}};
      const guardado=()=>caches.match(key);
      const nada=()=>new Response('',{status:504,statusText:'Sin conexion'});
      const t1=setTimeout(()=>guardado().then(m=>{if(m)da(m)}),4000);
      const t2=setTimeout(()=>guardado().then(m=>da(m||nada())),9000);
      fetch(key,{cache:'no-store'}).then(res=>{
        clearTimeout(t1);clearTimeout(t2);
        if(res.ok){const cp=res.clone();caches.open(V).then(c=>c.put(key,cp));da(res)}
        else guardado().then(m=>da(m||res));
      }).catch(()=>{clearTimeout(t1);clearTimeout(t2);guardado().then(m=>da(m||nada()))});
    }));
    return;
  }
  const fresh=u.origin===location.origin&&(u.pathname.endsWith('/hoy.js')||r.mode==='navigate');
  if(fresh){
    const key=r.mode==='navigate'?'index.html':'hoy.js';
    e.respondWith(fetch(r,{cache:'no-store'}).then(res=>{if(res.ok){const cp=res.clone();caches.open(V).then(c=>c.put(key,cp))}return res})
      .catch(()=>caches.match(key).then(m=>m||caches.match('index.html'))));
    return;
  }
  if(u.origin===location.origin||/(fonts\.(googleapis|gstatic)|upload\.wikimedia)\.(com|org)$/.test(u.hostname)){
    e.respondWith(caches.match(r).then(m=>{
      const net=fetch(r).then(res=>{if(res&&(res.ok||res.type==='opaque')){const cp=res.clone();caches.open(V).then(c=>c.put(r,cp))}return res}).catch(()=>m);
      return m||net;
    }));
  }
});
