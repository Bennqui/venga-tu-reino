#!/usr/bin/env node
/* Venga tu Reino — utilidades para los días preparados por adelantado (carpeta dias/).

   node tareas/dias.js estado    AAAA-MM-DD               resumen: hoy.js, día de hoy y hasta qué fecha hay días preparados
   node tareas/dias.js faltan    AAAA-MM-DD [n]           fechas por preparar desde hoy hasta hoy+n (n = 7 por defecto) y qué hacer con cada una
   node tareas/dias.js escribir  FECHA archivo.json       crea dias/FECHA.js a partir de un JSON completo (solo si pasa la validación)
   node tareas/dias.js completar FECHA archivo.json       agrega o reemplaza secciones de un día que ya existe (p. ej. {"conoce":{…}})
   node tareas/dias.js validar   dias/FECHA.js            revisa que el archivo de un día esté completo y bien formado
   node tareas/dias.js temas                              personas y hechos que ya salieron (para no repetir)
   node tareas/dias.js hoy       AAAA-MM-DD               copia dias/AAAA-MM-DD.js a hoy.js (solo si es válido)

   En estado, faltan y hoy, AAAA-MM-DD es siempre la fecha de HOY en Venezuela (America/Caracas). */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const RAIZ = path.resolve(__dirname, '..');
const DIAS = path.join(RAIZ, 'dias');
const RE_FECHA = /^\d{4}-\d{2}-\d{2}$/;

const aFecha = s => { const [y, m, d] = s.split('-').map(Number); return new Date(Date.UTC(y, m - 1, d)); };
const aTexto = d => d.toISOString().slice(0, 10);
const suma = (s, n) => { const d = aFecha(s); d.setUTCDate(d.getUTCDate() + n); return aTexto(d); };
const esFecha = s => RE_FECHA.test(s || '') && aTexto(aFecha(s)) === s;
const rutaDia = f => path.join(DIAS, f + '.js');
const hoyCaracas = () => new Date().toLocaleDateString('en-CA', { timeZone: 'America/Caracas' });
const serializar = H => 'window.HOY=' + JSON.stringify(H) + ';\n';

function evaluar(codigo) {
  const caja = { window: {} };
  vm.runInNewContext(codigo, caja, { timeout: 2000 });
  return { HOY: caja.window.HOY, extra: Object.keys(caja.window).filter(k => k !== 'HOY') };
}
/* La app lee los días anteriores con JSON.parse: el archivo debe ser exactamente window.HOY= + JSON + ; */
function esFormaJSON(codigo) {
  const m = /^\s*window\.HOY\s*=\s*([\s\S]*?);?\s*$/.exec(codigo);
  if (!m) return false;
  try { JSON.parse(m[1]); return true; } catch (e) { return false; }
}

const RANGOS = ['Solemnidad', 'Fiesta', 'Memoria', 'Memoria libre', 'Feria', 'Domingo'];
const COLORES = ['verde', 'morado', 'blanco', 'rojo', 'rosa'];
const TIPOS = ['Primera lectura', 'Salmo responsorial', 'Segunda lectura', 'Evangelio'];
const RELATOS = ['Parábola', 'Milagro', 'Enseñanza', 'Encuentro', 'Escena'];

function preparados() {
  if (!fs.existsSync(DIAS)) return [];
  return fs.readdirSync(DIAS).filter(f => /^\d{4}-\d{2}-\d{2}\.js$/.test(f)).map(f => f.slice(0, 10)).sort();
}
/* Personas y hechos ya usados: [{fecha, persona, hecho}] */
function temas() {
  return preparados().map(f => {
    try { const C = (evaluar(fs.readFileSync(rutaDia(f), 'utf8')).HOY || {}).conoce || {}; return { fecha: f, persona: (C.persona || {}).nombre || '', hecho: (C.hecho || {}).nombre || '' }; }
    catch (e) { return { fecha: f, persona: '', hecho: '' }; }
  });
}
const llano = s => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

