# Instalación y cadena de carga

Alfred Dev ya no instala el plugin copiando repositorios ni editando a mano los
JSON internos de Claude Code. El flujo actual delega la instalación en la CLI
nativa de Claude Code y solo añade una capa de verificación y parcheo donde el
plugin lo necesita de verdad: detección de Python 3.10+ y ajuste de `hooks.json`
y de `.mcp.json` cuando `python3` del sistema no es compatible. Además
materializa el alias corto `/alfred` como skill personal global invocable en
`~/.claude/skills/alfred/SKILL.md` y elimina el shim personal obsoleto
`~/.claude/commands/alfred.md` si existe, porque los skills empaquetados en un plugin se
cargan con namespace (`/alfred-dev:*`) y el comando corto debe existir fuera del
paquete.

Esto importa porque la cadena de carga sigue existiendo, pero el responsable de
materializarla ya no es un script artesanal del plugin, sino `claude plugin
marketplace add` y `claude plugin install`. Los instaladores de Alfred Dev se
limitan a dejar el entorno listo, pedir a Claude Code que registre globalmente
la fuente GitHub del plugin e instalar la versión nueva.

Importante: aquí `marketplace` es el nombre del subcomando de Claude Code, no
una tienda oficial de plugins. Alfred Dev es un plugin independiente y no oficial.
No usa un marketplace oficial de Anthropic; registra una fuente GitHub propia
con la CLI nativa de Claude Code.
La orden:

```bash
claude plugin marketplace add 686f6c61/alfred-dev --scope user
```

le dice a Claude Code que registre una **fuente GitHub propia** en
`known_marketplaces.json`, de forma global para ese usuario, para que la
primera instalación y las siguientes actualizaciones usen el mismo origen.
El instalador público fija `--scope user` explícitamente para no depender del
valor por defecto de la CLI. Antes de reinstalar, limpia primero cualquier rastro `local` o `project` de Alfred Dev en el contexto actual y después deja activa únicamente la instalación global de usuario.

---

## Los cinco eslabones de la cadena de carga

Claude Code sigue necesitando los mismos cinco eslabones para cargar un plugin:

1. registro global de la fuente GitHub;
2. copia local del origen;
3. caché operativa del plugin;
4. registro de instalación;
5. habilitación en `settings.json`.

La diferencia es que Alfred Dev **no los gestiona ya uno por uno**. Los
comandos de Claude Code se encargan de materializarlos:

```bash
claude plugin marketplace add 686f6c61/alfred-dev --scope user
claude plugin install alfred-dev@alfred-dev --scope user
```

Si alguno de esos eslabones queda roto, el plugin puede seguir sin cargarse de
forma silenciosa, pero el contrato del instalador actual es este:

- verificar requisitos locales mínimos;
- registrar o refrescar la fuente GitHub global de Alfred Dev;
- reinstalar o actualizar el plugin mediante la CLI nativa;
- crear o refrescar el alias personal global `/alfred`;
- eliminar o mover el shim personal obsoleto `~/.claude/commands/alfred.md`
  para evitar duplicados en el menú de slash commands;
- parchear la instalación para usar un Python compatible si hace falta;
- recordar que `/reload-plugins` aplica los cambios en la sesión actual, con
  reinicio de Claude Code como fallback si MCP/caché lo exige o el plugin no
  aparece.

### Resumen de los cinco eslabones

| # | Eslabón | Ubicación | Quién lo actualiza ahora |
|---|---------|-----------|--------------------------|
| 1 | Registro global de la fuente | `known_marketplaces.json` | `claude plugin marketplace add/remove` |
| 2 | Copia local del origen | `~/.claude/plugins/marketplaces/alfred-dev/` | `claude plugin marketplace add` |
| 3 | Caché del plugin | `~/.claude/plugins/cache/alfred-dev/alfred-dev/<version>/` | `claude plugin install` |
| 4 | Registro de instalación | `installed_plugins.json` | `claude plugin install/uninstall` |
| 5 | Habilitación | `settings.json > enabledPlugins` | `claude plugin install/uninstall` |

