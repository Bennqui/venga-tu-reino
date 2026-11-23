/* Revisión automática de los días preparados (dias/AAAA-MM-DD.js) contra el calendario de la app.
   Compara color y celebración, y revisa que el texto esté en español de América y que el día sea válido.
   Uso: node tareas/revisar-dias.js [desde AAAA-MM-DD] [n días]   (por defecto: hoy y los 7 siguientes) */
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const T = require('./calendario-app.js');
const raiz = path.join(__dirname, '..');
const pad = n => String(n).padStart(2, '0'), ymd = d => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
const desde = process.argv[2] ? new Date(process.argv[2] + 'T12:00:00') : new Date(), n = +(process.argv[3] || 8);
const sinT = s => (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
let avisos = 0, revisados = 0;
for (let i = 0; i < n; i++) {
  const d = new Date(desde); d.setDate(d.getDate() + i);
  const f = ymd(d), arch = path.join(raiz, 'dias', f + '.js');
  if (!fs.existsSync(arch)) { console.log('·', f, 'sin preparar'); continue; }
  revisados++;
  const P = [];
  try { execFileSync('node', [path.join(__dirname, 'dias.js'), 'validar', arch], { stdio: 'pipe' }); }
  catch (e) { P.push('no pasa la validación: ' + String(e.stdout || e.message).trim().split('\n').slice(0, 3).join(' | ')); }
  let H = null;
  try { H = JSON.parse(fs.readFileSync(arch, 'utf8').replace(/^\s*window\.HOY\s*=\s*/, '').replace(/;\s*$/, '')); } catch (e) { P.push('no se puede leer'); }
  if (H && H.misa) {
    const L = T.liturgia(d), S = T.santoDia(d, L);
    const color = (S && S.color) || L.color, tit = (S && S.n) || L.titulo;
    /* el color del día preparado puede ser más preciso (memoria libre elegida); se avisa solo si cambia el tiempo litúrgico */
    const fuerte = c => ['morado', 'rosa', 'rojo', 'blanco', 'verde'].indexOf(c);
    if (H.misa.color !== color) {
      const libre = /libre/i.test(H.misa.rango || '') || (H.misa.rango === 'Memoria' && L.color === 'verde');
      if (!libre) P.push('color ' + H.misa.color + ' en el día preparado, ' + color + ' según el calendario de la app (' + tit + ')');
    }
    if (d.getDay() === 0 && !/domingo|solemnidad|adviento|cuaresma|pascua|ramos|pentecost|trinidad|corpus|rey|familia|bautismo|epifan/i.test(sinT(H.titulo + ' ' + H.misa.celebracion)))
      P.push('es domingo y la celebración no lo dice: ' + H.misa.celebracion);
  }
  if (P.length) { avisos += P.length; console.log('✗', f, '\n   - ' + P.join('\n   - ')); }
  else console.log('✓', f, '·', H.misa.celebracion, '·', H.misa.color);
}
console.log(avisos ? avisos + ' cosas por revisar en ' + revisados + ' días' : 'Todo en orden: ' + revisados + ' días revisados');
process.exit(avisos ? 1 : 0);