/* Devuelve la lista de errores del contenido de un día (vacía si está bien). Los errores de la sección
   «Conoce tu Iglesia» empiezan por «conoce», para saber cuándo un día solo necesita esa sección. */
function validarCodigo(codigo, fechaEsperada) {
  const E = [];
  let r;
  try { r = evaluar(codigo); } catch (e) { return ['tiene un error de JavaScript: ' + e.message]; }
  const H = r.HOY;
  if (!/^\s*window\.HOY\s*=\s*\{/.test(codigo)) E.push('el archivo debe empezar con window.HOY={');
  if (r.extra.length) E.push('solo debe definir window.HOY (sobra: ' + r.extra.join(', ') + ')');
  if (!H || typeof H !== 'object') return E.concat('no define window.HOY');
  if (!esFormaJSON(codigo)) E.push('no está en la forma que escribe «node tareas/dias.js escribir»: no escribas el .js a mano, usa escribir o completar');
  if (/AAAA-MM-DD/.test(codigo)) E.push('quedó el texto de plantilla AAAA-MM-DD');

  const txt = (v, min) => typeof v === 'string' && v.trim().length >= (min || 1) && v.trim() !== '…';
  const pide = (ok, msg) => { if (!ok) E.push(msg); };
  const lista = (v, n, min) => Array.isArray(v) && v.length >= n && v.every(x => txt(x, min));

  pide(esFecha(H.fecha), 'fecha debe ser AAAA-MM-DD');
  if (fechaEsperada) pide(H.fecha === fechaEsperada, 'fecha es ' + H.fecha + ' pero el archivo es del ' + fechaEsperada);
  pide(txt(H.titulo, 5), 'falta titulo');
  pide(txt(H.fuente) && /^https:\/\//.test(H.fuente), 'fuente debe ser un enlace https');
  pide(esFecha(H.actualizado), 'actualizado debe ser AAAA-MM-DD');

  const L = Array.isArray(H.lecturas) ? H.lecturas : [];
  pide(L.length >= 3, 'lecturas debe tener al menos primera lectura, salmo y Evangelio');
  L.forEach((l, i) => {
    pide(l && TIPOS.includes(l.tipo), 'lecturas[' + i + '].tipo no válido: ' + (l && l.tipo));
    pide(l && txt(l.cita, 3), 'lecturas[' + i + '] sin cita');
    pide(l && txt(l.resumen, 30), 'lecturas[' + i + '] sin resumen');
  });
  const tiene = t => L.some(l => l && l.tipo === t);
  pide(tiene('Primera lectura'), 'falta la Primera lectura');
  pide(tiene('Salmo responsorial'), 'falta el Salmo responsorial');
  pide(L.length && L[L.length - 1] && L[L.length - 1].tipo === 'Evangelio', 'el Evangelio debe ser la última lectura');

  const ev = H.evangelio || {};
  pide(txt(ev.cita, 5), 'falta evangelio.cita');
  pide(/^(Mateo|Marcos|Lucas|Juan) /.test(ev.cita || ''), 'evangelio.cita debe empezar con Mateo, Marcos, Lucas o Juan');
  pide(lista(ev.resumen, 2, 40), 'evangelio.resumen debe tener 3 párrafos');
  pide(txt(ev.contexto, 40), 'falta evangelio.contexto');
  pide(txt(ev.significado, 150), 'evangelio.significado es muy corto');
  pide(lista(ev.hoy, 2, 10), 'evangelio.hoy debe tener 3 sugerencias');
  pide(txt(ev.pregunta, 10), 'falta evangelio.pregunta');
  pide(txt(ev.oracion, 20) && /Amén\.$/.test((ev.oracion || '').trim()), 'evangelio.oracion debe terminar en «Amén.»');
  const evL = L.find(l => l && l.tipo === 'Evangelio');
  if (evL && txt(ev.cita)) pide((evL.cita || '').split(' ')[0] === ev.cita.split(' ')[0], 'la cita del Evangelio no coincide entre lecturas y evangelio');

  const M = H.misa || {};
  pide(txt(M.celebracion, 5), 'falta misa.celebracion');
  pide(RANGOS.includes(M.rango), 'misa.rango no válido: ' + M.rango);
  pide(COLORES.includes(M.color), 'misa.color no válido: ' + M.color);
  ['gloria', 'credo', 'segunda'].forEach(k => pide(typeof M[k] === 'boolean', 'misa.' + k + ' debe ser true o false'));
  pide(M.segunda === tiene('Segunda lectura'), 'misa.segunda no coincide con las lecturas');
  pide(M.salmo && txt(M.salmo.cita, 3) && txt(M.salmo.respuesta, 5), 'falta misa.salmo (cita y respuesta)');
  const mi = /^Lectura del santo Evangelio según san (Mateo|Marcos|Lucas|Juan)$/.exec(M.evangelioIntro || '');
  pide(!!mi, 'misa.evangelioIntro debe ser exactamente «Lectura del santo Evangelio según san Mateo/Marcos/Lucas/Juan» (sin punto final)');
  if (mi && txt(ev.cita)) pide(ev.cita.indexOf(mi[1]) === 0, 'misa.evangelioIntro no coincide con el evangelista de la cita');
  const R = M.relato || {};
  pide(RELATOS.includes(R.tipo), 'misa.relato.tipo no válido: ' + R.tipo);
  pide(txt(R.titulo, 3) && txt(R.resumen, 20) && txt(R.ensenanza, 20), 'misa.relato incompleto (titulo, resumen, ensenanza)');
  if (RELATOS.includes(R.tipo) && R.tipo !== 'Parábola') pide(/^Hoy no hay parábola:/.test(R.resumen || ''), 'si no es parábola, misa.relato.resumen empieza con «Hoy no hay parábola:»');
  pide(txt(M.homilia, 20), 'falta misa.homilia');
  pide(txt(M.fieles, 5), 'falta misa.fieles');
  if ('aviso' in M) pide(txt(M.aviso, 5), 'misa.aviso está vacío (omítelo si no aplica)');

  const N = H.encuentro || {};
  pide(N.frase && txt(N.frase.texto, 5) && txt(N.frase.cita, 5), 'falta encuentro.frase (texto y cita)');
  if (N.frase && txt(N.frase.texto)) pide(!/[«»]/.test(N.frase.texto), 'encuentro.frase.texto no lleva « »');
  pide(lista(N.luces, 3, 10), 'encuentro.luces debe tener al menos 3');
  pide(N.conexion && txt(N.conexion.cita, 3) && txt(N.conexion.idea, 20), 'falta encuentro.conexion (cita e idea)');
  pide(lista(N.ver, 3, 10), 'encuentro.ver debe tener 3 preguntas');
  pide(lista(N.juzgar, 3, 10), 'encuentro.juzgar debe tener 3 preguntas');
  pide(lista(N.actuar, 2, 10), 'encuentro.actuar debe tener al menos 2 propósitos');
  if (Array.isArray(N.actuar)) {
    pide(N.actuar.some(a => /^Conversión:/.test(a || '')), 'encuentro.actuar necesita uno que empiece con «Conversión:»');
    pide(N.actuar.some(a => /^Apostolado:/.test(a || '')), 'encuentro.actuar necesita uno que empiece con «Apostolado:»');
  }
  pide(txt(N.compartir, 20), 'falta encuentro.compartir');
  if ('voz' in N) {
    const v = N.voz || {};
    pide(txt(v.autor, 3) && txt(v.texto, 10), 'encuentro.voz incompleta (autor y texto); si no hay cita verificada, omite voz');
    pide(txt(v.url) && /^https:\/\//.test(v.url), 'encuentro.voz.url debe ser el enlace https donde se vio la cita');
    if (txt(v.texto)) pide(!/[«»]/.test(v.texto), 'encuentro.voz.texto no lleva « »');
  }

  if (esFecha(H.fecha)) {
    const domingo = aFecha(H.fecha).getUTCDay() === 0;
    if (domingo) {
      pide(M.credo === true, 'es domingo: misa.credo debe ser true');
      pide(['Domingo', 'Solemnidad', 'Fiesta'].includes(M.rango), 'es domingo: misa.rango debe ser Domingo (o Solemnidad/Fiesta)');
    } else {
      pide(M.rango !== 'Domingo', 'no es domingo: misa.rango no puede ser Domingo');
    }
  }

  /* Conoce tu Iglesia: una persona y un hecho por día */
  const C = H.conoce;
  if (!C || typeof C !== 'object') E.push('conoce: falta la sección «Conoce tu Iglesia» (persona y hecho del día)');
  else {
    const usados = temas().filter(t => t.fecha !== H.fecha);
    for (const k of ['persona', 'hecho']) {
      const x = C[k], p = 'conoce.' + k;
      if (!x || typeof x !== 'object') { E.push(p + ': falta'); continue; }
      const cp = (ok, msg) => { if (!ok) E.push(p + msg); };
      cp(txt(x.nombre, 3), '.nombre falta');
      cp(txt(x.tipo, 3) && x.tipo.length <= 80, '.tipo falta o pasa de 80 caracteres');
      cp(txt(x.fechas, 2), '.fechas falta');
      if ('lugar' in x) cp(txt(x.lugar, 2), '.lugar está vacío (omítelo si no aplica)');
      cp(txt(x.resumen, 80), '.resumen es muy corto');
      cp(Array.isArray(x.historia) && x.historia.length >= 3 && x.historia.every(s => txt(s, 150)), '.historia debe tener al menos 3 párrafos de 150 caracteres o más');
      cp(txt(x.impacto, 150), '.impacto es muy corto');
      cp(lista(x.claves, 3, 8), '.claves debe tener al menos 3 fechas o datos');
      cp(txt(x.ensenanza, 60), '.ensenanza es muy corta');
      const largo = [x.resumen, x.impacto, x.ensenanza].concat(Array.isArray(x.historia) ? x.historia : []).filter(s => typeof s === 'string').join(' ').length;
      cp(largo >= 1500, ': la reseña es muy corta (' + largo + ' caracteres; mínimo 1500): cuéntala con detalle');
      cp(largo <= 4500, ': la reseña es demasiado larga (' + largo + ' caracteres; máximo 4500)');
      if (k === 'hecho' || 'estado' in x) cp(txt(x.estado, 40), '.estado falta: di qué dice la Iglesia (reconocimiento oficial)');
      if ('frase' in x) {
        const fr = x.frase || {};
        cp(txt(fr.texto, 10) && txt(fr.fuente, 3), '.frase incompleta (texto y fuente); si no hay frase verificada, omítela');
        if (txt(fr.texto)) cp(!/[«»]/.test(fr.texto), '.frase.texto no lleva « »');
      }
      if ('fiesta' in x) cp(txt(x.fiesta, 3), '.fiesta está vacío (omítelo si no aplica)');
      cp(Array.isArray(x.fuentes) && x.fuentes.length >= 1 && x.fuentes.every(f => f && txt(f.n, 2) && /^https:\/\/\S+$/.test(f.url || '')), '.fuentes: al menos una {n,url} con un enlace https que hayas visto');
      if (txt(x.nombre)) {
        const rep = usados.find(t => llano(t[k]) === llano(x.nombre));
        cp(!rep, ': «' + x.nombre + '» ya salió el ' + (rep && rep.fecha) + '; elige otro (mira «node tareas/dias.js temas»)');
      }
    }
    if (C.persona && C.hecho && txt(C.persona.nombre) && txt(C.hecho.nombre)) pide(llano(C.persona.nombre) !== llano(C.hecho.nombre), 'conoce: la persona y el hecho no pueden ser lo mismo');
  }
  return E;
}
function validar(archivo, fechaEsperada) {
  let codigo;
  try { codigo = fs.readFileSync(archivo, 'utf8'); } catch (e) { return ['no se puede leer: ' + e.message]; }
  return validarCodigo(codigo, fechaEsperada);
}

const erroresDia = f => fs.existsSync(rutaDia(f)) ? validar(rutaDia(f), f) : null;
const diaBien = f => { const E = erroresDia(f); return !!E && E.length === 0; };
/* 'completo' | 'sin-conoce' (Evangelio y Misa bien; falta o falla solo «Conoce tu Iglesia») | 'mal' | 'falta' */
const nivel = f => { const E = erroresDia(f); if (E === null) return 'falta'; if (!E.length) return 'completo'; return E.every(e => /^conoce/.test(e)) ? 'sin-conoce' : 'mal'; };
/* [{fecha, que:'nuevo'|'completar'|'rehacer', errores}] */
function faltan(hoy, n) {
  const out = [];
  for (let i = 0; i <= n; i++) {
    const f = suma(hoy, i), E = erroresDia(f);
    if (E === null) out.push({ fecha: f, que: 'nuevo', errores: [] });
    else if (E.length) out.push({ fecha: f, que: E.every(e => /^conoce/.test(e)) ? 'completar' : 'rehacer', errores: E });
  }
  return out;
}
function fechaHoyJs() {
  try { const H = evaluar(fs.readFileSync(path.join(RAIZ, 'hoy.js'), 'utf8')).HOY; return (H && H.fecha) || '(sin fecha)'; } catch (e) { return '(no se puede leer)'; }
}
function leerJSON(archivo) {
  let t;
  try { t = fs.readFileSync(path.resolve(archivo), 'utf8'); } catch (e) { console.log('NO SE PUEDE LEER ' + archivo + ': ' + e.message); process.exit(1); }
  try { const o = JSON.parse(t); if (!o || typeof o !== 'object' || Array.isArray(o)) throw new Error('debe ser un objeto { … }'); return o; }
  catch (e) { console.log('JSON NO VÁLIDO en ' + archivo + ': ' + e.message); process.exit(1); }
}
function guardar(fecha, H) {
  const codigo = serializar(H), E = validarCodigo(codigo, fecha);
  if (E.length) { console.log('NO VÁLIDO ' + fecha + ' (no se guardó nada):\n- ' + E.join('\n- ')); process.exit(1); }
  fs.mkdirSync(DIAS, { recursive: true });
  fs.writeFileSync(rutaDia(fecha), codigo);
  console.log('OK dias/' + fecha + '.js · ' + H.titulo + ' · ' + H.evangelio.cita + ' · persona: ' + H.conoce.persona.nombre + ' · hecho: ' + H.conoce.hecho.nombre);
}

const [, , cmd, a, b] = process.argv;
function uso(msg) {
  if (msg) console.error(msg);
  console.error('Uso: node tareas/dias.js estado|faltan|hoy AAAA-MM-DD [n] · escribir|completar FECHA archivo.json · validar dias/FECHA.js · temas');
  process.exit(2);
}

if (cmd === 'validar') {
  if (!a) uso();
  const archivo = path.resolve(a), nombre = path.basename(archivo, '.js');
  if (!esFecha(nombre)) uso('El archivo debe llamarse AAAA-MM-DD.js');
  const E = validar(archivo, nombre);
  if (E.length) { console.log('NO VÁLIDO ' + nombre + ':\n- ' + E.join('\n- ')); process.exit(1); }
  const H = evaluar(fs.readFileSync(archivo, 'utf8')).HOY;
  console.log('OK ' + nombre + ' · ' + H.titulo + ' · ' + H.evangelio.cita + ' · persona: ' + H.conoce.persona.nombre + ' · hecho: ' + H.conoce.hecho.nombre);
} else if (cmd === 'escribir') {
  if (!esFecha(a) || !b) uso('Uso: node tareas/dias.js escribir FECHA archivo.json');
  const H = leerJSON(b);
  if (!H.fecha) H.fecha = a;
  if (!H.actualizado) H.actualizado = hoyCaracas();
  guardar(a, H);
} else if (cmd === 'completar') {
  if (!esFecha(a) || !b) uso('Uso: node tareas/dias.js completar FECHA archivo.json');
  if (!fs.existsSync(rutaDia(a))) { console.log('FALTA dias/' + a + '.js: usa «escribir» con el día completo'); process.exit(1); }
  let H;
  try { H = evaluar(fs.readFileSync(rutaDia(a), 'utf8')).HOY; } catch (e) { H = null; }
  if (!H || typeof H !== 'object') { console.log('dias/' + a + '.js no se puede leer: usa «escribir» con el día completo'); process.exit(1); }
  const extra = leerJSON(b);
  if ('fecha' in extra && extra.fecha !== a) { console.log('El JSON es de otra fecha (' + extra.fecha + ')'); process.exit(1); }
  guardar(a, Object.assign({}, H, extra));
} else if (cmd === 'temas') {
  const T = temas().filter(t => t.persona || t.hecho);
  console.log(T.length ? T.map(t => t.fecha + ' | persona: ' + t.persona + ' | hecho: ' + t.hecho).join('\n') : 'NINGUNO');
} else if (cmd === 'faltan') {
  if (!esFecha(a)) uso('Falta la fecha de hoy (AAAA-MM-DD)');
  const n = b === undefined ? 7 : Math.max(0, Math.min(30, parseInt(b, 10) || 0));
  const F = faltan(a, n);
  const nota = { nuevo: 'NUEVO: no existe; prepara el día completo y usa «escribir»', completar: 'COMPLETAR: ya existe y solo le falta o le falla la sección conoce; usa «completar»', rehacer: 'REHACER: existe pero tiene errores; corrígelo con «completar» o «escribir»' };
  console.log(F.length ? F.map(x => x.fecha + '  ' + nota[x.que] + (x.que === 'rehacer' ? '\n   - ' + x.errores.slice(0, 6).join('\n   - ') : '')).join('\n') : 'NADA');
} else if (cmd === 'hoy') {
  if (!esFecha(a)) uso('Falta la fecha de hoy (AAAA-MM-DD)');
  const origen = rutaDia(a);
  if (!fs.existsSync(origen)) { console.log('FALTA dias/' + a + '.js: no se cambió hoy.js'); process.exit(1); }
  const E = validar(origen, a), nv = nivel(a);
  if (nv === 'mal') { console.log('NO VÁLIDO dias/' + a + '.js: no se cambió hoy.js\n- ' + E.join('\n- ')); process.exit(1); }
  const destino = path.join(RAIZ, 'hoy.js');
  const nuevo = fs.readFileSync(origen);
  const aviso = nv === 'sin-conoce' ? ' (AVISO: al día de hoy le falta la sección conoce)' : '';
  if (fs.existsSync(destino) && fs.readFileSync(destino).equals(nuevo)) console.log('IGUAL hoy.js ya es el del ' + a + aviso);
  else { fs.writeFileSync(destino, nuevo); console.log('COPIADO dias/' + a + '.js → hoy.js' + aviso); }
} else if (cmd === 'estado') {
  if (!esFecha(a)) uso('Falta la fecha de hoy (AAAA-MM-DD)');
  const fh = fechaHoyJs();
  console.log('hoy.js: ' + fh + (fh === a ? ' (al día)' : ' (VIEJO)'));
  const nv = nivel(a);
  console.log('día de hoy (dias/' + a + '.js): ' + ({ completo: 'listo', 'sin-conoce': 'listo, pero le falta la sección conoce', mal: 'TIENE ERRORES', falta: 'FALTA' })[nv]);
  let seguidos = 0; while (seguidos < 60 && diaBien(suma(a, seguidos + 1))) seguidos++;
  console.log('días completos por delante (seguidos): ' + seguidos + (seguidos ? ' (hasta ' + suma(a, seguidos) + ')' : ''));
  const F = faltan(a, 7);
  console.log('por preparar en la ventana de 7 días: ' + (F.length ? F.map(x => x.fecha + ' (' + x.que + ')').join(', ') : 'ninguno'));
} else uso();
