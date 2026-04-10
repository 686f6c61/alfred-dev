# Instalación y cadena de carga

Alfred Dev ya no instala el plugin copiando repositorios ni editando a mano los
JSON internos de Claude Code. El flujo actual delega la instalación en la CLI
nativa de Claude Code y solo añade una capa de verificación y parcheo donde el
plugin lo necesita de verdad: detección de Python 3.10+ y ajuste de `hooks.json`
y `mcp.json` cuando `python3` del sistema no es compatible.

Esto importa porque la cadena de carga sigue existiendo, pero el responsable de
materializarla ya no es un script artesanal del plugin, sino `claude plugin
marketplace add` y `claude plugin install`. Los instaladores de Alfred Dev se
limitan a dejar el entorno listo, pedir a Claude Code que registre globalmente
la fuente GitHub del plugin e instalar la versión nueva.

Importante: aquí `marketplace` es el nombre del subcomando de Claude Code, no
una tienda oficial de plugins. Alfred Dev es un plugin independiente y no oficial.
La orden:

```bash
claude plugin marketplace add 686f6c61/alfred-dev
```

le dice a Claude Code que registre una **fuente GitHub propia** en
`known_marketplaces.json`, de forma global para ese usuario, para que la
primera instalación y las siguientes actualizaciones usen el mismo origen.

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
claude plugin marketplace add 686f6c61/alfred-dev
claude plugin install alfred-dev@alfred-dev
```

Si alguno de esos eslabones queda roto, el plugin puede seguir sin cargarse de
forma silenciosa, pero el contrato del instalador actual es este:

- verificar requisitos locales mínimos;
- registrar o refrescar la fuente GitHub global de Alfred Dev;
- reinstalar o actualizar el plugin mediante la CLI nativa;
- parchear la instalación para usar un Python compatible si hace falta;
- recordar que Claude Code debe reiniciarse.

### Resumen de los cinco eslabones

| # | Eslabón | Ubicación | Quién lo actualiza ahora |
|---|---------|-----------|--------------------------|
| 1 | Registro global de la fuente | `known_marketplaces.json` | `claude plugin marketplace add/remove` |
| 2 | Copia local del origen | `~/.claude/plugins/marketplaces/alfred-dev/` | `claude plugin marketplace add` |
| 3 | Caché del plugin | `~/.claude/plugins/cache/alfred-dev/alfred-dev/<version>/` | `claude plugin install` |
| 4 | Registro de instalación | `installed_plugins.json` | `claude plugin install/uninstall` |
| 5 | Habilitación | `settings.json > enabledPlugins` | `claude plugin install/uninstall` |

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
    end

    U->>S: Ejecutar instalador remoto
    S->>S: Verificar Claude Code, HOME/USERPROFILE y Python 3.10+
    S->>C: claude plugin marketplace remove alfred-dev (si existe)
    S->>C: claude plugin marketplace add 686f6c61/alfred-dev
    C-->>P: Registrar fuente global en known_marketplaces.json
    S->>C: claude plugin install alfred-dev@alfred-dev
    C-->>P: Refrescar cache + installed_plugins + enabledPlugins
    S->>P: Parchar hooks.json / mcp.json si python3 no sirve
    S-->>U: Reinicia Claude Code
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

1. desinstala la instancia previa del plugin si sigue registrada;
2. elimina el registro previo de Alfred Dev si existe;
3. ejecuta `claude plugin marketplace add 686f6c61/alfred-dev`;
4. confirma que Claude Code dejó registrada la fuente GitHub en `known_marketplaces.json`;
5. ejecuta `claude plugin install alfred-dev@alfred-dev`;
6. si el `python3` por defecto no es válido pero sí hay otro Python
   compatible, parchea la instalación para que hooks y MCP usen esa ruta.

Si coexisten varias versiones del plugin en `~/.claude/plugins/cache/alfred-dev/`,
el instalador parchea de forma determinista la instalación activa: primero la
ruta exacta `cache/alfred-dev/alfred-dev/<version>` y, si esa estructura no
está disponible, la versión más reciente cuyo `plugin.json` declare la misma
versión que el instalador acaba de desplegar.

### Parcheo de Python compatible

El instalador no recompila ni rehace el plugin. Solo actualiza dos puntos del
runtime instalado cuando `python3` no apunta a una versión válida:

- `hooks/hooks.json`, reemplazando `python3 ${CLAUDE_PLUGIN_ROOT}` por la ruta
  absoluta del intérprete compatible;
- `.claude-plugin/mcp.json`, sustituyendo el `command` del servidor
  `alfred-memory`.

Ese parcheo es importante sobre todo en macOS, donde `/usr/bin/python3` puede
seguir siendo 3.9 aunque el usuario tenga 3.12+ instalado por Homebrew o pyenv.

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
`py` y después `python3` o `python`, y actualiza `hooks.json` y `mcp.json`
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

1. `claude plugin uninstall alfred-dev@alfred-dev` si la CLI está disponible;
2. `claude plugin marketplace remove alfred-dev` si la CLI está disponible;
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

Despues de la desinstalacion, es necesario reiniciar Claude Code para que los cambios surtan efecto.

---

## Actualización

La actualización se gestiona a traves del comando `/alfred-dev:update`, que
comprueba si hay una versión mas reciente en GitHub y, si existe, presenta un
único menú seleccionable para decidir si se aplica o no.

### Como funciona el proceso

El flujo de actualización consta de cuatro pasos que el comando ejecuta de forma interactiva:

**Paso 1 -- Obtener la versión instalada.** El comando busca el fichero `plugin.json` mas reciente dentro de `~/.claude/plugins/cache/alfred-dev/` y lee el campo `version`. Si coexisten varias versiones en cache (por actualizaciones previas), selecciona la mas reciente por fecha de modificacion.

**Paso 2 -- Consultar la última release en GitHub.** Hace una peticion a la API de GitHub en `https://api.github.com/repos/686f6c61/alfred-dev/releases/latest` y extrae el `tag_name` (versión), el `name` (titulo de la release), el `body` (notas del cambio) y la fecha de publicacion.

