# Matriz de promesas y evidencia 0.6.0

Esta matriz traduce los claims publicos de Alfred Dev a evidencia verificable.
Su objetivo es que "hace lo que promete" sea auditable antes de publicar, no
una impresion subjetiva despues de leer el README.

## Leyenda

- **Cubierto**: existe prueba automatica, smoke local o salida de CLI que
  demuestra el claim en la superficie actual.
- **Parcial**: hay contratos automaticos, pero falta conversacion real o
  integracion externa completa.
- **Pendiente externo**: requiere credenciales, autenticacion o un entorno que
  no se puede simular de forma honesta en este checkout.

| Promesa publica | Evidencia canonica | Estado |
|-----------------|--------------------|--------|
| La version publica se mantiene en `0.6.0` hasta publicar | `npm run release:audit`, `tests/test_version_consistency.py` | Cubierto |
| `plugin.json` es la fuente canónica de version y el marketplace no duplica `version`, evitando drift silencioso de release | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `tests/test_version_consistency.py`, `npm run release:audit` | Cubierto |
| Claude ve 19 agentes | `claude plugin details alfred-dev@alfred-dev`, `npm run release:audit` | Cubierto |
| Hay 10 agentes de nucleo y 9 opcionales | `agents/`, `agents/alfred.md`, `tests/test_personality.py`, `npm run release:audit` | Cubierto |
| Los agentes se cargan desde `agents/`, no desde `plugin.json` | `docs/architecture.md`, `tests/test_public_surface_contract.py`, `claude plugin details` | Cubierto |
| Los modelos y colores de agentes usan valores actuales de Claude Code y mantienen la política 0.6.0 de 7 `opus` y 12 `sonnet` | `agents/*.md`, `docs/personality.md`, `tests/test_public_surface_contract.py`, `npm run release:audit` | Cubierto |
| Las herramientas declaradas por agentes usan nombres oficiales de Claude Code o patrones MCP válidos | `agents/*.md`, `tests/test_public_surface_contract.py`, `npm run release:audit` | Cubierto |
| Los agentes de plugin no listan ni instruyen herramientas que Claude Code no entrega a subagentes (`AskUserQuestion`, plan mode, wakeups o espera MCP); las preguntas navegables quedan en comandos del hilo principal | `agents/*.md`, `tests/test_public_surface_contract.py`, `npm run release:audit` | Cubierto |
| Hay 62 skills publicados en 15 dominios | `.claude-plugin/plugin.json`, `find skills -name SKILL.md`, `npm run release:audit` | Cubierto |
| El catálogo de skills se publica por los 15 dominios explícitos cuando el marketplace apunta al root del plugin | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `npm run release:audit` | Cubierto |
| La UI de plugin muestra un nombre humano sin cambiar el namespace técnico | `displayName: "Alfred Dev"` en `.claude-plugin/plugin.json` y `.claude-plugin/marketplace.json`, `npm run release:audit` | Cubierto |
| Los `SKILL.md` usan frontmatter soportado por Claude Code, declaran `name`/`description`, no duplican nombres y cada `name` coincide con su directorio invocable | `skills/**/SKILL.md`, `tests/test_public_surface_contract.py`, `npm run release:audit` | Cubierto |
| Los valores de frontmatter de skills siguen el contrato actual de Claude Code: booleanos reales, `model` compatible, `effort` en `low/medium/high/xhigh/max`, `context: fork`, `shell` en `bash/powershell` y reglas `allowed-tools`/`disallowed-tools` con nombres oficiales o MCP | `skills/**/SKILL.md`, `tests/test_release_audit.py`, `tests/test_public_surface_contract.py`, `npm run release:audit` | Cubierto |
| Las señales de descubrimiento de skills no se truncan: `description + when_to_use` queda en 1.536 caracteres o menos, el límite oficial del listing de Claude Code | `skills/**/SKILL.md`, `tests/test_release_audit.py`, `tests/test_public_surface_contract.py`, `npm run release:audit` | Cubierto |
| Los skills delicados o con side effects quedan visibles pero forzados a activacion manual explicita | `skills/**/SKILL.md`, `tests/test_public_surface_contract.py`, `npm run release:audit` | Cubierto |
| Hay 26 rutas publicas: 25 comandos `/alfred-dev:*` y `/alfred` como skill personal global instalado sin shim personal duplicado | `.claude-plugin/plugin.json`, `skills/alfred/alfred/SKILL.md`, `install.sh`, `install.ps1`, `commands/help.md`, `docs/architecture.md`, `npm run release:audit` | Cubierto |
| El frontmatter de comandos usa solo campos soportados para comandos por Claude Code: `description`, `argument-hint` cuando hay `$ARGUMENTS`, `allowed-tools`, `disallowed-tools` y `model`; no acepta campos propios de `SKILL.md`, valida `model` contra alias/IDs actuales y las reglas de herramientas, inline o en lista YAML, usan nombres oficiales, `Skill(...)` o MCP | `commands/*.md`, `tests/test_release_audit.py`, `tests/test_public_surface_contract.py`, `npm run release:audit` | Cubierto |
| El protocolo compartido `_composicion.md` viaja en el paquete pero no se publica como comando de usuario | `commands/_composicion.md`, `.claude-plugin/plugin.json`, `npm run release:audit` | Cubierto |
| Los flujos que usan composición dinámica leen `_composicion.md` desde la instalación del plugin, no desde el proyecto auditado | `commands/{feature,fix,quick,spike,ship,audit}.md`, `npm run release:audit` | Cubierto |
| La matriz manual cubre las 26 rutas públicas | `npm run release:audit:manual -- --dry-run`, `tests/test_manual_smoke.py`, `npm run release:audit` | Cubierto |
| La matriz manual cubre las 40 opciones publicas documentadas, incluidas las secciones navegables de `/config`, scopes de Lucius y menús `AskUserQuestion` de permisos/gates; valida IDs `comando:opcion` contra comandos reales y exige que cada contrato lo cubra un caso cuyo prompt ejecuta ese mismo comando | `npm run release:audit:manual -- --dry-run`, `tests/test_manual_smoke.py`, `tests/test_release_audit.py`, `npm run release:audit` | Cubierto |
| La matriz runtime de `/update` cubre y valida los scopes `user`, `local`, `project` y `managed` | `scripts/manual_smoke.py`, `tests/test_manual_smoke.py`, `tests/test_release_audit.py`, `npm run release:audit` | Cubierto |
| `/alfred-dev:config` cubre preview y persistencia de sus 7 secciones | `tests/test_config_loader.py`, `npm run release:audit` | Cubierto |
| La detección automática de stack cubre los ecosistemas prometidos en README: Node/TypeScript, Python, Rust, Go, Ruby, Elixir, Java/Kotlin, PHP, C#/.NET y Swift | `core/config_loader.py`, `tests/test_config_loader.py`, fixtures de `npm run release:audit` | Cubierto |
| La fase de estilo visual con Selina es condicional: entra en proyectos con frontend, se salta en backend/API y mantiene gate de usuario | `core/orchestrator.py`, `tests/test_selina_orchestrator.py`, `npm run release:audit` | Cubierto |
| La composición dinámica decide agentes con señales reales y razonamiento semántico, no por matching de keywords aisladas | `commands/_composicion.md`, `README.md`, `docs/configuration.md`, `npm run release:audit` | Cubierto |
| Las quality gates son verificables por contrato local: tests rojos y seguridad KO bloquean; autopilot solo autoaprueba gates de usuario y no despliegue | `core/orchestrator.py`, `tests/test_orchestrator.py`, `npm run release:audit` | Cubierto |
| Autopilot se activa por configuración/estado, no por un flag público inexistente | `README.md`, `commands/{_composicion,feature,fix,ship}.md`, `site/src/i18n/*`, `npm run release:audit` | Cubierto |
| No quedan prompts runtime con comandos legacy `/alfred ...` | `npm run release:audit` check `claims` | Cubierto |
| Los contadores publicos no vuelven a 60 skills, 12 hooks o 9+8 agentes | `npm run release:audit` check `claims` | Cubierto |
| El core Python no se promete con un contador obsoleto: README y landing agrupan modulos por responsabilidad | `README.md`, `site/src/i18n/*`, `npm run release:audit` check `claims` | Cubierto |
| Lucius no promete un modelo obsoleto fijo | `agents/lucius.md`, `commands/help.md`, `site/src/i18n/*`, `npm run release:audit` | Cubierto |
| Hooks en formato actual `command` + `args` | `hooks/hooks.json`, `npm run release:audit` | Cubierto |
| Los hooks no declaran `matcher` en eventos donde Claude Code lo ignora silenciosamente (`Stop`, `UserPromptSubmit`, `PostToolBatch`, tareas/worktrees y similares); `UserPromptExpansion` queda cubierto sin matcher para registrar cualquier slash command expandido | `hooks/hooks.json`, `tests/test_release_audit.py`, `npm run release:audit` | Cubierto |
| Los hooks sincronos declaran timeout entero y no superan 10 segundos; los guards bloqueantes mantienen limite de 5 segundos | `hooks/hooks.json`, `tests/test_release_audit.py`, `npm run release:audit` | Cubierto |
| La documentación de hooks usa el contrato de salida actual (`decision`, `hookSpecificOutput.hookEventName`, `hookSpecificOutput.additionalContext`, `systemMessage`) | `docs/hooks.md`, `npm run release:audit` | Cubierto |
| Guards bloqueantes conservan `exit 2` | `npm run release:audit`, tests de hooks | Cubierto |
| Los hooks que bloquean con `exit 2` no emiten JSON por stdout que Claude Code ignoraría; las instrucciones de bloqueo viajan por stderr | `hooks/{dangerous-command-guard.py,prefetch-finish-guard.py,secret-guard.sh}`, `tests/test_*guard.py`, `npm run release:audit` | Cubierto |
| MCP de memoria se declara como plugin desde `.mcp.json` | `.mcp.json`, `claude mcp get plugin:alfred-dev:alfred-memory` | Cubierto |
| El duplicado project-scope de `.mcp.json` en desarrollo local esta explicado | `docs/installation.md`, `docs/release-audit-0.6.0.md` | Cubierto |
| El servidor MCP habla JSONL stdio moderno y mantiene compatibilidad de lectura heredada | `tests/test_memory_server.py`, `npm run release:audit:mcp` | Cubierto |
| Las 15 herramientas MCP ejecutan operaciones reales contra SQLite | `npm run release:audit:mcp` | Cubierto |
| Las tools MCP paginadas declaran límites defensivos y recortan peticiones abusivas para evitar salidas/cargas enormes | `tests/test_memory_server.py`, `npm run release:audit:mcp` | Cubierto |
| `memory_log_event` limita entradas libres, recorta `payload`/`content` MCP enormes y conserva metadatos de recorte | `tests/test_memory_server.py`, `tests/test_memory.py`, `npm run release:audit:mcp` | Cubierto |
| Las tools MCP que leen/escriben rutas (`memory_export`, `memory_import`) quedan acotadas al proyecto actual | `tests/test_memory_server.py`, `npm run release:audit:mcp` | Cubierto |
| La memoria persistente mantiene SQLite local, FTS5/fallback, export/import, sanitización de secretos y permisos `0600` | `tests/test_memory.py`, `tests/test_memory_server.py`, `npm run release:audit:mcp`, `npm run release:audit` | Cubierto |
| El paquete publicable no arrastra caches, sesiones locales, tests ni builds generados | `npm pack --dry-run --json`, `npm run release:audit` | Cubierto |
| Las 7 plantillas de artefactos viajan en el paquete y se comparan contra la cache instalada | `templates/*.md`, `npm pack --dry-run --json`, `npm run release:audit:full` | Cubierto |
| Los flujos principales tienen cierre canonico y gates documentadas | `commands/{feature,fix,quick,spike,ship,audit}.md`, `npm run release:audit` | Cubierto |
| Continuidad operativa: mapear, discutir, quick, pause, resume, status, progress, standup | `npm run release:audit:continuity` | Cubierto |
| SonIA operativo: blocked, in-progress, validate, search, sync-github fail-closed | `npm run release:audit:continuity`, `npm run release:audit:external` | Cubierto |
| Memory UI abre/reutiliza UI local y se puede cerrar sin dejar proceso suelto | `npm run release:audit:continuity` | Cubierto |
| UAT humana no se aprueba sin indicacion explicita | `commands/verify.md`, `tests/test_continuity.py`, `npm run release:audit:human` | Cubierto |
| Alfred no debe fingir tests, deploys ni auditorias sin evidencia | `commands/_composicion.md`, `agents/alfred.md`, `npm run release:audit:human` | Cubierto |
| AskUserQuestion se reserva para ambiguedad real o gates humanas y los helpers canónicos emiten `questions[]`/`multiSelect` actuales | `commands/*.md`, `core/config_loader.py`, `core/optional_agents.py`, `npm run release:audit:human`, `npm run release:audit` | Cubierto |
| Compliance europeo RGPD/NIS2/CRA, OWASP, threat model y SBOM están integrados en prompts, agente de seguridad, skills y plantillas; no sustituyen revisión legal humana | `agents/security-officer.md`, `skills/seguridad/compliance-check/SKILL.md`, `skills/seguridad/threat-model/SKILL.md`, `templates/{threat-model,sbom}.md`, `npm run release:audit` | Cubierto |
| Docker/SonarQube pide permiso y documenta omisiones | `commands/audit.md`, `site/src/i18n/*`, `npm run release:audit:external`, `npm run release:audit` | Cubierto |
| GitHub Sync mantiene GitHub como espejo, no fuente de verdad | `commands/sync-github.md`, `npm run release:audit:external` | Cubierto |
| Lucius es solo lectura, usa `codex exec --sandbox read-only --ephemeral --json --output-last-message`, compara estado Git y no sustituye sign-off de QA/seguridad/arquitectura | `agents/lucius.md`, `commands/lucius.md`, `npm run release:audit:external` | Cubierto |
| Deploy de `ship` nunca se autoaprueba | `commands/ship.md`, `npm run release:audit:external` | Cubierto |
| Paquete publicable sin secretos reales | `npm run release:audit` escanea `npm pack --dry-run --json` con `core/secrets.py` | Cubierto |
| La evidencia manual de release no filtra secretos en previews de respuesta, stderr ni artefactos | `scripts/manual_smoke.py`, `core/secrets.py`, `tests/test_manual_smoke.py`, `npm run release:audit` | Cubierto |
| La revisión humana no puede crear plantillas ni aprobar evidencia o notas humanas con secretos | `scripts/manual_review_gate.py`, `core/secrets.py`, `tests/test_manual_review_gate.py`, `npm run release:audit` | Cubierto |
| La evidencia manual y sus plantillas de revisión se escriben con permisos `0600` | `scripts/manual_smoke.py`, `scripts/manual_review_gate.py`, `tests/test_manual_smoke.py`, `tests/test_manual_review_gate.py`, `npm run release:audit` | Cubierto |
| La revisión humana queda ligada a la matriz actual: `review.cases` debe conservar `prompt`, `expected`, `setup`, `commands`, `suite`, `option_keys` y `runtime_keys` vigentes para cada caso | `scripts/manual_review_gate.py`, `tests/test_manual_review_gate.py`, `npm run release:audit` | Cubierto |
| Instaladores usan CLI nativa, materializan `/alfred` en `~/.claude/skills/alfred/SKILL.md`, eliminan el shim personal obsoleto `~/.claude/commands/alfred.md` y parchean Python compatible en hooks/MCP | `install.sh`, `install.ps1`, `tests/test_install_script.py` | Cubierto |
| `/alfred-dev:update` normaliza instalaciones `user`, `local`, `project` o desconocidas a instalación global de usuario; `managed` queda en manos del administrador | `commands/update.md`, `docs/installation.md`, matriz runtime de `scripts/manual_smoke.py`, `npm run release:audit` | Cubierto |
| Landing compila y refleja contadores actuales | `npm --prefix site run check`, `npm --prefix site run build`, `npm run release:audit` | Cubierto |
| Comportamiento humano real en conversacion con Claude CLI | `docs/manual-smoke-0.6.0.json` completo contra worktree actual (43/43 casos, `failed=0`, `blocked_auth=0`) + `docs/manual-smoke-installed-0.6.0.json` completo contra cache instalada actual (43/43 casos, `failed=0`, `blocked_auth=0`) + `docs/manual-smoke-installed-alfred-0.6.0.json` contra cache instalada actual para `/alfred`; revisiones `docs/manual-smoke-review-0.6.0.json` y `docs/manual-smoke-installed-review-0.6.0.json` quedan ligadas por `evidence_file`, `evidence_sha256`, `plugin_surface.roots`, `plugin_surface.file_count`, `plugin_surface.sha256`, metadatos de caso (`prompt`, `expected`, `setup`, `commands`, `suite`, `option_keys`, `runtime_keys`) y mapas `command_coverage`/`option_coverage`/`runtime_coverage` contra la matriz actual; reportes asistidos ayudan a leer flags de riesgo, superficie stale y notas humanas debiles sin aprobar nada | Parcial: auth recuperada y matrices worktree/instalada completas actuales; falta revisión humana explicita |

