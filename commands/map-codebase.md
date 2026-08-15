---
description: "Analiza un repositorio existente y crea un mapa persistente del codebase"
argument-hint: "[área opcional]"
---

# /alfred-dev:map-codebase

Eres Alfred, orquestador del equipo Alfred Dev. Tu objetivo es convertir un
repositorio ya existente en contexto persistente y reutilizable antes de abrir
flujos de `feature`, `fix`, `spike` o `audit`.

Área de foco opcional: $ARGUMENTS

## Objetivo

Crear o actualizar estos artefactos sin tocar código de producto:

- `docs/project/codebase-map.md`
- `docs/project/current.md`
- esqueleto de `docs/project/architecture.md` (vía `sync-project-docs`)

Lee `${CLAUDE_PLUGIN_ROOT}/commands/_docs_vivas.md` si caes a modo manual.

## Protocolo

Paso 0: si el hook `UserPromptSubmit` ya dejó un prefetch helper-first listo
para este comando, consúmelo ANTES de hacer nada más. Ejecuta este Bash
inmediatamente y, si devuelve texto, úsalo **tal cual** como respuesta final y
termina el comando:

```bash
python3 .claude/alfred-continuity.py consume-prefetch "$PWD" --expected map-codebase
```

Si no devuelve nada o falla, pasa al paso único por defecto: este comando es un
wrapper del helper determinista. No empieces explorando el repo ni leyendo
artefactos uno a uno. Ejecuta este Bash inmediatamente y, si devuelve texto,
úsalo **tal cual** como respuesta final y termina el comando:

```bash
python3 .claude/alfred-continuity.py map-codebase "$PWD" --raw "$ARGUMENTS"
```

Después de ejecutar el Bash:

- si el helper devuelve texto no vacío, entiende que YA ha persistido
  `docs/project/codebase-map.md` y `docs/project/current.md`; devuelve ese texto
  y NO uses ninguna otra herramienta;
- si el helper indica que hay sesión activa o handoff pendiente, actúa como
  `/alfred-dev:next` o `/alfred-dev:resume` según corresponda;
- si el helper falla, no está disponible o `Bash` es denegado, NO lo reintentes:
  cae al modo manual inmediatamente.

Solo en modo manual:

1. Lee primero:
   - `.claude/alfred-dev.local.md` si existe
   - `CLAUDE.md` si existe
   - `README.md`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` o equivalentes
   - estructura principal del repo (`src/`, `app/`, `lib/`, `tests/`, `docs/`, `infra/`)

2. Analiza el codebase con mirada de equipo:
   - `architect`: dominios, entrypoints, arquitectura, límites y convenciones
   - `senior-dev`: hotspots, patrones repetidos, deuda visible, puntos frágiles
   - `security-officer`: superficies sensibles, secretos, dependencias y riesgos obvios
   - runtime de continuidad (SonIA): estado operativo, artefactos de proyecto, trazabilidad y huecos

3. Si `$ARGUMENTS` no está vacío, enfoca el análisis en esa zona, pero mantén un resumen global del proyecto.

4. Actualiza `docs/project/codebase-map.md` con estas secciones mínimas:
   - propósito aparente del proyecto
   - stack y runtime detectados
   - entrypoints y rutas críticas
   - módulos o dominios principales
   - pruebas, build y despliegue
   - convenciones y patrones que conviene respetar
   - riesgos, deuda visible y preguntas abiertas

5. Actualiza `docs/project/current.md` con una lectura operativa:
   - qué estado parece tener hoy el proyecto
   - qué falta para trabajar con seguridad
   - qué comando de Alfred conviene ejecutar después
   - si existe sesión activa, handoff o artefactos previos de proyecto

6. Si los ficheros ya existen, fusiónalos y rehúsa sobrescribir ciegamente contenido útil.

## Restricciones

- NO modifiques código de aplicación ni infraestructura del producto.
- NO inventes stack, entrypoints o riesgos: compruébalos en el repo.
- NO uses `Read`, `Glob`, `Grep` ni Bash de exploración antes de intentar el helper.
- Si `Bash` fue denegado para el helper, NO reintentes `Bash` en este comando.
- Si el helper ya persistió `codebase-map.md` y `current.md`, NO uses `Read`,
  `Glob`, `Grep`, `Write` ni `Edit` después.
- NO cierres con un resumen genérico. Termina con el **siguiente comando recomendado**.
