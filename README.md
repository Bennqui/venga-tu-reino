# Venga tu Reino

App católica para seguir la Misa, rezar el Rosario y orar con el Evangelio del día. Funciona sin conexión (agrégala a la pantalla de inicio desde Safari).

## Cómo se actualiza sola

- `dias/AAAA-MM-DD.js`: un archivo por fecha, preparado **por adelantado** (una semana completa), con el Evangelio, la Misa, el Encuentro y «Conoce tu Iglesia» (una persona y un hecho de la historia de la Iglesia). La app carga el de la fecha del teléfono, así que cambia de día sola a medianoche, y guarda los próximos días para usarlos sin internet.
- `hoy.js`: copia del día de hoy (respaldo).
- Una tarea programada de Claude corre cada medianoche **en la nube** (no necesita ninguna computadora encendida): prepara los días que falten y los sube aquí. Otra tarea, el «Vigilante», revisa de madrugada y avisa si algo falló.
- `tareas/GUIA.md` explica cómo se escribe cada día y `tareas/dias.js` lo valida.