Nota de cierre: el bloqueo anterior "falta matriz instalada completa actual"
queda cerrado por `docs/manual-smoke-installed-0.6.0.json`; lo pendiente ya no
es falta de ejecución, sino revisión humana explicita e integraciones externas
reales.
| Sync GitHub contra repo real con `gh` autenticado | `docs/external-live-smoke-0.6.0.json`: `mode=live`, `github_status=ok`, `write_attempted=true`, `synced_tasks=1`, `board_issue=https://github.com/686f6c61/alfred-dev/issues/7`, `retired=0`, `remote_drift=0` | Cubierto |
| SonarQube real con Docker operativo | `docs/external-live-smoke-sonarqube-0.6.0.json`: `status=ok`, SonarQube `26.6.0.123539`, `system_status=UP`, scanner `EXECUTION SUCCESS`, Quality Gate `OK`, `bugs=0`, `vulnerabilities=0`, `security_hotspots=0`, `code_smells=1`, token temporal revocado, fixture temporal borrado y contenedor eliminado | Cubierto |
| Lucius real contra Codex CLI autenticado | `docs/external-live-smoke-0.6.0.json`: `codex_status=ok`, `live_attempted=true`, `codex exec --sandbox read-only --ephemeral --json --output-last-message`, `final_message_preview=OK_ALFRED_CODEX_EXTERNAL_060` | Cubierto |

