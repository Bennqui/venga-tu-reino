#!/usr/bin/env node
/* Venga tu Reino — utilidades para los días preparados por adelantado (carpeta dias/).

   node tareas/dias.js estado  AAAA-MM-DD          resumen: hoy.js, día de hoy y hasta qué fecha hay días preparados
   node tareas/dias.js faltan  AAAA-MM-DD [n]      fechas que faltan (o están mal) desde hoy hasta hoy+n (n = 7 por defecto)
   node tareas/dias.js validar dias/AAAA-MM-DD.js  revisa que el archivo de un día esté completo y bien formado
   node tareas/dias.js hoy     AAAA-MM-DD          copia dias/AAAA-MM-DD.js a hoy.js (solo si es válido)

   AAAA-MM-DD es siempre la fecha de HOY en Venezuela (America/Caracas). */
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

function leer(archivo) {
  const codigo = fs.readFileSync(archivo, 'utf8');
  const caja = { window: {} };
  vm.runInNewContext(codigo, caja, { timeout: 2000 });
  return { codigo, HOY: caja.window.HOY, extra: Object.keys(caja.window).filter(k => k !== 'HOY') };
}

const RANGOS = ['Solemnidad', 'Fiesta', 'Memoria', 'Memoria libre', 'Feria', 'Domingo'];
const COLORES = ['verde', 'morado', 'blanco', 'rojo', 'rosa'];
const TIPOS = ['Primera lectura', 'Salmo responsorial', 'Segunda lectura', 'Evangelio'];
const RELATOS = ['Parábola', 'Milagro', 'Enseñanza', 'Encuentro', 'Escena'];

/* Devuelve la lista de errores de un archivo de día (vacía si está bien). */
function validar(archivo, fechaEsperada) {
  const E = [];
  let r;
  try { r = leer(archivo); } catch (e) { return ['no se puede leer o tiene un error de JavaScript: ' + e.message]; }
  const H = r.HOY;
  if (!/^\s*window\.HOY\s*=\s*\{/.test(r.codigo)) E.push('el archivo debe empezar con window.HOY={');
  if (r.extra.length) E.push('solo debe definir window.HOY (sobra: ' + r.extra.join(', ') + ')');
  if (!H || typeof H !== 'object') return E.concat('no define window.HOY');
  if (/AAAA-MM-DD/.test(r.codigo)) E.push('quedó el texto de plantilla AAAA-MM-DD');

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
  return E;
}

function preparados() {
  if (!fs.existsSync(DIAS)) return [];
  return fs.readdirSync(DIAS).filter(f => /^\d{4}-\d{2}-\d{2}\.js$/.test(f)).map(f => f.slice(0, 10)).sort();
}
const diaBien = f => fs.existsSync(rutaDia(f)) && validar(rutaDia(f), f).length === 0;
function faltan(hoy, n) {
  const out = [];
  for (let i = 0; i <= n; i++) { const f = suma(hoy, i); if (!diaBien(f)) out.push(f); }
  return out;
}
function fechaHoyJs() {
  try { const H = leer(path.join(RAIZ, 'hoy.js')).HOY; return (H && H.fecha) || '(sin fecha)'; } catch (e) { return '(no se puede leer)'; }
}

const [, , cmd, a, b] = process.argv;
function uso(msg) { if (msg) console.error(msg); console.error('Uso: node tareas/dias.js estado|faltan|hoy AAAA-MM-DD [n]  ·  node tareas/dias.js validar dias/AAAA-MM-DD.js'); process.exit(2); }

if (cmd === 'validar') {
  if (!a) uso();
  const archivo = path.resolve(a), nombre = path.basename(archivo, '.js');
  if (!esFecha(nombre)) uso('El archivo debe llamarse AAAA-MM-DD.js');
  const E = validar(archivo, nombre);
  if (E.length) { console.log('NO VÁLIDO ' + nombre + ':\n- ' + E.join('\n- ')); process.exit(1); }
  const H = leer(archivo).HOY;
  console.log('OK ' + nombre + ' · ' + H.titulo + ' · ' + H.evangelio.cita);
} else if (cmd === 'faltan') {
  if (!esFecha(a)) uso('Falta la fecha de hoy (AAAA-MM-DD)');
  const n = b === undefined ? 7 : Math.max(0, Math.min(30, parseInt(b, 10) || 0));
  const F = faltan(a, n);
  console.log(F.length ? F.join('\n') : 'NADA');
} else if (cmd === 'hoy') {
  if (!esFecha(a)) uso('Falta la fecha de hoy (AAAA-MM-DD)');
  const origen = rutaDia(a);
  if (!fs.existsSync(origen)) { console.log('FALTA dias/' + a + '.js: no se cambió hoy.js'); process.exit(1); }
  const E = validar(origen, a);
  if (E.length) { console.log('NO VÁLIDO dias/' + a + '.js: no se cambió hoy.js\n- ' + E.join('\n- ')); process.exit(1); }
  const destino = path.join(RAIZ, 'hoy.js');
  const nuevo = fs.readFileSync(origen);
  if (fs.existsSync(destino) && fs.readFileSync(destino).equals(nuevo)) console.log('IGUAL hoy.js ya es el del ' + a);
  else { fs.writeFileSync(destino, nuevo); console.log('COPIADO dias/' + a + '.js → hoy.js'); }
} else if (cmd === 'estado') {
  if (!esFecha(a)) uso('Falta la fecha de hoy (AAAA-MM-DD)');
  const fh = fechaHoyJs();
  console.log('hoy.js: ' + fh + (fh === a ? ' (al día)' : ' (VIEJO)'));
  console.log('día de hoy (dias/' + a + '.js): ' + (diaBien(a) ? 'listo' : 'FALTA'));
  let seguidos = 0; while (seguidos < 60 && diaBien(suma(a, seguidos + 1))) seguidos++;
  console.log('días preparados por delante (seguidos): ' + seguidos + (seguidos ? ' (hasta ' + suma(a, seguidos) + ')' : ''));
  const F = faltan(a, 7);
  console.log('faltan en la ventana de 7 días: ' + (F.length ? F.join(', ') : 'ninguno'));
  const malos = preparados().filter(f => f >= a && validar(rutaDia(f), f).length);
  if (malos.length) console.log('con errores: ' + malos.join(', '));
} else uso();