El alias corto no forma parte de esos cinco eslabones del plugin: es un skill
personal global invocable en `~/.claude/skills/alfred/SKILL.md`. El plugin
empaqueta `skills/alfred/alfred/SKILL.md` como fuente oculta
(`user-invocable: false`) y el instalador materializa la copia personal con
`user-invocable: true` para que `/alfred` aparezca una sola vez en el menú de
cualquier proyecto sin depender del namespace del plugin. Si queda un
`~/.claude/commands/alfred.md` de instalaciones anteriores, se elimina o se
mueve a backup para no duplicar el selector.

---

## Diagrama del proceso de instalación

El flujo real actual es este:

```mermaid
sequenceDiagram
    box rgb(40, 40, 50) Script de instalación
        participant S as "install.sh / install.ps1"
    end
    box rgb(30, 60, 80) Entorno local
        participant U as "Usuario / shell"
        participant C as "Claude CLI"
    end
    box rgb(50, 40, 60) Ficheros locales
        participant P as "~/.claude/plugins/"
        participant A as "~/.claude/skills/alfred/"
    end

    U->>S: Ejecutar instalador remoto
    S->>S: Verificar Claude Code, HOME/USERPROFILE y Python 3.10+
    S->>C: claude plugin uninstall alfred-dev@alfred-dev --scope local
    S->>C: claude plugin uninstall alfred-dev@alfred-dev --scope project
    S->>C: claude plugin marketplace remove alfred-dev --scope user (si existe)
    S->>C: claude plugin marketplace add 686f6c61/alfred-dev --scope user
    C-->>P: Registrar fuente global en known_marketplaces.json
    S->>C: claude plugin install alfred-dev@alfred-dev --scope user
    C-->>P: Refrescar cache + installed_plugins + enabledPlugins
    S->>A: Copiar SKILL.md invocable y eliminar shim obsoleto de /alfred
    S->>P: Parchar hooks.json / .mcp.json si python3 no sirve
    S-->>U: Ejecuta /reload-plugins; reinicia si MCP/caché lo exige
```

---

## Script de instalación para macOS y Linux

**Fichero:** `install.sh`

**Uso:**

```bash
curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash
```

Si ya tienes el repo clonado o descargado localmente, puedes ejecutar el mismo
instalador directamente desde esa copia:

```bash
bash ./install.sh
```

El script es idempotente: si ya existe una instalación previa, la refresca en
vez de exigir desinstalación manual.

### Qué verifica

Antes de tocar la instalación, el script comprueba:

1. que existe un `HOME` válido;
2. que existe `~/.claude/`;
3. que el comando `claude` está disponible;
4. que existe un Python **3.10 o superior**.

La detección de Python no se limita a `python3`: prueba también variantes como
`python3.13`, `python3.12`, `python3.11` o `python3.10`, y en macOS revisa las
rutas habituales de Homebrew (`/opt/homebrew/bin`, `/usr/local/bin`) si el
intérprete del PATH es demasiado antiguo.

### Qué hace realmente

Una vez verificado el entorno:

1. limpia instalaciones heredadas con
   `claude plugin uninstall alfred-dev@alfred-dev --scope local` y
   `claude plugin uninstall alfred-dev@alfred-dev --scope project`;
2. limpia fuentes heredadas con
   `claude plugin marketplace remove alfred-dev --scope local` y
   `claude plugin marketplace remove alfred-dev --scope project`;
3. desinstala la instancia previa `user` del plugin si sigue registrada;
4. elimina el registro previo `user` de Alfred Dev si existe;
5. ejecuta `claude plugin marketplace add 686f6c61/alfred-dev --scope user`;
6. confirma que Claude Code dejó registrada la fuente GitHub en `known_marketplaces.json`;
7. ejecuta `claude plugin install alfred-dev@alfred-dev --scope user`;
8. copia `skills/alfred/alfred/SKILL.md` desde la caché instalada a
   `~/.claude/skills/alfred/SKILL.md` con `user-invocable: true` y elimina o
   mueve `~/.claude/commands/alfred.md` para que `/alfred` sea global sin
   duplicarse en el selector;
9. si el `python3` por defecto no es válido pero sí hay otro Python
   compatible, parchea la instalación para que hooks y MCP usen esa ruta.