## Referencias de alineacion

- Claude Code plugins, skills, hooks y MCP: ver `docs/release-audit-0.6.0.md`
  para las referencias oficiales usadas y los checks que las ejercitan.
- Codex CLI: Lucius no fija un modelo en sus prompts. Codex CLI debe usar la
  configuracion local del usuario o el modelo recomendado por su version
  instalada. El flujo no interactivo usa JSONL para trazabilidad tecnica y
  `--output-last-message` como fuente primaria del informe humano.

## Estado actual

La base tecnica de 0.6.0 queda cubierta por pruebas, smokes locales, matrices
headless reales con Claude CLI y tres pruebas externas vivas. El preflight de autenticacion ya esta en `ok` con Claude Code `2.1.183`;
`docs/manual-smoke-0.6.0.json` conserva la matriz worktree actual con 43/43
casos ejecutados, `failed=0` y `blocked_auth=0`;
`docs/manual-smoke-installed-0.6.0.json` conserva la matriz instalada actual con
43/43 casos ejecutados, `failed=0` y `blocked_auth=0`;
`docs/manual-smoke-installed-alfred-0.6.0.json` demuestra que el alias global
`/alfred` funciona desde la cache instalada actual;
`docs/external-live-smoke-0.6.0.json` demuestra GitHub Sync real y Codex real; y
`docs/external-live-smoke-sonarqube-0.6.0.json` demuestra SonarQube real con
Docker y scanner.
La publicacion sigue sin poder cerrarse honestamente hasta que una
persona revise las respuestas finales y apruebe explicitamente
`docs/manual-smoke-review-0.6.0.json` y la revision instalada correspondiente.
El gate final `npm run release:audit:prepublish` valida hashes y revisiones sin
regenerar la evidencia. Los reportes asistidos Markdown ayudan a leer, pero no
sustituyen `approved=true` ni las notas humanas.