**Paso 3 -- Comparar versiones.** El `tag_name` (sin el prefijo `v`) y la versión instalada deben compararse como semver real, nunca como texto plano. `0.10.0` es mayor que `0.9.0`, aunque lexicograficamente parezca lo contrario. Si la release es mas nueva, el comando muestra las notas y ofrece un único menú con dos opciones: actualizar ahora o cancelar. Si las versiones coinciden, informa de que el plugin esta al dia y termina.

**Paso 4 -- Ejecutar la actualización.** Si el usuario acepta, el comando detecta la plataforma (`uname -s`) y ejecuta el instalador correspondiente:

- **macOS / Linux:** `curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash`
- **Windows:** `irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex`

Los instaladores son idempotentes: vuelven a registrar el marketplace,
reinstalan el plugin mediante la CLI nativa de Claude Code y mantienen la
habilitación activa. No es necesario desinstalar antes de actualizar.

Tras la actualización, el usuario debe reiniciar Claude Code para que se cargue la nueva versión.

---

## Resolución de problemas

Claude Code no ofrece diagnosticos cuando un plugin no se carga. El fallo es completamente silencioso: el plugin simplemente no aparece. Esto hace que la depuración requiera verificar los cinco eslabones de la cadena de forma manual y sistematica.

### Claude Code no detecta el plugin

Es el problema mas frecuente y casi siempre se debe a que falta uno de los cinco eslabones. La forma mas fiable de diagnosticarlo es verificar cada uno en orden:

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

Si alguno de estos comandos devuelve un resultado inesperado, ese es el eslabon roto. La solucion mas directa suele ser reinstalar el plugin ejecutando de nuevo el script de instalación.

### Error "marketplace no registrado"

Si `known_marketplaces.json` no contiene la entrada `alfred-dev`, Claude Code no sabe donde buscar el plugin. Esto puede ocurrir si el fichero se reinicio o si otra herramienta lo sobreescribio. La solucion es ejecutar de nuevo el instalador, que registra el marketplace de forma idempotente.

### El plugin no se carga tras instalar

Claude Code carga los plugins unicamente al inicio de sesión. Si el plugin se acaba de instalar pero Claude Code ya estaba ejecutandose, no lo detectara hasta el siguiente reinicio. La solucion es cerrar Claude Code completamente y volver a abrirlo.

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
| Plugin invisible en Claude Code | Falta algun eslabon de la cadena | Verificar los 5 eslabones en orden |
| "marketplace no registrado" | `known_marketplaces.json` sin la entrada | Reinstalar con `install.sh` |
| Plugin instalado pero no aparece | Claude Code no se ha reiniciado | Cerrar y abrir Claude Code |
| Script no se ejecuta en macOS | Sin permisos de ejecución | `chmod +x install.sh` |
| Error de JSON invalido | Fichero corrupto por interrupcion | Restaurar el fichero y reinstalar |
| Fallo de red al actualizar | Sin conexión o rate limit de GitHub | Reintentar mas tarde |
