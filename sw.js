/* Venga tu Reino: funciona sin conexión. La app y sus textos se guardan en el teléfono;
   hoy.js (el Evangelio del día) se busca primero en internet y, si no hay, se usa el último guardado. */
const V='vtr-v7';
const BASE=['./','index.html','hoy.js','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(BASE)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const r=e.request;if(r.method!=='GET')return;
  const u=new URL(r.url);
  const fresh=u.origin===location.origin&&(u.pathname.endsWith('/hoy.js')||r.mode==='navigate');
  if(fresh){
    e.respondWith(fetch(r).then(res=>{const cp=res.clone();caches.open(V).then(c=>c.put(r.mode==='navigate'?'index.html':r,cp));return res})
      .catch(()=>caches.match(r.mode==='navigate'?'index.html':r).then(m=>m||caches.match('index.html'))));
    return;
  }
  if(u.origin===location.origin||/(fonts\.(googleapis|gstatic)|upload\.wikimedia)\.(com|org)$/.test(u.hostname)){
    e.respondWith(caches.match(r).then(m=>{
      const net=fetch(r).then(res=>{if(res&&(res.ok||res.type==='opaque')){const cp=res.clone();caches.open(V).then(c=>c.put(r,cp))}return res}).catch(()=>m);
      return m||net;
    }));
  }
});
