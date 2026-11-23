# Venga tu Reino

App católica para seguir la Misa, rezar el Rosario y orar con el Evangelio del día. Funciona sin conexión (agrégala a la pantalla de inicio desde Safari).

## Cómo se actualiza sola

- `dias/AAAA-MM-DD.js`: un archivo por fecha, preparado **por adelantado** (una semana completa), con el Evangelio, la Misa, el Encuentro y «Conoce tu Iglesia» (una persona y un hecho de la historia de la Iglesia). La app carga el de la fecha del teléfono, así que cambia de día sola a medianoche, y guarda los próximos días para usarlos sin internet.
- `hoy.js`: copia del día de hoy (respaldo).
- `dias/linea.json`: índice que se rehace solo con cada día nuevo; alimenta la línea del tiempo de «Personas y hechos» y la línea de estado de la app.
- Una tarea programada de Claude corre cada medianoche **en la nube** (no necesita ninguna computadora encendida): prepara los días que falten y los sube aquí. Otra tarea, el «Vigilante», revisa de madrugada y avisa si algo falló.
- `tareas/GUIA.md` explica cómo se escribe cada día y `tareas/dias.js` lo valida.
- `biblia/`: la Biblia que usa «Leer la lectura completa»: versión católica de Mons. Juan Straubinger (Biblia Platense, dominio público), 73 libros, salmos con la numeración de la Vulgata, «el Señor» en lugar de «Yahvé» y español actual de América («ustedes» en lugar de «vosotros», `tareas/moderno.py`). Junto a cada lectura, el botón «Leer como en la Misa de hoy» abre el texto oficial del Leccionario (Conferencia del Episcopado Mexicano, el mismo del Misal de Venezuela) en la página de los obispos de EE. UU. La genera `tareas/biblia.py` (workflow «Biblia católica de dominio público»).
- Pruebas: `node tareas/prueba-calendario.js` (40 fechas clave, ciclos y misterios del Rosario) y `node tareas/revisar-dias.js` (los días preparados contra el calendario y en español de América). Corren solas en GitHub con cada cambio.
