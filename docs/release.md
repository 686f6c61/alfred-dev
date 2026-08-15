# Release y auditoría (0.7.0)

Esta página sustituye las matrices fijas de 0.6.0. Describe cómo se publica
Alfred Dev **ahora**: inventario real, comandos de auditoría y revisión humana.
No congela hashes ni recuentos de una release antigua. Docs oficiales
revalidadas 2026-08-15.

Inventario público actual: **10 agentes**, **11 skills**, **18 comandos**
namespaced, **10 hooks**. `plugin.json` es la fuente canónica de `version`.
`marketplace.json` no duplica ese campo. El `displayName: "Alfred Dev"` es el
nombre humano; el namespace técnico es `alfred-dev`.

No hay alias global `/alfred`. La entrada es `/alfred-dev:alfred`. El instalador
no pisa `~/.claude/skills` ni crea `~/.claude/commands/alfred.md`.

---

## Superficie que hay que alinear

Antes de publicar, estas superficies deben decir lo mismo:

- `.claude-plugin/plugin.json` (18 comandos publicados)
- `commands/` (más internos `_composicion.md`, `_docs_vivas.md`, `next.md`, `search.md`)
- `agents/` (10 fichas)
- `skills/*/SKILL.md` (11 planas)
- `hooks/hooks.json` (10 scripts)
- `README.md`, `docs/architecture.md`, `docs/commands.md`, `docs/skills.md`
- `package.json` (scripts de auditoría)

Los flujos cargan `_composicion.md` y `_docs_vivas.md` desde la instalación del
plugin, no desde el proyecto auditado.

Claude Code describe commands/ como skills planas soportadas y recomienda
`skills/` para plugins nuevos. Alfred conserva `commands/` para la UX pública
`/alfred-dev:*`. El frontmatter de comandos es más estrecho que el de skills:
`description`, `argument-hint`, `allowed-tools`, `disallowed-tools`, `model`.
`argument-hint` va con `$ARGUMENTS`. `model` se valida contra alias/IDs
actuales. Las reglas de herramientas usan nombres oficiales, tanto inline como
en lista YAML.

Cada `SKILL.md` declara `name` coincidente con el directorio, `description` +
`when_to_use` dentro del límite de listing de 1.536 caracteres, y
`disable-model-invocation: true` en los skills con side effects
(style-direction, sonarqube, incident-response, pr-workflow).

---

## Comandos de auditoría

| Gate | Comando | Qué valida |
|------|---------|------------|
| Suite local | `python3 -m pytest tests/ -q` | Core, hooks, MCP, instaladores, contratos |
| Auditoría base | `npm run release:audit` | Inventario 0.7.0, manifiestos, frontmatter, empaquetado |
| Auditoría completa | `npm run release:audit:full` | Base + continuidad + MCP + contratos externos sin side effects |
| Preflight Claude | `npm run release:audit:manual:preflight` | Auth y CLI (`auth_preflight.status=ok`) |
| Evidencia manual | `npm run release:audit:manual:evidence` | Matriz worktree (`scripts/manual_smoke.py`) |
| Evidencia instalada | `npm run release:audit:manual:evidence:installed` | Misma matriz contra caché user |
| Revisión humana | `npm run release:audit:manual:review` | Plantilla aprobada, fechada, anotada |
| Prepublish | `npm run release:audit:prepublish` | Full + preflight + reviews; no regenera evidencias |

La matriz manual cubre las **18 rutas publicas**, **40 opciones publicas** y
**4 contratos runtime** de `/update`. Los IDs de opción se validan contra
comandos publicados. Cada `argument-hint` tiene opción cubierta. Los scripts de
evidencia ejecutan `--auth-preflight`. Los previews se sanitizan con
`core/secrets.py`. Evidencias y plantillas se escriben con permisos `0600` y
están ignoradas por git y npm (`docs/manual-smoke*.json`,
`docs/manual-smoke*.md`).

El gate de revisión exige `evidence_file`, `evidence_sha256` y
`plugin_surface.sha256` de esa run (no un hash congelado en este documento).
Rechaza evidencias antiguas (`--require-current-auth-preflight`), secretos,
notas genéricas (`notes_low_quality`) o repetidas (`notes_repeated`). No crea
plantilla desde evidencia contaminada. No aprueba la release por sí mismo:
hace falta `approved=true` humano.

Pendientes que no cubre el contrato local (siguen siendo revisión humana o
entorno real): GitHub Sync con `gh`, SonarQube/Docker, Lucius contra Codex
CLI. El preflight externo (`npm run release:audit:external:preflight`,
`scripts/external_live_smoke.py`) no crea issues, no arranca contenedores y
no hace llamadas Codex.

---

## Claims que el audit local sí cubre

- quality gates son verificables por contrato local
- Paquete publicable sin secretos reales (`core/secrets.py`)
- Modelos y colores de agentes con valores actuales de Claude Code
- Herramientas de agentes con nombres oficiales; no `AskUserQuestion` en subagentes
- `_composicion.md` viaja en el paquete pero no se publica
- Detección de stack: Node/TypeScript, Python, Rust, Go, Ruby, Elixir, Java/Kotlin, PHP, C#/.NET y Swift
- Selina condicional
- Compliance europeo RGPD/NIS2/CRA
- AskUserQuestion con `questions[]` y `multiSelect`
- Hooks: `decision`, `hookSpecificOutput.hookEventName`,
  `hookSpecificOutput.additionalContext` y `systemMessage`. No se declara
  `matcher` en eventos donde Claude Code lo ignora.

---

## Runbook humano (criterios y bloqueos)

El revisor no afirma haber ejecutado tests, deploys, SonarQube, GitHub Sync,
Docker o Codex si no hay evidencia. Pide decisión humana. No autoaprueba UAT,
deploys, seguridad ni auditorías. No filtra secretos a mano: el gate usa
`core/secrets.py`.

Bloqueos típicos: `blocked_auth`, `first_party_oauth_token_rejected`, notas
vacías, superficie del plugin distinta entre worktree e instalación, matriz
desalineada con `command_coverage` / `option_coverage` / `runtime_coverage`.

Si la auth falla: `claude auth logout`, `claude auth login`, `claude doctor`.
Diagnóstico: `npm run release:audit:manual:auth:diagnose`
(`scripts/claude_auth_recovery.py`).
