---
description: "Comprueba y aplica actualizaciones del plugin Alfred Dev"
---

# /alfred-dev:update

Eres Alfred. El usuario quiere comprobar si hay una version nueva del plugin. Sigue estos pasos al pie de la letra.

## Paso 1: obtener la version instalada y el scope

Primero usa la CLI nativa de Claude Code, porque es la fuente autoritativa de
instalaciones activas, scopes e installPath:

```bash
claude plugin list --json
```

Busca la entrada `alfred-dev@alfred-dev`. Si hay varias, prioriza:

1. una entrada `enabled: true` cuyo `projectPath`, si existe, coincide con el
   proyecto actual;
2. una entrada `enabled: true` sin `projectPath` (instalación `user`);
3. cualquier entrada `alfred-dev@alfred-dev` como último recurso.

Extrae:

- `version`
- `scope` (`user`, `local`, `project` o `managed`)
- `installPath`
- `projectPath` si existe

Si `claude plugin list --json` falla o no devuelve la entrada, usa este fallback
de cache para la version y marca el scope como `desconocido`:

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

El fallback selecciona la version mas reciente por fecha de modificacion para
evitar errores cuando coexistan varias versiones en cache, pero no lo uses para
decidir scope si la CLI sí ha devuelto uno.

## Paso 2: consultar la ultima release en GitHub

Ejecuta con Bash:

```bash
curl -s --max-time 10 "https://api.github.com/repos/686f6c61/alfred-dev/releases/latest"
```

Extrae del JSON: `tag_name` (version), `name` (titulo), `body` (notas de la release), `published_at` (fecha).

Si la peticion falla (sin red, rate limit, timeout), informa del error y sugiere reintentarlo mas tarde. No sigas adelante. En concreto:

- Si el JSON contiene `"message": "API rate limit exceeded"`, informa al usuario de que ha superado el limite de peticiones de GitHub y que puede reintentar en unos minutos o pasar un token con `-H "Authorization: token ..."`.
- Si curl devuelve un codigo de error o timeout, muestra el error y sugiere comprobar la conexion.
- Si el JSON no contiene `tag_name`, es una respuesta inesperada. Muestra el contenido raw y aborta.

## Paso 3: comparar versiones

Valida que `tag_name` tiene formato semver valido: debe coincidir con el patron `v?X.Y.Z` donde X, Y, Z son numeros (por ejemplo `v0.3.0` o `0.3.0`). Si no coincide, muestra un aviso y aborta: el formato de la release no es el esperado.

Normaliza `tag_name` (sin la `v` inicial) y la version instalada a tuplas
numericas `(major, minor, patch)` y comparalas como semver real. **Nunca**
compares las versiones como texto plano (`0.10.0` es mayor que `0.9.0`).

Si necesitas una comparacion determinista, ejecuta con Bash:

```bash
python3 - <<'PY'
def parse(value):
    return tuple(int(part) for part in value.strip().lstrip('v').split('.'))

installed = "VERSION_INSTALADA"
latest = "TAG_NAME"

print(parse(latest) > parse(installed))
PY
```

Sustituye `VERSION_INSTALADA` y `TAG_NAME` por los valores reales del paso 1 y 2.

### Si hay version nueva

Muestra al usuario:
- La version actual instalada
- La version nueva disponible
- Las notas de la release formateadas en markdown

Despues usa **un único `AskUserQuestion`** con menú seleccionable real. No
dejes la decisión en texto libre. Las dos opciones deben ser:
- **"Actualizar ahora"** -- ejecuta el comando de instalacion (paso 4)
- **"Ahora no"** -- cancela

### Si esta al dia

Informa de que no hay actualizaciones disponibles y muestra la version actual. Fin.

## Paso 4: ejecutar la actualizacion

Si el usuario acepta, usa siempre la ruta global de usuario salvo que el scope
sea `managed`. Alfred Dev no conserva instalaciones `local` ni `project` al
actualizar desde este comando: las normaliza a `--scope user` para que `/alfred`
y `/alfred-dev:*` funcionen en cualquier proyecto del usuario.

### Scope user, local, project o desconocido

Para instalaciones de usuario, locales, de proyecto o con scope desconocido,
usa el instalador soportado de Alfred Dev. Esta ruta vuelve a registrar la
fuente GitHub con `--scope user`, reinstala mediante la CLI nativa de Claude
Code, rematerializa el alias personal global `/alfred` en
`~/.claude/skills/alfred/SKILL.md`, elimina el shim personal obsoleto
`~/.claude/commands/alfred.md` si existe y vuelve a aplicar el parche de Python compatible
en `hooks.json` y `.mcp.json` cuando hace falta.

Si el scope detectado era `local` o `project`, dilo antes de ejecutar: la
actualización convertirá esa instalación en una instalación global de usuario.
No uses `claude plugin update --scope local` ni `claude plugin update --scope project`.

Primero detecta la plataforma y despues ejecuta el instalador correspondiente.

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

### Scope managed

Si el scope detectado es `managed`, no intentes actualizarlo. Explica que las
instalaciones managed las controla la política del administrador y que el
usuario debe pedir la actualización a quien gestione Claude Code en su equipo.

Despues de que termine cualquier actualización, informa al usuario de que debe
ejecutar **`/reload-plugins`** en Claude Code para cargar la nueva versión en la
sesión actual. Si Claude Code avisa por MCP/caché, si decide no usar
`/reload-plugins --force` o si el inventario no cambia, entonces debe reiniciar
Claude Code.

## Notas

- Los instaladores son idempotentes: sobreescriben la instalacion anterior sin conflictos.
- No hace falta desinstalar primero en scope `user`.
- En scope `local` o `project`, no conserves el scope: convierte a instalacion
  global de usuario con el instalador para que el alias personal global
  `/alfred` exista en cualquier proyecto como skill personal invocable y para
  que cualquier shim personal de comando heredado se elimine o respalde.
- Si el script de instalacion falla, muestra el error completo al usuario.
- En Windows tambien funciona con WSL o Git Bash usando el instalador bash.

## Cierre canónico del comando

- Si no hay versión nueva, cierra ahí: no propongas pasos extra ni una decisión ficticia.
- Si sí hay versión nueva, usa un único menú seleccionable real con las dos opciones definidas arriba y no lo sustituyas por texto libre.
- Si la actualización se ejecuta bien, el cierre debe ser corto y accionable: versión aplicada, ejecutar `/reload-plugins` y reiniciar solo si MCP/caché lo exige o el inventario no cambia.
