/* Prueba automática del calendario litúrgico de la app (calendario de Venezuela).
   Ejecuta el código real de index.html sin navegador y revisa fechas clave de varios años.
   Uso: node tareas/prueba-calendario.js   (sale con error si alguna fecha está mal) */
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
const T = ctx.__T;

/* [fecha, celebración esperada (texto que debe aparecer), color] — calendario litúrgico de Venezuela */
const CASOS = [
  ['2026-11-22', 'Rey del Universo', 'blanco'],
  ['2026-11-29', 'Domingo I de Adviento', 'morado'],
  ['2026-12-08', 'Inmaculada', 'blanco'],
  ['2026-12-12', 'Guadalupe', 'blanco'],
  ['2026-12-13', 'Domingo III de Adviento', 'rosa'],
  ['2026-12-14', 'Juan de la Cruz', 'blanco'],
  ['2026-11-23', 'semana 34', 'verde'],
  ['2026-12-25', 'Natividad', 'blanco'],
  ['2026-12-26', 'San Esteban', 'rojo'],
  ['2026-12-27', 'Sagrada Familia', 'blanco'],
  ['2027-01-01', 'Madre de Dios', 'blanco'],
  ['2027-01-06', 'Epifanía', 'blanco'],
  ['2027-01-10', 'Bautismo del Señor', 'blanco'],
  ['2027-01-11', 'semana 1 del Tiempo Ordinario', 'verde'],
  ['2027-01-14', 'Divina Pastora', 'blanco'],
  ['2027-02-10', 'Miércoles de Ceniza', 'morado'],
  ['2027-03-07', 'Domingo IV de Cuaresma', 'rosa'],
  ['2027-03-19', 'José', 'blanco'],
  ['2027-03-21', 'Domingo de Ramos', 'rojo'],
  ['2027-03-25', 'Jueves Santo', 'blanco'],
  ['2027-03-26', 'Viernes Santo', 'rojo'],
  ['2027-03-28', 'Domingo de Pascua', 'blanco'],
  ['2027-04-04', 'Domingo II de Pascua', 'blanco'],
  ['2027-04-05', 'Anunciación', 'blanco'],
  ['2027-05-09', 'Ascensión', 'blanco'],
  ['2027-05-16', 'Pentecostés', 'rojo'],
  ['2027-05-17', 'Madre de la Iglesia', 'blanco'],
  ['2027-05-23', 'Santísima Trinidad', 'blanco'],
  ['2027-05-30', 'Corpus Christi', 'blanco'],
  ['2027-06-04', 'Sagrado Corazón', 'blanco'],
  ['2027-06-29', 'Pedro', 'rojo'],
  ['2027-08-15', 'Asunción', 'blanco'],
  ['2027-09-11', 'Coromoto', 'blanco'],
  ['2027-10-26', 'José Gregorio', 'blanco'],
  ['2027-11-01', 'Todos los Santos', 'blanco'],
  ['2027-11-21', 'Rey del Universo', 'blanco'],
  ['2027-11-28', 'Domingo I de Adviento', 'morado'],
  ['2028-01-09', 'Bautismo del Señor', 'blanco'],
  ['2028-04-16', 'Domingo de Pascua', 'blanco'],
  ['2028-06-04', 'Pentecostés', 'rojo'],
];
let mal = 0;
for (const [f, tit, col] of CASOS) {
  for (const hora of ['00:05', '12:00', '23:55']) {          // la hora del teléfono no debe cambiar el día litúrgico
    const d = new Date(f + 'T' + hora + ':00');
    const L = T.liturgia(d), S = T.santoDia(d, L);           // igual que misaHoy() cuando el día no está preparado
    const titulo = (S && S.n) || L.titulo, color = (S && S.color) || L.color;
    const ok = (titulo || '').includes(tit) && color === col;
    if (!ok) { mal++; console.log('MAL', f, hora, '→', titulo, '·', color, '| esperado:', tit, '·', col); }
  }
}
/* ciclos: el domingo I de Adviento cambia el ciclo dominical */
const ciclos = [['2026-11-28', 'A'], ['2026-11-29', 'B'], ['2027-11-28', 'C'], ['2028-12-03', 'A']];
for (const [f, c] of ciclos) { const r = T.cicloDom(new Date(f + 'T12:00:00')); if (r !== c) { mal++; console.log('MAL ciclo', f, r, '≠', c) } }
/* Rosario: misterios del día (san Juan Pablo II, Rosarium Virginis Mariae) */
const ros = [['2026-11-23', 'Gozosos'], ['2026-11-24', 'Dolorosos'], ['2026-11-25', 'Gloriosos'], ['2026-11-26', 'Luminosos'], ['2026-11-27', 'Dolorosos'], ['2026-11-28', 'Gozosos'], ['2026-11-22', 'Gloriosos'], ['2026-12-06', 'Gozosos'], ['2027-02-14', 'Dolorosos']];
for (const [f, m] of ros) { const d = new Date(f + 'T12:00:00'); const r = T.misDia(d, T.liturgia(d)).n; if (r !== m) { mal++; console.log('MAL rosario', f, r, '≠', m) } }
console.log(mal ? mal + ' fallos' : 'Calendario OK: ' + CASOS.length + ' fechas (a 3 horas distintas), ciclos y misterios del Rosario');
process.exit(mal ? 1 : 0);
