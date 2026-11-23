/* Carga el código real de index.html y datos.js sin navegador y devuelve sus funciones del calendario.
   Lo usan tareas/prueba-calendario.js y tareas/revisar-dias.js. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const raiz = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(raiz, 'index.html'), 'utf8');
const datos = fs.readFileSync(path.join(raiz, 'datos.js'), 'utf8');
const ini = html.indexOf('<script>\n(function(){');
const fin = html.indexOf('\n})();', ini);
if (ini < 0 || fin < 0) { console.error('No encontré el código principal en index.html'); process.exit(1); }
const cuerpo = html.slice(ini + '<script>\n(function(){'.length, fin);

/* Un «navegador» de mentira: cualquier cosa que el código toque devuelve algo inofensivo. */
const nada = new Proxy(function () {}, {
  get: (t, k) => k === Symbol.toPrimitive ? () => '' : k === 'then' ? undefined : k === Symbol.iterator ? function* () {} : nada,
  apply: () => nada, construct: () => nada, set: () => true
});
const mem = {};
const ctx = {
  console, Math, JSON, Date, Intl, Promise, Set, Map, Object, Array, String, Number, RegExp, Symbol, Error, parseInt, parseFloat, isNaN,
  encodeURIComponent, decodeURIComponent, setTimeout: () => 0, clearTimeout: () => 0, setInterval: () => 0, requestAnimationFrame: () => 0,
  fetch: () => new Promise(() => {}), document: nada, navigator: nada, location: nada, history: nada, matchMedia: () => nada,
  addEventListener: () => {}, removeEventListener: () => {}, getComputedStyle: () => nada, IntersectionObserver: function () { return nada },
  speechSynthesis: nada, SpeechSynthesisUtterance: function () { return nada }, caches: nada, performance: nada,
  localStorage: { getItem: k => (k in mem ? mem[k] : null), setItem: (k, v) => { mem[k] = String(v) }, removeItem: k => { delete mem[k] } },
  innerWidth: 390, innerHeight: 844, scrollY: 0, scrollTo: () => {}, devicePixelRatio: 2
};
ctx.window = ctx; ctx.self = ctx; ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(datos, ctx);
/* Lo que el código busque y no exista en esta prueba (pantalla, sonidos…) recibe un objeto inofensivo. */
const propios = new Set((datos.match(/^(?:const|let|var|function)\s+([A-Za-z_$][\w$]*)/gm) || []).map(x => x.split(/\s+/)[1]));
ctx.__G = new Proxy({}, { has: (t, k) => typeof k === 'string' && !(k in ctx) && !propios.has(k) && k !== '__T', get: (t, k) => k === Symbol.unscopables ? undefined : nada });
vm.runInContext('with(__G){(function(){' + cuerpo + '\n;globalThis.__T={liturgia,misDia,cicloDom,cicloSem,santoDia};})();}', ctx);
module.exports = ctx.__T;

