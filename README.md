# Venga tu Reino

App católica para seguir la Misa, rezar el Rosario y orar con el Evangelio del día. Funciona sin conexión (agrégala a la pantalla de inicio desde Safari).

## Cómo se actualiza sola

- `dias/AAAA-MM-DD.js`: un archivo por fecha, preparado **por adelantado** (una semana completa), con el Evangelio, la Misa, el Encuentro y «Conoce tu Iglesia» (una persona y un hecho de la historia de la Iglesia). La app carga el de la fecha del teléfono, así que cambia de día sola a medianoche, y guarda los próximos días para usarlos sin internet.
- `hoy.js`: copia del día de hoy (respaldo).
- `dias/linea.json`: índice que se rehace solo con cada día nuevo; alimenta la línea del tiempo de «Personas y hechos» y la línea de estado de la app.
- Una tarea programada de Claude corre cada medianoche **en la nube** (no necesita ninguna computadora encendida): prepara los días que falten y los sube aquí. Otra tarea, el «Vigilante», revisa de madrugada y avisa si algo falló.
- `tareas/GUIA.md` explica cómo se escribe cada día y `tareas/dias.js` lo valida.
- Lecturas y Evangelio: desde nov 2026 la app no muestra el texto bíblico dentro; abre Vatican News (lecturas del día) y vatican.va (misterios del Rosario). La carpeta `biblia/` (Straubinger) queda en el repositorio sin usarse, por si se quiere volver atrás.
- Orar › Adoración: guía de Hora Santa con enlaces a las Letanías al Santísimo y otras oraciones eucarísticas (ACI Prensa).
- Pruebas: `node tareas/prueba-calendario.js` (40 fechas clave, ciclos y misterios del Rosario) y `node tareas/revisar-dias.js` (los días preparados contra el calendario y en español de América). Corren solas en GitHub con cada cambio.
- Ideas tomadas de Hallow (nov 2026): «Silencio con Dios» (Orar › Más), temporizador de oración en silencio con campana suave hecha en el teléfono, también dentro del Evangelio del paso a paso y en Adoración; y la oración con el Evangelio en versión Breve (5 min) o Completa (15 min). Para volver a la versión anterior existe la rama `antes-hallow`.
- Diseño inspirado en Hallow (nov 2026): tarjetas con pinturas en «Para tu día» (carrusel) y en Orar › Más; pantalla de inicio de la oración con la pintura, la cita y Breve/Completa; «Escuchar» abre un reproductor a pantalla completa (pausa, avance, detener); racha con número grande. Versión anterior a estos cambios: rama `antes-hallow-2`.
