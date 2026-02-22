---
name: gui
description: Abre el dashboard GUI de Alfred Dev en el navegador
arguments:
  - name: accion
    description: "Accion a realizar: open (defecto), status, stop"
    required: false
---

Gestiona el dashboard GUI de Alfred Dev.

## Acciones

- **open** (defecto): abre el dashboard en el navegador. Si el servidor no esta arrancado, lo indica.
- **status**: muestra el estado del servidor GUI (puerto, PID, conexiones).
- **stop**: para el servidor GUI manualmente.

## Instrucciones

1. Leer el fichero `.claude/alfred-gui-port` para obtener los puertos activos.
2. Si la accion es `open` (o no se especifica accion):
   - Si el fichero existe y el puerto esta activo, abrir `http://127.0.0.1:{http_port}` en el navegador con `open` (macOS) o `xdg-open` (Linux).
   - Si no existe, informar de que el servidor no esta arrancado (se levanta automaticamente al iniciar sesion si hay memoria activa).
3. Si la accion es `status`:
   - Leer el PID de `.claude/alfred-gui.pid` y verificar que el proceso esta activo.
   - Mostrar los puertos HTTP y WebSocket.
4. Si la accion es `stop`:
   - Leer el PID y enviar SIGTERM.
   - Confirmar la parada.