El instalador público normaliza la instalación a **global de usuario**
(`--scope user`). Si detecta rastros heredados de Alfred Dev en `local` o
`project`, los elimina primero y luego reinstala por la ruta global. Incluso
cuando se audita una copia local del worktree, la fuente debe registrarse con
`claude plugin marketplace add "$PWD" --scope user` y la instalación debe
hacerse con `claude plugin install alfred-dev@alfred-dev --scope user`; no se usa `--scope local` como ruta soportada. Si
instalas el worktree a mano con esos comandos directos, rematerializa también
el alias personal global desde `skills/alfred/alfred/SKILL.md` a
`~/.claude/skills/alfred/SKILL.md`, cambiando `user-invocable: false` por
`user-invocable: true`, y elimina `~/.claude/commands/alfred.md` si es el shim
obsoleto de Alfred Dev. Si
`/alfred-dev:update` detecta una
instalación `local` o `project` heredada, avisa y la convierte a instalación
global de usuario en vez de conservar ese scope.
En otras palabras, la instalación normal soportada es siempre una
instalación global de usuario.

Si coexisten varias versiones del plugin en `~/.claude/plugins/cache/alfred-dev/`,
el instalador parchea de forma determinista la instalación activa: primero la
ruta exacta `cache/alfred-dev/alfred-dev/<version>` y, si esa estructura no
está disponible, la versión más reciente cuyo `plugin.json` declare la misma
versión que el instalador acaba de desplegar.

### Parcheo de Python compatible

El instalador no recompila ni rehace el plugin. Solo actualiza dos puntos del
runtime instalado cuando `python3` no apunta a una versión válida:

- `hooks/hooks.json`, reemplazando el `command` de los hooks Python por la ruta
  absoluta del intérprete compatible y manteniendo los `args` con
  `${CLAUDE_PLUGIN_ROOT}`;
- `.mcp.json`, sustituyendo el `command` del servidor
  `alfred-memory`.

Ese parcheo es importante sobre todo en macOS, donde `/usr/bin/python3` puede
seguir siendo 3.9 aunque el usuario tenga 3.12+ instalado por Homebrew o pyenv.

### Nota para desarrollo local del plugin

Alfred Dev declara su servidor de memoria en `.mcp.json` porque Claude Code
descubre los MCP de plugin desde la raíz del plugin. Cuando se ejecuta
`claude mcp list` estando dentro del propio repositorio de Alfred Dev, Claude
Code también interpreta ese mismo `.mcp.json` como configuración MCP de
proyecto y puede mostrar una segunda entrada `alfred-memory` en estado
`Pending approval`.

No hay que aprobar esa entrada de proyecto para validar el plugin. La señal
canónica es la entrada con prefijo de plugin:

```bash
claude mcp get plugin:alfred-dev:alfred-memory
```

Debe aparecer como `Status: ✔ Connected`. En una instalación global de usuario
`--scope user`, `claude mcp list` desde otro directorio permite ver la lista sin
el duplicado de proyecto. Durante una auditoría del worktree, registra también
la fuente local con `--scope user`; así `/alfred` y `/alfred-dev:*` siguen
disponibles fuera del repo.

---

## Script de instalación para Windows

**Fichero:** `install.ps1`

