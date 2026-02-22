---
description: "Comprueba y aplica actualizaciones del plugin Alfred Dev"
---

# Actualizar Alfred Dev

Eres Alfred. El usuario quiere comprobar si hay una version nueva del plugin. Sigue estos pasos al pie de la letra.

## Paso 1: obtener la version instalada

Ejecuta con Bash:

```bash
python3 -c "
import json, os, glob, sys

candidates = sorted(
    glob.glob(os.path.expanduser('~/.claude/plugins/cache/alfred-dev/**/.claude-plugin/plugin.json'), recursive=True),
    key=os.path.getmtime,
    reverse=True
)
if not candidates:
    print('desconocida')
    sys.exit(0)
with open(candidates[0]) as f:
    print(json.load(f).get('version', 'desconocida'))
" 2>/dev/null || echo "desconocida"
```

Si no se puede leer, busca la version en el fichero `plugin.json` mas cercano dentro de `~/.claude/plugins/cache/alfred-dev/`. El script selecciona la version mas reciente por fecha de modificacion para evitar errores cuando coexistan varias versiones en cache.

## Paso 2: consultar la ultima release en GitHub

Ejecuta con Bash:

```bash
curl -s --max-time 10 "https://api.github.com/repos/686f6c61/alfred-dev/releases/latest"
```

Extrae del JSON: `tag_name` (version), `name` (titulo), `body` (notas de la release), `published_at` (fecha).

Si la peticion falla (sin red, rate limit, timeout), informa del error y sugiere reintentarlo mas tarde. No sigas adelante.

## Paso 3: comparar versiones

Compara `tag_name` (sin la `v` inicial) con la version instalada del paso 1.

### Si hay version nueva

Muestra al usuario:
- La version actual instalada
- La version nueva disponible
- Las notas de la release formateadas en markdown

Pregunta al usuario si quiere actualizar usando AskUserQuestion con las opciones:
- **"Actualizar ahora"** -- ejecuta el comando de instalacion (paso 4)
- **"Ahora no"** -- cancela

### Si esta al dia

Informa de que no hay actualizaciones disponibles y muestra la version actual. Fin.

## Paso 4: ejecutar la actualizacion

Si el usuario acepta, primero detecta la plataforma y despues ejecuta el instalador correspondiente.

### Deteccion de plataforma

Ejecuta con Bash:

```bash
uname -s 2>/dev/null || echo "Windows"
```

- Si devuelve `Darwin` o `Linux`: es macOS o Linux, usa el instalador bash.
- Si falla o devuelve `Windows` / `MINGW` / `MSYS` / `CYGWIN`: es Windows, usa el instalador PowerShell.

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex
```

Despues de que termine, informa al usuario de que **debe reiniciar Claude Code** (cerrar y volver a abrir) para que los cambios surtan efecto. Los plugins se cargan al inicio de sesion.

## Notas

- Los instaladores son idempotentes: sobreescriben la instalacion anterior sin conflictos.
- No hace falta desinstalar primero.
- Si el script de instalacion falla, muestra el error completo al usuario.
- En Windows tambien funciona con WSL o Git Bash usando el instalador bash.
