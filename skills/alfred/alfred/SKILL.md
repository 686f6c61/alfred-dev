---
name: alfred
description: "Alias global /alfred para abrir el asistente contextual de Alfred Dev sin escribir el namespace completo. Activar solo cuando el usuario invoque explicitamente /alfred."
disable-model-invocation: true
user-invocable: false
---

# /alfred

Marcador de instalacion: Alfred Dev global alias.

Este skill existe para que el usuario pueda escribir `/alfred` en Claude Code.
No crea una segunda familia de comandos ni sustituye el namespace tecnico
`alfred-dev`: el resto de acciones siguen viviendo en `/alfred-dev:*`.
Internamente reutiliza `commands/alfred.md` como contrato del asistente
contextual, pero ese Markdown no se registra como slash command publico del
plugin. Este fichero fuente queda oculto cuando se carga desde el plugin para
no duplicar `/alfred` en el selector. El instalador copia este mismo fichero a
`~/.claude/skills/alfred/SKILL.md` cambiando `user-invocable` a `true`, y
elimina el shim personal obsoleto `~/.claude/commands/alfred.md` si existe,
para que `/alfred` aparezca como una sola entrada global personal en cualquier
proyecto y también responda en `claude -p`.

## Protocolo

1. Trata la invocacion como la entrada contextual principal de Alfred Dev con
   los mismos argumentos del usuario.
2. Lee y sigue el contrato canonico en `${CLAUDE_PLUGIN_ROOT}/commands/alfred.md`
   cuando esa ruta exista.
   Si este skill esta cargado como alias personal desde `~/.claude/skills` y
   `CLAUDE_PLUGIN_ROOT` no esta disponible, localiza el plugin instalado en
   `~/.claude/plugins/cache/alfred-dev/` y lee el `commands/alfred.md` de la
   version activa o mas reciente. En desarrollo local, si estas dentro del
   repositorio, usa `commands/alfred.md` del repo actual.
   Si no puedes localizar el contrato, informa de que el alias global existe
   pero el plugin instalado no esta disponible, y pide reinstalar con
   `install.sh`/`install.ps1` o ejecutar `/alfred-dev:update`.
3. Si el helper de continuidad devuelve `command: "alfred"` o recomienda
   `/alfred-dev:alfred`, no vuelvas a redirigir a `/alfred` ni a
   `/alfred-dev:alfred`. Esa senal solo significa que no hay un flujo concreto
   decidido todavia. Clasifica la peticion del usuario y elige un comando
   operativo concreto; para "que toca ahora" o continuidad usa
   `/alfred-dev:next`.
4. En la respuesta final deja claro el comando real ejecutado o simulado y por
   que esa ruta era la correcta.

## Restricciones

- No presentes `/alfred-dev:alfred` como comando publico disponible.
- No inventes resultados de helpers, tests, agentes o MCP sin salida de
  herramienta, artefacto persistido o confirmacion explicita del usuario.
- No conviertas este alias en una lista de comandos; solo enruta igual que
  `/alfred-dev:alfred`.