**Uso (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex
```

La filosofía es la misma que en Bash: la CLI de Claude Code hace la instalación
real y el script añade detección robusta de Python y parcheo de runtime.

### Diferencias con el script bash

| Aspecto | Bash (`install.sh`) | PowerShell (`install.ps1`) |
|---------|---------------------|---------------------------|
| Ruta base | `$HOME/.claude` | `$env:USERPROFILE\\.claude` |
| Detección de Python | `python3`, `python3.13`... + rutas Homebrew | `py -3.13`, `py -3.12`, `py -3.11`, `py -3.10`, `python3`, `python` |
| Verificación de Claude | `command -v claude` | `Get-Command claude` |
| Escritura auxiliar | `sed` + escritura directa | `ConvertFrom-Json` / `ConvertTo-Json` + `Write-TextFileAtomic` |
| Parcheo runtime | reemplazo textual en JSON | mutación estructurada del JSON |

En Windows, Python 3.10+ sigue siendo obligatorio porque hooks, core y MCP se
ejecutan también allí sobre Python. El instalador prueba primero el launcher
`py` y después `python3` o `python`, y actualiza `hooks.json` y `.mcp.json`
para usar la ruta exacta del intérprete encontrado.

---

## Desinstalacion

Los scripts de desinstalacion (`uninstall.sh` para macOS/Linux, `uninstall.ps1`
para Windows) siguen ya la misma filosofía que la instalación: primero intentan
usar la CLI nativa de Claude Code y luego limpian restos físicos o registros si
quedara algún rastro.

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash
```

Desde una copia local del repo:

```bash
bash ./uninstall.sh
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.ps1 | iex
```

### Que se elimina

El flujo actual de desinstalación es:

1. `claude plugin uninstall alfred-dev@alfred-dev --scope user` si la CLI está disponible;
2. `claude plugin marketplace remove alfred-dev --scope user` si la CLI está disponible;
3. borrado de restos en `cache/alfred-dev/` y `marketplaces/alfred-dev/`;
4. limpieza residual de `known_marketplaces.json`,
   `installed_plugins.json` y `settings.json` si todavía hubiera entradas.

El proceso de desinstalacion toca exclusivamente los componentes del plugin dentro de `~/.claude/plugins/` y `~/.claude/settings.json`. La siguiente tabla detalla cada operación en el orden en que se ejecuta:

| Orden | Operación | Descripción |
|-------|-----------|-------------|
| 1 | Eliminar cache | Borra `~/.claude/plugins/cache/alfred-dev/` con todas las versiones |
| 2 | Eliminar directorio de marketplace | Borra `~/.claude/plugins/marketplaces/alfred-dev/` |
| 3 | Limpiar `known_marketplaces.json` | Elimina la entrada `alfred-dev` del mapa de marketplaces conocidos |
| 4 | Limpiar `installed_plugins.json` | Elimina la entrada `alfred-dev@alfred-dev` del inventario de plugins |
| 5 | Limpiar `settings.json` | Elimina la clave `alfred-dev@alfred-dev` de `enabledPlugins` |

La limpieza manual de JSON queda como red de seguridad para instalaciones
antiguas, estados intermedios o residuos que la CLI no hubiera retirado.

### Que no se elimina

Los scripts de desinstalacion no tocan los ficheros de configuración local del proyecto. Esto es intencional: si el usuario reinstala el plugin mas adelante, su configuración de proyecto se conserva. Los ficheros que permanecen son:

- `.claude/alfred-dev.local.md` -- configuración local del proyecto
- `.claude/alfred-dev-state.json` -- estado persistente del plugin

Para una limpieza total, estos ficheros deben eliminarse manualmente desde cada proyecto donde se haya utilizado Alfred Dev.

Despues de la desinstalacion, ejecuta `/reload-plugins` en las sesiones abiertas
para descargar la superficie del plugin. Si Claude Code avisa por MCP/caché o
sigue mostrando comandos de Alfred, cierra y vuelve a abrir Claude Code.

---

## Actualización

La actualización se gestiona a traves del comando `/alfred-dev:update`, que
comprueba si hay una versión mas reciente en GitHub y, si existe, presenta un
único menú seleccionable para decidir si se aplica o no. Antes de aplicar nada,
lee `claude plugin list --json` para saber si Alfred Dev esta instalado como
`user`, `local`, `project` o `managed`.

### Como funciona el proceso

El flujo de actualización consta de cuatro pasos que el comando ejecuta de forma interactiva:

**Paso 1 -- Obtener la versión instalada y el scope.** El comando consulta
`claude plugin list --json` y extrae `version`, `scope`, `installPath` y, si
existe, `projectPath` de la entrada `alfred-dev@alfred-dev`. Si la CLI no
devuelve la entrada, usa como fallback el `plugin.json` mas reciente dentro de
`~/.claude/plugins/cache/alfred-dev/` y marca el scope como desconocido.

**Paso 2 -- Consultar la última release en GitHub.** Hace una peticion a la API de GitHub en `https://api.github.com/repos/686f6c61/alfred-dev/releases/latest` y extrae el `tag_name` (versión), el `name` (titulo de la release), el `body` (notas del cambio) y la fecha de publicacion.

**Paso 3 -- Comparar versiones.** El `tag_name` (sin el prefijo `v`) y la versión instalada deben compararse como semver real, nunca como texto plano. `0.10.0` es mayor que `0.9.0`, aunque lexicograficamente parezca lo contrario. Si la release es mas nueva, el comando muestra las notas y ofrece un único menú con dos opciones: actualizar ahora o cancelar. Si las versiones coinciden, informa de que el plugin esta al dia y termina.

**Paso 4 -- Ejecutar la actualización.** Si el usuario acepta, el comando usa
la ruta global de usuario salvo en instalaciones `managed`:

- En scope `user`, `local`, `project` o desconocido, detecta la plataforma
  (`uname -s`) y ejecuta el instalador correspondiente. Esta ruta reinstala
  mediante la CLI nativa de Claude Code con `--scope user`, limpia primero
  cualquier rastro `local` o `project` de Alfred Dev en el contexto actual y
  mantiene el parche de Python compatible para hooks y MCP. También refresca
  `~/.claude/skills/alfred/SKILL.md`, el alias personal global que hace visible
  `/alfred` sin namespace, y elimina el shim obsoleto de commands si existe. Si
  el scope detectado era `local` o `project`, el
  comando lo explica antes: la actualización normaliza a instalación global de
  usuario.

- **macOS / Linux:** `curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash`
- **Windows:** `irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex`

- En scope `managed`, no intenta actualizar: informa de que la instalación la
  controla una política de administrador.

Los instaladores son idempotentes: vuelven a registrar el marketplace,
reinstalan el plugin mediante la CLI nativa de Claude Code y mantienen la
habilitación activa. No es necesario desinstalar antes de actualizar en scope
`user`.

Tras la actualización, el usuario debe ejecutar `/reload-plugins` para cargar la
nueva versión en la sesión actual. Si Claude Code avisa por MCP/caché o el
inventario no cambia, debe reiniciar Claude Code.

---

## Resolución de problemas

Claude Code actual sí ofrece diagnósticos útiles para plugins, aunque algunos
fallos de instalación siguen pareciendo "el plugin no aparece" si solo miras la
lista de comandos. Antes de tocar ficheros internos, usa primero la superficie
oficial de diagnóstico:

```bash
claude plugin list
claude plugin details alfred-dev@alfred-dev
claude plugin validate . --strict
claude --debug
```

Dentro de una sesión interactiva, `/plugin` muestra los plugins instalados y
prioriza los que tienen errores de carga. `/plugin validate` valida el manifest,
frontmatter de skills/agentes/comandos y `hooks/hooks.json`; `/reload-plugins`
recarga la superficie activa tras instalar, habilitar o deshabilitar plugins.
Si esos diagnósticos no explican el problema, entonces revisa los cinco
eslabones de la cadena de carga.

### Claude Code no detecta el plugin

Es el problema mas frecuente y casi siempre se debe a una validación fallida, a
una sesión sin recargar plugins o a que falta uno de los cinco eslabones. La
forma mas fiable de diagnosticarlo es mirar primero `claude plugin list`,
`claude plugin details alfred-dev@alfred-dev` y `/plugin` dentro de Claude Code.
Si el inventario sigue sin explicar el fallo, verifica cada eslabon en orden:

```bash
# 1. Comprobar que el marketplace esta registrado
python3 -c "import json; print(json.dumps(json.load(open('$HOME/.claude/plugins/known_marketplaces.json')), indent=2))"

# 2. Comprobar que el directorio del marketplace existe y tiene el catalogo
ls -la ~/.claude/plugins/marketplaces/alfred-dev/.claude-plugin/

# 3. Comprobar que la cache existe y contiene plugin.json
ls -la ~/.claude/plugins/cache/alfred-dev/alfred-dev/*/.claude-plugin/

# 4. Comprobar el registro de instalación
python3 -c "import json; d=json.load(open('$HOME/.claude/plugins/installed_plugins.json')); print(json.dumps(d.get('plugins',{}).get('alfred-dev@alfred-dev','NO ENCONTRADO'), indent=2))"

# 5. Comprobar la habilitacion
python3 -c "import json; d=json.load(open('$HOME/.claude/settings.json')); print(d.get('enabledPlugins',{}).get('alfred-dev@alfred-dev','NO HABILITADO'))"
```

Si alguno de estos comandos devuelve un resultado inesperado, ese es el eslabon
roto. La solucion mas directa suele ser reinstalar el plugin ejecutando de nuevo
el script de instalación. Si `claude plugin validate . --strict` falla desde el
checkout del plugin, corrige primero el manifest, frontmatter o `hooks.json`
señalado por la CLI.

### Error "marketplace no registrado"

Si `known_marketplaces.json` no contiene la entrada `alfred-dev`, Claude Code no sabe donde buscar el plugin. Esto puede ocurrir si el fichero se reinicio o si otra herramienta lo sobreescribio. La solucion es ejecutar de nuevo el instalador, que registra el marketplace de forma idempotente.

### El plugin no se carga tras instalar

Si el plugin se acaba de instalar mientras Claude Code ya estaba ejecutandose,
ejecuta primero `/reload-plugins`. Claude Code recarga los plugins activos y
muestra el inventario actualizado de plugins, skills, agentes, hooks y MCP. Si
la recarga avisa por coste/caché de MCP, usa `/reload-plugins --force` solo si
aceptas ese coste en la siguiente petición; si no quieres forzarlo o el plugin
sigue sin aparecer, cierra Claude Code completamente y vuelve a abrirlo.

### Permisos en macOS

Si los scripts no se ejecutan, es probable que no tengan permiso de ejecución. Aunque el método recomendado (`curl | bash`) no requiere permisos especiales en el script remoto, si se descarga manualmente el fichero hay que asegurarse de que tiene permisos adecuados:

```bash
chmod +x install.sh
```

### El fichero JSON interno esta corrupto

Si algun fichero interno de Claude Code (`known_marketplaces.json`,
`installed_plugins.json`, `settings.json`) contiene JSON invalido, tanto la
instalación como la carga del plugin pueden fallar. El instalador actual no
reconstruye esos ficheros por su cuenta: normalmente verás un error propagado
desde la propia CLI de Claude Code o un estado incompleto tras `claude plugin
marketplace add` / `claude plugin install`.

Si sospechas corrupcion en esos ficheros, la recuperación sigue siendo manual.
Por ejemplo:

```bash
# Restaurar known_marketplaces.json
echo '{}' > ~/.claude/plugins/known_marketplaces.json

# Restaurar installed_plugins.json
echo '{"version":2,"plugins":{}}' > ~/.claude/plugins/installed_plugins.json
```

Despues de restaurar el fichero, se puede ejecutar el instalador de nuevo para
que la CLI de Claude Code reconstruya las entradas del plugin.

### Resumen rápido de diagnóstico

| Sintoma | Causa probable | Solucion |
|---------|---------------|----------|
| Plugin invisible en Claude Code | Validación fallida, sesión sin recargar o falta algun eslabon | `claude plugin list/details`, `/plugin`, `/reload-plugins`, luego verificar los 5 eslabones |
| `/alfred` no aparece en el menú | Falta `~/.claude/skills/alfred/SKILL.md`, la copia personal no tiene `user-invocable: true` o la sesión arrancó antes de que existiera la carpeta personal de skills | Reinstalar con `install.sh`, ejecutar `/reload-plugins --force`; si el menú sigue sin vigilar la carpeta nueva, reiniciar Claude Code |
| "marketplace no registrado" | `known_marketplaces.json` sin la entrada | Reinstalar con `install.sh` |
| Plugin instalado pero no aparece | Sesión sin recargar plugins | Ejecutar `/reload-plugins`; reiniciar si MCP/caché lo exige |
| Error de manifest/frontmatter/hooks | Schema o sintaxis incompatible | `claude plugin validate . --strict` o `/plugin validate` |
| Script no se ejecuta en macOS | Sin permisos de ejecución | `chmod +x install.sh` |
| Error de JSON invalido | Fichero corrupto por interrupcion | Restaurar el fichero y reinstalar |
| Fallo de red al actualizar | Sin conexión o rate limit de GitHub | Reintentar mas tarde |
