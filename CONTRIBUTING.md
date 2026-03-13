# Guia de contribucion

Alfred Dev es un plugin de Claude Code compuesto por agentes, skills, comandos, hooks y modulos core en Python. Esta guia explica como anadir o modificar cada tipo de componente para que las contribuciones sean consistentes con la arquitectura existente.

## Requisitos previos

- Python 3.10 o superior.
- Claude Code instalado y configurado.
- git.

No hay dependencias externas: todo el codigo Python usa exclusivamente la stdlib.

## Estructura del proyecto

```
alfred-dev/
  agents/                 # 8 agentes de nucleo (.md)
  agents/optional/        # 7 agentes opcionales (.md)
  commands/               # 11 comandos /alfred (.md)
  skills/                 # 60 skills en 13 dominios (SKILL.md)
  hooks/                  # 11 hooks del ciclo de vida (.py, .sh)
    hooks.json            # Registro de eventos
  core/                   # Motor de orquestacion y memoria (Python)
  mcp/                    # Servidor MCP stdio (memoria persistente)
  templates/              # 7 plantillas de artefactos (.md)
  tests/                  # Tests unitarios (pytest, unittest)
```

## Anadir un agente

Los agentes son ficheros Markdown con frontmatter YAML que define metadatos y un system prompt en el cuerpo.

1. Crear `agents/<nombre>.md` (nucleo) o `agents/optional/<nombre>.md` (opcional).
2. Incluir el frontmatter obligatorio:

```yaml
---
name: nombre-del-agente
description: Descripcion breve de su rol y cuando se activa.
model: opus          # opus para razonamiento complejo, sonnet para tareas estructuradas
tools: [Glob, Grep, Read, Write, Edit, Bash]
color: "#hex"        # Color identificativo del agente
---
```

3. Escribir el system prompt en el cuerpo del Markdown. Incluir:
   - Identidad y rol.
   - Proceso de trabajo paso a paso.
   - Criterios de exito.
   - Frases tipicas (personalidad).

4. Registrar el agente en `.claude-plugin/plugin.json` dentro del array `agents`.
5. Si es opcional, anadirlo al catalogo de agentes en `commands/_composicion.md` y a `suggest_optional_agents()` en `core/config_loader.py`.
6. Anadir tests si el agente tiene logica programatica.

## Anadir un skill

Cada skill es un directorio dentro de `skills/<dominio>/` con un fichero `SKILL.md`.

1. Crear `skills/<dominio>/<nombre-skill>/SKILL.md`.
2. Formato del fichero:

```yaml
---
name: nombre-del-skill
description: Que hace y cuando usarlo.
---
```

3. En el cuerpo, documentar:
   - Proposito.
   - Proceso paso a paso.
   - Criterios de exito.
   - Errores comunes y como evitarlos.

4. Registrar en `.claude-plugin/plugin.json` si el skill debe ser invocable directamente.

## Anadir un comando

Los comandos son ficheros Markdown en `commands/` que definen slash commands de Claude Code.

1. Crear `commands/<nombre>.md`.
2. Frontmatter obligatorio:

```yaml
---
name: nombre
description: Descripcion que aparece en /alfred help.
---
```

3. El cuerpo contiene las instrucciones que Claude recibe al invocar el comando.

## Anadir un hook

Los hooks interceptan eventos del ciclo de vida de Claude Code. Pueden ser scripts Python o Bash.

1. Crear `hooks/<nombre>.<py|sh>`.
2. Registrar el hook en `hooks/hooks.json` con el evento y la configuracion:

```json
{
  "event": "PreToolUse",
  "pattern": "Write|Edit",
  "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/<nombre>.py",
  "async": false
}
```

3. **Convenciones de salida:**
   - `exit 0` -- Permitir la operacion (informativo).
   - `exit 2` -- Bloquear la operacion (hook de seguridad).

4. **Entrada:** los hooks reciben JSON por stdin con los datos del evento.
5. **Tests obligatorios:** crear `tests/test_<nombre>.py` con cobertura de los casos criticos.

## Modificar el core

Los modulos en `core/` contienen la logica del plugin en Python:

| Modulo | Responsabilidad |
|--------|-----------------|
| `config_loader.py` | Carga de configuracion, deteccion de stack |
| `orchestrator.py` | Maquina de estados, gestion de flujos |
| `personality.py` | Motor de personalidad, tono, frases |
| `memory.py` | Base de datos SQLite de memoria persistente |

Reglas para modificar el core:

- Ejecutar los tests antes y despues: `python3 -m pytest tests/ -v`.
- Mantener cero dependencias externas (solo stdlib).
- Documentar funciones publicas con docstrings.
- Los secretos nunca se almacenan en texto plano: pasar por `sanitize_content()`.

## Tests

El proyecto usa `unittest` como framework (stdlib) y `pytest` como runner.

```bash
# Ejecutar todos los tests
python3 -m pytest tests/ -v

# Ejecutar un fichero concreto
python3 -m pytest tests/test_memory.py -v

# Con cobertura (requiere pip install coverage)
coverage run -m pytest tests/ -v
coverage report
```

Convenciones:

- Nombrar ficheros `test_<modulo>.py`.
- Usar `tempfile.NamedTemporaryFile` o `TemporaryDirectory` para fixtures de disco.
- Limpiar ficheros WAL/SHM de SQLite en `tearDown()`.
- Evitar mocks excesivos: usar instancias reales cuando sea posible.

## Estilo

- Codigo Python: PEP 8.
- Comentarios y documentacion: castellano de Espana.
- Variables y funciones: ingles.
- Commits: `tipo: descripcion breve` (feat, fix, refactor, docs, test, chore).

## Proceso de contribucion

1. Crear rama descriptiva: `feature/<nombre>`, `fix/<nombre>`.
2. Implementar el cambio con tests.
3. Verificar que pasan los 326+ tests.
4. Abrir pull request con descripcion del cambio y motivacion.
