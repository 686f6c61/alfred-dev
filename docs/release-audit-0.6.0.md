# Auditoria de release 0.6.0

Este documento es la matriz viva para publicar Alfred Dev 0.6.0. La meta no es
solo que el plugin valide: cada claim publico debe estar alineado con Claude
Code actual, tener evidencia reproducible y comportarse de forma humana en un
proyecto real.

La matriz complementaria [promise-evidence-0.6.0.md](promise-evidence-0.6.0.md)
traduce las promesas públicas a evidencia canónica y separa lo cubierto de lo
que sigue pendiente por depender de autenticación o servicios externos.
El resumen ejecutivo [release-readiness-0.6.0.md](release-readiness-0.6.0.md)
mantiene la decisión de salida: técnicamente preparado para revisión final,
pero no aprobado para publicación hasta completar revisión humana y pendientes
externos.
La revisión humana caso por caso se ejecuta con
[manual-review-0.6.0.md](manual-review-0.6.0.md), que define criterio de
aprobación, bloqueos obligatorios y comandos finales sin sustituir el gate.

## Referencias oficiales usadas

- Claude Code plugins reference (`https://code.claude.com/docs/en/plugins-reference`):
  estructura de plugin, agentes en `agents/`,
  soporte de MCP desde `.mcp.json`, versionado y errores comunes.
- Claude Code plugin marketplaces
  (`https://code.claude.com/docs/en/plugin-marketplaces`): la version puede
  resolverse desde `plugin.json`, marketplace o SHA; evitar duplicarla en
  manifest y marketplace impide que un valor stale quede enmascarado.
- Claude Code discover/install plugins
  (`https://code.claude.com/docs/en/discover-plugins`): `claude plugin
  details` y `/plugin` muestran el inventario real; tras instalar, habilitar o
  deshabilitar plugins, `/reload-plugins` aplica cambios sin reiniciar salvo
  aviso de coste/caché de MCP, donde `/reload-plugins --force` es explícito.
- Claude Code MCP docs (`https://code.claude.com/docs/en/mcp`): `.mcp.json`,
  scopes, precedencia, aprobacion de MCP de proyecto y expansion de variables
  de entorno.
- Claude Code subagents docs (`https://code.claude.com/docs/en/sub-agents`):
  los agentes de plugin no deben depender de `hooks`, `mcpServers` ni
  `permissionMode`, porque Claude ignora esos campos en ese scope.
- Claude Code tools reference (`https://code.claude.com/docs/en/tools-reference`):
  `Agent` es la herramienta actual para lanzar subagentes; `Task` queda como
  nomenclatura obsoleta en esta superficie.
- Claude Code Handle approvals and user input
  (`https://code.claude.com/docs/en/agent-sdk/user-input`): `AskUserQuestion`
  debe usarse cuando hay varias rutas válidas y necesita opciones
  seleccionables, no como texto plano ambiguo. Los payloads canónicos usan
  `questions[]` y `multiSelect` conforme a la referencia actual del SDK.
- Claude Code best practices (`https://code.claude.com/docs/en/best-practices`):
  para trabajo grande conviene dejar que Claude entreviste con
  `AskUserQuestion`, cubrir trade-offs y terminar con verificación end-to-end.
- Claude Code error reference (`https://code.claude.com/docs/en/errors`) y
  authentication docs (`https://code.claude.com/docs/en/authentication`): los errores
  OAuth `401` requieren revisar precedencia de credenciales, refrescar login o
  usar `claude setup-token` para scripts; versiones previas a `2.1.174` tenian
  fixes relevantes para auth headless/background.
- Claude Code troubleshoot installation and login
  (`https://code.claude.com/docs/en/troubleshoot-install`): si el login falla
  o el token caduca, la ruta oficial incluye reautenticacion limpia,
  `claude doctor` y, en macOS, revisar Keychain cuando las credenciales no se
  guardan o no persisten.
- Claude Code skills docs (`https://code.claude.com/docs/en/skills`): cambios
  en `hooks/`, `.mcp.json` y `agents/` requieren recargar plugins.
- Claude Code commands docs (`https://code.claude.com/docs/en/commands`) y
  Agent SDK slash commands
  (`https://code.claude.com/docs/en/agent-sdk/slash-commands`): los comandos
  custom siguen siendo Markdown, pero su frontmatter operativo es mas estrecho
  que el de `SKILL.md`.
- Claude Code hooks reference (`https://code.claude.com/docs/en/hooks`): los
  hooks de comando pueden usar `args` para evitar tokenizacion shell, y los
  bloqueos por `exit 2` solo funcionan si no se neutraliza el codigo de salida.
- Claude Code plugins reference (`https://code.claude.com/docs/en/plugins-reference`):
  `${CLAUDE_PLUGIN_ROOT}` apunta a una instalación versionada y efímera; los
  artefactos persistentes deben vivir fuera de esa cache.
- OpenAI Codex non-interactive mode
  (`https://developers.openai.com/codex/noninteractive`) y Codex CLI reference
  (`https://developers.openai.com/codex/cli/reference`): `codex exec` es la
  interfaz documentada para ejecuciones no interactivas, el modo read-only es
  el punto de partida seguro, `--ephemeral` evita persistir la sesión y
  `--full-auto` queda como compatibilidad deprecada.

## Revalidacion oficial 2026-06-20

Contraste realizado el 2026-06-20 contra documentación oficial vigente de
Claude Code y OpenAI Codex. Resultado: sin drift documental detectado para los
contratos de Alfred Dev 0.6.0.
La referencia actual de plugins tambien documenta componentes no usados por
Alfred Dev en esta release: LSP servers, monitors y themes. No forman parte de
las promesas publicas de 0.6.0 y quedan bloqueados por `release:audit` si se
declaran sin gate, pruebas y documentacion dedicadas.

Superficie actual del plugin tras refrescar el README público con la sección
del equipo y mantener `/alfred` como skill personal global sin shim de comando
duplicado:
`plugin_surface.sha256=0ec656f2c4bbc1c329d8df142b868a02f272bc68c5d0985696cd98996eb7cd68`.
La autenticacion de `claude -p` se recupero el 2026-06-20 con relogin
interactivo. Tras el ajuste documental del README, las matrices worktree,
instalada y el smoke critico de `/alfred` deben regenerarse contra esta
superficie antes de aprobar la publicación final; las revisiones humanas siguen
pendientes de forma explícita.
Nota posterior: las evidencias manuales citadas más abajo que conservan
`plugin_surface.sha256=fb72f4beec3ccba3c35fa2291e1f3b03d80542f3e8a5f5b7f083569c7e5f3de8`
siguen siendo evidencia funcional previa al ajuste documental del README, pero
deben regenerarse antes de aprobar `release:audit:prepublish`.

| Superficie | Fuente oficial | Contrato verificado en Alfred Dev |
|------------|----------------|-----------------------------------|
| Comandos de plugin | Claude Code plugins reference + skills docs | Claude Code actual describe `commands/` como skills planas soportadas y recomienda `skills/` para plugins nuevos. Alfred Dev mantiene 25 slash commands namespaced en `commands/` para preservar la UX pública `/alfred-dev:*`, mientras `/alfred` se materializa como skill personal global en `~/.claude/skills/alfred/SKILL.md`; cualquier shim personal obsoleto en `~/.claude/commands/alfred.md` se elimina para no duplicar el selector. `plugin.json` enumera solo los 25 comandos namespaced. `commands/_composicion.md` y `commands/alfred.md` quedan empaquetados como recursos internos compartidos; no forman parte de esa lista pública y los flujos los cargan desde la instalación del plugin, no desde el proyecto auditado. |
| Metadatos de plugin | Claude Code plugins reference + marketplace docs | `plugin.json` y `marketplace.json` declaran `displayName: "Alfred Dev"` para que la UI muestre un nombre humano sin cambiar el namespace técnico `alfred-dev`; `plugin.json` es la fuente canónica de `version` y el marketplace no duplica ese campo, evitando drift silencioso; el marketplace conserva `source: "./"` como ruta relativa al root del marketplace, no a `.claude-plugin/`, y la documentación de instalación usa fuente GitHub para que esa ruta relativa sea resoluble. |
| Frontmatter de comandos | Claude Code commands docs + Agent SDK slash commands docs + tools reference | Cada comando público mantiene frontmatter estricto con campos soportados para comandos (`description`, `argument-hint`, `allowed-tools`, `disallowed-tools`, `model`); los comandos con argumentos emparejan `argument-hint` con `$ARGUMENTS`, `model` se valida contra alias/IDs actuales de Claude Code, y `release:audit` valida que `allowed-tools`/`disallowed-tools`, tanto inline como en lista YAML, solo usen nombres oficiales de herramientas, `Skill(...)` o patrones MCP. |
| Skills de plugin | Claude Code plugins reference + skills docs | El marketplace local apunta al root del plugin (`source: "./"`) y `plugin.json` enumera explícitamente los 15 dominios de `skills/`, evitando que el catálogo publicado dependa de inferencias o de una ruta genérica. Cada `SKILL.md` usa frontmatter soportado por Claude Code, declara `name`/`description`, mantiene nombres únicos y hace coincidir `name` con el directorio invocable. No se permiten colisiones entre skills y comandos publicados: `skills/alfred/alfred` es la fuente oculta (`user-invocable: false`) del alias que el instalador copia como skill personal global `/alfred` materializado con `user-invocable: true`, y `commands/alfred.md` queda como contrato interno no registrado. Además, `release:audit` valida valores de skill documentados: booleanos (`disable-model-invocation`, `user-invocable`), `model`, `effort`, `context`, `shell` y reglas `allowed-tools`/`disallowed-tools`; también exige que `description + when_to_use` no supere el límite oficial de listing de 1.536 caracteres para que Claude no pierda señales de invocación por truncado. |
| Agentes de plugin | Claude Code plugins reference + subagents docs + tools reference | Los agentes viven en `agents/`, no en `plugin.json`; el frontmatter evita campos ignorados en agentes de plugin como `hooks`, `mcpServers` y `permissionMode`, valida `model` contra los alias/IDs actuales de Claude Code, valida `color` contra los valores soportados, valida `tools` contra nombres oficiales o patrones MCP, excluye herramientas no disponibles en subagentes como `AskUserQuestion` y conserva la política 0.6.0 de 7 `opus` y 12 `sonnet`. |
| Skills manual-only | Claude Code skills docs | Los skills pesados o con side effects claros siguen publicados, pero `release:audit` exige `disable-model-invocation: true` en `style-direction`, `incident-response`, `sonarqube`, `release-planning`, `pr-workflow`, `release` y `repo-setup`. |
| MCP de plugin | Claude Code plugins reference + MCP docs | `alfred-memory` vive en `.mcp.json`, usa lanzador portable con `CLAUDE_PLUGIN_ROOT` y fallback `cwd`, y conecta como `plugin:alfred-dev:alfred-memory`. |
| Estado persistente | Claude Code plugins reference | La cache versionada del plugin no guarda estado. Alfred usa `.claude/alfred-memory.db` porque la memoria es por proyecto; `CLAUDE_PLUGIN_DATA` queda reservado para dependencias/caches del plugin que deban sobrevivir a updates. |
| Límites MCP | Claude Code MCP docs | Las tools paginadas de memoria declaran máximos y recortan `limit` abusivos; `memory_log_event` limita identificadores y recorta `summary`, `content` y `payload` enormes. |
| Duplicado local MCP | Claude Code MCP docs | Una entrada project-scope leida desde `.mcp.json` puede quedar `Pending approval`; no invalida la entrada de plugin conectada. |
| LSP, monitors y themes | Claude Code plugins reference | No se publican en 0.6.0. `release:audit` falla si aparecen `lspServers`, `experimental.monitors`, `experimental.themes` o componentes equivalentes sin una gate de release especifica, porque introducirian procesos o integraciones nuevas fuera de la evidencia actual. |
| Scopes de instalación | Claude Code plugins reference | El instalador público usa `--scope user`; antes limpia rastros heredados `local`/`project` del mismo plugin en el contexto actual y deja la instalación normal como global de usuario. `/alfred-dev:update` normaliza `user`, `local`, `project` o desconocido a `--scope user`; solo `managed` queda fuera por política de administrador. |
| Hooks | Claude Code hooks reference | `hooks.json` usa exec form con `args` cuando hay rutas de plugin, conserva bloqueos con `exit 2` sin emitir JSON que Claude Code ignoraría, evita declarar `matcher` en eventos donde Claude Code lo ignora silenciosamente, cubre `UserPromptExpansion` para slash commands directos, no usa `if` fuera de eventos de herramienta, exige timeout entero y <= 10 s para hooks sincronos, y la documentación enseña el output actual: `decision`, `hookSpecificOutput.hookEventName`, `hookSpecificOutput.additionalContext` y `systemMessage`. |
| Preguntas humanas | Claude Code tools reference + Handle approvals and user input | `AskUserQuestion` queda reservado para ambigüedad real, gates humanas y configuración con opciones navegables; los helpers canónicos emiten `questions[]` y `multiSelect: false`. |
| Verificación | Claude Code best practices | Los comandos no declaran éxito sin evidencia legible: tests, build, salida de herramienta, artefacto o confirmación humana explícita. |
| Lucius/Codex | OpenAI Codex non-interactive mode + CLI reference | Lucius usa `codex exec --sandbox read-only --ephemeral --json --output-last-message`, captura JSONL técnico, lee el informe humano desde el último mensaje y fija `approval_policy='never'` por configuración para ejecuciones no interactivas. |

## Criterios de salida

| Area | Requisito | Evidencia requerida | Estado |
|------|-----------|---------------------|--------|
| Versionado | Toda la superficie publica y runtime declaran `0.6.0` desde `plugin.json`; el marketplace no duplica `version` porque Claude Code prioriza el manifest del plugin | `tests/test_version_consistency.py`, busqueda sin restos vivos de la version intermedia anterior | Cubierto por tests |
| Auditoria automatica | Existe un verificador local reproducible para los contratos de release | `npm run release:audit` | Cubierto por script |
| Catálogo público | `plugin.json`, `/alfred-dev:help` y `docs/architecture.md` describen los mismos 25 comandos namespaced sin duplicados y documentan `/alfred` como skill personal global instalado sin shim personal duplicado; `_composicion.md` y `commands/alfred.md` quedan como recursos internos empaquetados; el frontmatter de comandos usa solo los campos soportados para comandos y reglas `allowed-tools`/`disallowed-tools` con nombres oficiales de herramientas | `npm run release:audit` | Cubierto por script |
| Claims públicos | README, arquitectura, landing, help, agentes y skills manual-only no tienen contadores antiguos, inventarios core congelados ni modelos obsoletos fijados | `npm run release:audit` | Cubierto por script |
| Configuración | `/alfred-dev:config` expone las 7 secciones reales del runtime con menú, preview, round-trip de persistencia y helpers canónicos | `npm run release:audit` + `tests/test_config_loader.py` | Cubierto por script |
| Detección de stack | Los ecosistemas prometidos en README se detectan con fixtures reales: Node/TypeScript, Python, Rust, Go, Ruby, Elixir, Java/Kotlin, PHP, C#/.NET y Swift | `npm run release:audit` + `tests/test_config_loader.py` | Cubierto por script |
| Selina condicional | La fase `estilo_visual` existe solo en `feature`, usa Selina, se ejecuta con frontend y se registra como saltada en backend/API | `npm run release:audit` + `tests/test_selina_orchestrator.py` | Cubierto por script |
| Quality gates | Tests rojos, seguridad KO y despliegue en autopilot bloquean según contrato; autopilot solo autoaprueba gates de usuario no forzadas | `npm run release:audit` + `tests/test_orchestrator.py` | Cubierto por script |
| Ejecución de comandos | Los 25 comandos namespaced y `/alfred` preservan argumentos, helper-first cuando aplica, cierre canónico de flujos y contratos interactivos; los flujos cargan `_composicion.md` desde la instalación del plugin | `npm run release:audit` | Cubierto por script |
| Autopilot | La superficie pública no anuncia flags inexistentes; autopilot se activa por configuración/estado y acepta estado canónico + alias legacy | `npm run release:audit` | Cubierto por script |
| Inventario Claude | Claude ve 62 skills, 19 agents, 7 grupos de hooks y 1 MCP | `claude plugin details alfred-dev@alfred-dev` | Cubierto por smoke local |
| Manifest | `.claude-plugin/plugin.json` no declara `agents` ni `mcpServers` | `tests/test_public_surface_contract.py` | Cubierto por tests |
| Agentes | Los 19 agentes estan en `agents/` raiz, usan frontmatter soportado sin campos ignorados por plugins y mantienen modelos y colores compatibles con Claude Code actual bajo la política 7 `opus` / 12 `sonnet` | `npm run release:audit` + tests de contrato | Cubierto por script |
| Skills | Los 62 skills usan campos y valores de frontmatter compatibles con Claude Code actual: booleanos reales, modelos/effort/context/shell documentados, reglas de herramientas con nombres oficiales o MCP, y descripciones dentro del límite de listing de 1.536 caracteres | `npm run release:audit` + `tests/test_public_surface_contract.py` | Cubierto por script |
| Nomenclatura | Comandos, agentes y docs usan `Agent` para subagentes | `rg "\bTask\b"` revisado por contexto | Cubierto por auditoria textual |
| Hooks | `hooks.json` usa exec form con `args`, todos los scripts declarados existen y cubren los 13 hooks visibles, conserva `exit 2` en guards bloqueantes sin stdout JSON ignorado, no declara matchers ignorados por el evento, mantiene timeout sincronico entero <= 10 s y el wrapper helper-first no queda atado a una cache rotada | `npm run release:audit` + `tests/test_session_start_hook.py` | Cubierto por script |
| MCP plugin | `alfred-memory` se declara en `.mcp.json` raiz y conecta como plugin | `claude mcp get plugin:alfred-dev:alfred-memory` | Cubierto por smoke local |
| MCP transporte | El servidor responde al transporte stdio MCP moderno | probe con SDK MCP y `tests/test_memory_server.py` | Cubierto por tests |
| MCP límites | Las tools paginadas declaran máximos y recortan límites abusivos | `npm run release:audit:mcp` + `tests/test_memory_server.py` | Cubierto por smoke MCP |
| MCP rutas | Las tools de import/export no leen ni escriben fuera del proyecto actual | `npm run release:audit:mcp` + `tests/test_memory_server.py` | Cubierto por smoke MCP |
| Desarrollo local | El duplicado project-scope de `.mcp.json` dentro del repo esta explicado | `docs/installation.md` | Cubierto por docs |
| Empaquetado | `npm pack --dry-run --json` incluye comandos, agentes, skills, las 7 plantillas de artefactos y solo artefactos del plugin; excluye caches, `.claude/`, `.crupier/`, evidencias manuales, tests y builds locales | `npm run release:audit` | Cubierto por script |
| Instaladores | Bash y PowerShell instalan via CLI de Claude y parchean Python compatible | `tests/test_install_script.py`, `bash -n install.sh` | Cubierto por tests |
| Sitio | Landing compila y muestra version y claims coherentes | `npm --prefix site run check && npm --prefix site run build` | Cubierto por smoke local |
| Memoria | Las 15 herramientas MCP listan, validan schema y ejecutan operaciones base | `npm run release:audit:mcp` + tests unitarios | Cubierto por smoke MCP |
| Flujos | `feature`, `fix`, `quick`, `spike`, `ship`, `audit` siguen sus fases y gates | tests de continuidad/orquestador + prueba en proyecto fixture | Parcial; contratos de cierre de los 6 flujos cubiertos, conversación real pendiente |
| Comandos operativos | `next`, `status`, `pause`, `resume`, `verify`, `validate`, `sync-github`, `update` devuelven salida humana y no duplican resumen | tests de continuidad + smoke CLI en fixture | Parcial; helpers principales, argumentos y contratos interactivos cubiertos |
| Humanidad | Alfred pregunta cuando hay incertidumbre, no finge pruebas, deja gates claras y registra UAT | `npm run release:audit:human` + runbook manual con prompts representativos | Parcial; contratos automáticos cubiertos, falta conversación real |
| Seguridad | Guards de secretos, comandos peligrosos, lecturas sensibles, SonarQube con permiso explicito, Lucius con `codex exec --sandbox read-only` y diff-check Git, y evidencia de tests bloquean lo que prometen | tests de hooks + `npm run release:audit:external` | Parcial; falta sesion manual completa |
| Publicacion | Instalar desde marketplace GitHub deja cache, version e inventario correctos | uninstall/install local + `release:audit:full` + `claude plugin list/details/mcp get` | Cubierto por smoke local |

## Smoke terminal canonico

Ejecutar antes de publicar:

Si `claude plugin list` muestra `alfred-dev@alfred-dev` en una version remota
anterior, registrar este worktree como fuente global de usuario y refrescar la
instalacion global antes del smoke de Claude:

```bash
claude plugin marketplace remove alfred-dev --scope user
claude plugin marketplace add "$PWD" --scope user
claude plugin uninstall alfred-dev@alfred-dev --scope user
claude plugin install alfred-dev@alfred-dev --scope user
mkdir -p "$HOME/.claude/skills/alfred"
cp "$PWD/skills/alfred/alfred/SKILL.md" "$HOME/.claude/skills/alfred/SKILL.md"
python3 -c "from pathlib import Path; p=Path.home()/'.claude/skills/alfred/SKILL.md'; s=p.read_text(); p.write_text(s.replace('user-invocable: false','user-invocable: true',1))"
rm -f "$HOME/.claude/commands/alfred.md"
```

La retirada previa evita que `claude plugin details` lea una copia GitHub stale
del marketplace aunque `claude plugin list` ya muestre una caché local nueva.
`npm run release:audit:full` tambien compara la cache instalada con el worktree
en superficies criticas (plugin metadata, agentes, comandos, core, hooks, MCP, skills y templates)
antes de aceptar el smoke de Claude.

```bash
claude plugin validate . --strict
npm run release:audit:prepublish:prepare
npm run release:audit:prepublish
npm run release:audit
npm run release:audit:continuity
npm run release:audit:mcp
npm run release:audit:external
npm run release:audit:external:preflight
npm run release:audit:claude:commands
npm run release:audit:human
npm run release:audit:manual:preflight
npm run release:audit:manual:evidence
npm run release:audit:manual:evidence:installed
npm run release:audit:manual:report
npm run release:audit:manual:report:installed
npm run release:audit:manual:review
npm run release:audit:manual:review:installed
claude plugin details alfred-dev@alfred-dev
claude mcp get plugin:alfred-dev:alfred-memory
python3 -m pytest tests/ -q
npm --prefix site run check
npm --prefix site run build
bash -n install.sh
git diff --check
```

Para el servidor MCP, ademas del health-check de Claude, ejecutar un probe SDK
que use exactamente `.mcp.json` y confirme:

- `tools.length == 15`
- primera herramienta `memory_search`
- `stderr` vacio al arrancar

## Ultima verificacion local

Fecha: 2026-06-20.

```text
claude plugin validate . --strict
Resultado: ✔ Validation passed

npm run release:audit
Resultado: release-audit 0.6.0 ok; incluye catálogo de 25 comandos namespaced alineado entre plugin.json, help y arquitectura, `/alfred` documentado como skill personal global invocable, frontmatter de agentes compatible con plugins, modelos y colores de agentes validados contra Claude Code actual y política 7 opus/12 sonnet, contratos de ejecución de comandos, autopilot por configuración/estado sin flag público fantasma, claims públicos 19/62/26 rutas/13, configuración con 7 secciones canónicas y round-trip de persistencia, empaquetado seco sin artefactos locales, alias `/alfred` auditado como skill personal global, hooks en exec form y guards bloqueantes con exit 2.
Tambien escanea el paquete publicable de `npm pack --dry-run --json` con los
patrones canónicos de `core/secrets.py` para confirmar que no se publican
secretos reales ni artefactos generados como `.crupier/`.

npm run release:audit:continuity
Resultado: next/map-codebase/discuss/quick, status/pause/resume/progress/standup, blocked/in-progress/validate/search/verify, write-handoff/allow-stop-once/consume-prefetch/normalize-kanban/memory-ui/sync-github-fail-closed ok en fixture temporal

npm run release:audit:mcp
Resultado: 15 tools listadas, 15 tools invocadas con datos reales, SQLite temporal saludable

npm run release:audit:external
Resultado: Docker/SonarQube pide permiso y documenta omisiones; sync-github mantiene GitHub como espejo seguro; Lucius confirma coste y no modifica ficheros; ship mantiene deploy con gate humana.

npm run release:audit:external:preflight
Resultado esperado: genera `docs/external-live-smoke-0.6.0.json` con permisos
`0600` y estado exacto de `gh`, Docker/SonarQube y Codex CLI sin escribir en
GitHub, sin arrancar SonarQube y sin ejecutar Codex. Las pruebas reales con
efectos externos quedan tras flags explicitos de `scripts/external_live_smoke.py`.

npm run release:audit:human
Resultado: AskUserQuestion queda limitado a ambigüedad real y gates humanas; los helpers canónicos usan `questions[]`/`multiSelect`; helpers operativos no duplican salida; UAT exige indicación humana explícita; antifingimiento centralizado.

npm run release:audit:manual:evidence
Resultado actual: `docs/manual-smoke-0.6.0.json` completo contra el worktree;
`auth_preflight.status=ok`, Claude Code `2.1.183`, `run_status=complete`,
43/43 casos ejecutados, `failed=0`, `blocked_auth=0`,
`plugin_surface.sha256=fb72f4beec3ccba3c35fa2291e1f3b03d80542f3e8a5f5b7f083569c7e5f3de8`,
`evidence_sha256=63cbc3822ac4c4bdb56699427db7fdeefd2fb36a9b4de04a7e6865aad6262008`
y coste observado `$33.2240255`.

npm run release:audit:manual:evidence:installed
Resultado actual: `docs/manual-smoke-installed-0.6.0.json` completo contra
la cache instalada global de usuario; `auth_preflight.status=ok`, Claude Code
`2.1.183`, `run_status=complete`, 43/43 casos ejecutados, `failed=0`,
`blocked_auth=0`,
`plugin_surface.sha256=fb72f4beec3ccba3c35fa2291e1f3b03d80542f3e8a5f5b7f083569c7e5f3de8`,
`evidence_sha256=778add69bebd84e7bf6fbd79be045ed6dc5d60ccf1d738da1c89bfc2c3a6a9b8`
y coste observado `$32.414956`.

Historial sustituido: las evidencias anteriores
`evidence_sha256=1acb7d9937862acf9470c2df0cf22f2aa18478c8fe6818490ee91b85007461e7`
y
`evidence_sha256=c96d9895b9c76125a3b04fa653976c351a2b9cee4c1d7f46f305aefd077bd292`
quedan como rastro de ejecuciones previas y no como evidencia vigente.

python3 scripts/manual_smoke.py --installed --auth-preflight --case alfred-route --output docs/manual-smoke-installed-alfred-0.6.0.json
Resultado actual: cache instalada global de usuario, `auth_preflight.status=ok`,
`run_status=complete`, `/alfred` ejecutado con `returncode=0`, `failed=0`,
`blocked_auth=0`,
`plugin_surface.sha256=fb72f4beec3ccba3c35fa2291e1f3b03d80542f3e8a5f5b7f083569c7e5f3de8`,
`evidence_sha256=b63b82d537ab4c66a2be33d718dd53d6c3279f10ad1839665cf8c81a480b7092`
y coste observado `$1.1070825`.

npm run release:audit:manual:report
Resultado: `docs/manual-smoke-report-0.6.0.md` generado como reporte asistido
de revision del worktree; no aprueba la release ni modifica la plantilla. El
reporte marca `plugin_surface.roots`, `plugin_surface.file_count` y
`plugin_surface.sha256` si la evidencia ya no coincide con el plugin actual.

npm run release:audit:manual:report:installed
Resultado: `docs/manual-smoke-installed-report-0.6.0.md` generado como reporte
asistido de revision de la cache instalada; no aprueba la release ni modifica
la plantilla. El reporte marca `plugin_surface.roots`,
`plugin_surface.file_count` y `plugin_surface.sha256` si la evidencia ya no
coincide con la cache instalada actual.

Actualizacion de autenticacion del 2026-06-20T10:13:08Z:

```bash
npm run release:audit:manual:preflight:diagnose
npm run release:audit:manual:auth:diagnose
claude auth logout
claude auth login
npm run release:audit:manual:preflight
```

Resultado: el bloqueo `first_party_oauth_token_rejected`/401 queda resuelto tras
`claude auth logout` + `claude auth login` en terminal interactiva. El preflight
actual devuelve `auth_preflight.status=ok`, `api_error_status=null`,
`response_preview=OK`, Claude Code `2.1.183`, `authMethod=claude.ai`,
`apiProvider=firstParty` y `subscriptionType=max`.
El intento directo con `--max-budget-usd 0.01` ya no falla por auth: llega a
inferencia real y termina con `error_max_budget_usd`. La nota historica se
mantiene porque explica la recuperacion: `--bare` no era prueba valida de OAuth,
`claude doctor` no emitia salida visible en este entorno y el debug saneado habia
confirmado 401 antes de consumir tokens.
La guia reproducible para diagnosticar una futura recaida queda en
`scripts/claude_auth_recovery.py`; no escribe credenciales y puede emitir un
reporte local privado ignorado por git/npm.

npm run release:audit:manual:review:init
Resultado: `docs/manual-smoke-review-0.6.0.json` creado para revision humana
del worktree. Pendiente rellenar `reviewer`, `reviewed_at`, `approved=true` y
`cases.*.approved=true` con notas humanas no vacias tras revisar la evidencia.

npm run release:audit:manual:review:installed:init
Resultado: `docs/manual-smoke-installed-review-0.6.0.json` creado para
revision humana de la cache instalada. Pendiente la misma aprobacion humana
explicita.

npm run release:audit:manual -- --dry-run
Resultado: plugin_source=worktree; public_commands=26, covered_commands=26, missing_commands=none; public_options=40, covered_options=40, missing_options=none; runtime_contracts=4, covered_runtime_contracts=4, missing_runtime_contracts=none

npm run release:audit:manual -- --case alfred-route
Resultado: case `alfred-route` ejecutado correctamente; `/alfred` enruta desde
el alias global hacia la continuidad operativa y la evidencia JSON conserva
command_coverage para las 26 rutas publicas y option_coverage para las opciones
publicas.

codex --version && codex exec --sandbox read-only --ephemeral --help
Resultado: codex-cli 0.137.0; `codex exec` acepta `--sandbox read-only` y
`--ephemeral`, y el help documenta `--json` y `--output-last-message` para
automatización trazable. En esta versión `--ask-for-approval` no es flag
directo de `codex exec`, así que Lucius fija `approval_policy='never'`
mediante `-c`.

npm run release:audit:full
Resultado: release-audit 0.6.0 ok; incluye frontmatter de agentes compatible con plugins, modelos y colores de agentes validados contra Claude Code actual y política 7 opus/12 sonnet, claims públicos, configuración canónica, Lucius con Codex exec read-only, cache instalada alineada con worktree incluido templates, Claude CLI, continuidad, MCP tools, contratos externos, contratos humanos, site, pytest completo y checks de sintaxis/json/diff.

npm run release:audit:claude:commands
Resultado: Claude arranca en PTY real, se escribe `/alfred` en el selector
interactivo y confirma `/alfred` visible, comandos `/alfred-dev:*` visibles y
ausencia de `No commands match`.

claude plugin details alfred-dev@alfred-dev
Resultado: Alfred Dev (alfred-dev) 0.6.0, 62 skills, 19 agents, 7 grupos de hooks, 1 MCP

claude plugin list
Resultado: alfred-dev@alfred-dev, Version: 0.6.0, Scope: user, Status: enabled

claude mcp get plugin:alfred-dev:alfred-memory
Resultado: Status: ✔ Connected

claude mcp list
Resultado: `plugin:alfred-dev:alfred-memory` aparece conectado; la entrada
project-scope `alfred-memory` aparece `Pending approval` por ejecutar desde la
raíz del repo que contiene `.mcp.json`.

SDK MCP probe usando .mcp.json
Resultado: ok=true, tools=15, first=memory_search, stderr=""

python3 -m pytest tests/ -q
Resultado: 1274 passed, 15 subtests passed

npm --prefix site run check
Resultado: 0 errors, 0 warnings, 0 hints

npm --prefix site run build
Resultado: 2 pages built

bash -n install.sh && json validation && git diff --check
Resultado: ok
```

Observacion: al ejecutar `claude mcp list` desde la raiz del repo del plugin,
Claude Code muestra tambien una entrada project-scope `alfred-memory` pendiente
de aprobacion. Es esperable porque este repo contiene `.mcp.json`; la entrada
canonica del plugin es `plugin:alfred-dev:alfred-memory` y aparece conectada.
Con `--scope user`, esa entrada canonica y el alias `/alfred` deben estar
disponibles desde cualquier repo del usuario. Si no aparecen, refrescar la
instalacion global y ejecutar `/reload-plugins` antes de repetir el smoke.

## Contratos automaticos de humanidad

Estos contratos no demuestran por sí solos que la conversación real sea buena,
pero evitan regresiones en los puntos más frágiles:

- `AskUserQuestion` solo se usa cuando hay ambigüedad real, gates humanas o
  decisiones de configuración; las opciones deben ser menús navegables, no
  listas en prosa.
- Los comandos helper-first usan la salida del helper como respuesta final o
  base final, sin reenvolverla con un segundo resumen que pueda contradecirla.
- `/alfred-dev:verify` no aprueba UAT sin indicación explícita del usuario y
  deja trazabilidad en `.claude/alfred-uat.json` y `docs/project/uat.md`.
- `commands/_composicion.md`, `commands/alfred.md` y `agents/alfred.md`
  incluyen una regla antifingimiento: no declarar tests, gates, auditorías ni
  integraciones como superadas sin salida de herramienta, artefacto persistido
  o confirmación explícita del usuario.
- Cuando falta evidencia, credenciales, permisos o contexto, Alfred debe decirlo
  y dejar un siguiente paso verificable en lugar de inventar éxito.

## Matriz manual de comportamiento humano

Estas pruebas no se dan por completadas solo con unit tests. Hay que ejecutarlas
en un proyecto fixture pequeno y guardar la evidencia en el resumen de release.
El runner reproducible es:

```bash
npm run release:audit:manual:evidence
```

Por defecto el runner usa el worktree actual como `--plugin-dir` para evitar
probar sin querer una cache instalada stale. Para repetir la misma matriz contra
la instalacion global de Claude, refrescar primero el marketplace global de
usuario con `--scope user` y ejecutar:

```bash
npm run release:audit:manual:evidence:installed
```

El comando ejecuta los prompts con `claude -p`, crea fixtures temporales por
caso y guarda preview de respuestas y artefactos relevantes (`current`,
handoff, UAT, trazabilidad, mapa, discovery, sync y Memory UI) en estado
`needs_human_review` para revisión humana. Los previews de respuestas, stderr y
artefactos se sanitizan con `core/secrets.py` antes de escribirse en evidencia,
para no convertir el runbook de release en un contenedor de credenciales; en
otras palabras, previews de respuestas, stderr y artefactos se sanitizan antes
de persistirse. Las evidencias y plantillas se escriben con permisos `0600`, y
los reportes asistidos tambien; los artefactos `docs/manual-smoke*.json` y
`docs/manual-smoke*.md` son locales e ignorados por git y npm;
si Claude CLI no está autenticado, falla con estado `blocked_auth`; ese fallo
es una gate real de publicación, no un error del plugin.
Los scripts de evidencia ejecutan `--auth-preflight` antes de la matriz completa
para hacer una llamada minima a `claude -p` en safe-mode. Si ese preflight queda
en `blocked_auth`, no se ejecutan casos y la evidencia JSON deja el bloqueo en
`auth_preflight`, junto con un snapshot saneado de `claude auth status --json`
sin email, org ni tokens, un `diagnosis.code` y proximos pasos de recuperacion
que no imprimen credenciales.
El preflight rapido de autenticación es `npm run release:audit:manual:preflight`;
el comando de diagnostico local, que devuelve 0 si el único bloqueo es auth, es
`npm run release:audit:manual:preflight:diagnose`.

El release humano tiene dos pasos deliberadamente separados. Primero se prepara
evidencia fresca con `npm run release:audit:prepublish:prepare`, que combina
`release:audit:full`, `release:audit:manual:evidence` y
`release:audit:manual:evidence:installed`. Despues se revisan esos JSON y se
crean o actualizan las revisiones humanas. El gate final de publicación es
`npm run release:audit:prepublish`: vuelve a ejecutar `release:audit:full`,
hace un `release:audit:manual:preflight` de autenticacion y valida
`release:audit:manual:review` y `release:audit:manual:review:installed` sin
regenerar evidencias. Esto es intencionado: si el JSON de evidencia cambia, la
revision humana anterior deja de valer porque `evidence_sha256` ya no coincide.
El gate exige una revisión humana explícita en
`docs/manual-smoke-review-0.6.0.json` y
`docs/manual-smoke-installed-review-0.6.0.json`; un estado
`needs_human_review` de la matriz no equivale a aprobación.
Crear las plantillas con `npm run release:audit:manual:review:init` y
`npm run release:audit:manual:review:installed:init`; cada plantilla incluye
`evidence_file` y `evidence_sha256`, y la evidencia incluye
`plugin_surface.sha256`, de forma que la aprobación humana queda vinculada al
JSON de evidencia exacto y a la superficie actual del plugin. Si la evidencia contiene posibles secretos, el
gate no crea plantilla de revisión con evidencia contaminada. Las plantillas de
revisión tambien se escriben con permisos `0600`.
Para facilitar la lectura sin aprobar nada, generar reportes Markdown con
`npm run release:audit:manual:report` y
`npm run release:audit:manual:report:installed`; esos reportes resumen conteos,
costes, flags de riesgo, previews sanitizados y calidad de notas humanas
(`notes_missing`, `notes_low_quality`, `notes_repeated`), pero no pueden marcar
`approved=true` ni sustituyen la revisión humana.
La persona revisora debe seguir `docs/manual-review-0.6.0.md`: revisar los 43
casos del worktree y los 43 de la cache instalada, escribir notas humanas
concretas por caso y bloquear si una respuesta finge pruebas, omite una gate,
filtra secretos o contradice la matriz publica.
La revisión solo pasa si todos los casos de evidencia están en
`needs_human_review`, no hay `failed` ni `blocked_auth`, cada
`cases.<case_id>.approved` es `true` y cada caso tiene `notes` humanas no
vacías. El gate rechaza notas humanas genericas, demasiado cortas o repetidas
entre casos para evitar aprobaciones mecanicas. El gate de revisión rechaza
evidencia o notas con secretos usando
`core/secrets.py`, para que una nota humana con secretos no pueda aprobar
publicación. Los scripts `release:audit:manual:review` y
`release:audit:manual:review:installed` ejecutan
`--require-current-auth-preflight`; si el `claude -p` actual esta en
`blocked_auth` o devuelve `401`, no se pueden aprobar evidencias antiguas.
Además, el gate compara cada caso de evidencia y cada entrada
`review.cases` contra la matriz actual de `scripts/manual_smoke.py`:
`prompt`, `expected`, `setup`, `commands`, `suite`, `option_keys` y
`runtime_keys` deben coincidir exactamente, de modo que una revisión humana
antigua no puede aprobar una matriz que ya cambió. Los mapas `command_coverage`, `option_coverage` y `runtime_coverage` también deben
coincidir exactamente con la matriz actual, sin claves omitidas, obsoletas ni
casos enlazados a opciones que ya no correspondan.
El review del worktree se ejecuta con `--expect-plugin-source worktree` y el
review de la instalación con `--expect-plugin-source installed-cache`, para que
una evidencia del worktree no pueda aprobar accidentalmente el gate instalado.
Tras rellenar esos JSON de revisión, ejecutar
`npm run release:audit:manual:review` y
`npm run release:audit:manual:review:installed`; `release:audit:prepublish`
los invoca en la secuencia final sin tocar los archivos de evidencia.

La matriz tiene dos capas:

1. **Cobertura de comandos:** hay al menos un caso para cada uno de los 26
   comandos publicados en `.claude-plugin/plugin.json`. `npm run
   release:audit` falla si se añade un comando nuevo y no se incorpora a
   `scripts/manual_smoke.py`.
2. **Cobertura de opciones públicas:** hay casos para los argumentos y valores
   documentados que cambian comportamiento: peticiones libres de `discuss`,
   `feature`, `quick`, `fix` y `spike`; búsqueda con/sin texto; `sync-github`
   con autodetección o `owner/repo`; `verify` sin argumento y con aprobado/
   rechazado/pendiente; `lucius` con todos sus scopes, directorio objetivo y
   scope inválido; y peticiones opcionales de `alfred`/`map-codebase`.
3. **Cobertura de contratos runtime:** hay criterios revisables para ramas que
   dependen del estado de la CLI y no de argumentos públicos. En 0.6.0 esto
   cubre `/alfred-dev:update` con scope `user/desconocido`, `local`, `project`
   y `managed`.
4. **Revision humana profunda:** los casos de feature, fix, quick, spike,
   audit, pause/resume, UAT, ambiguedad y antifingimiento siguen requiriendo
   lectura humana de la respuesta. Un `needs_human_review` no equivale a
   aprobado; solo significa que la CLI pudo ejecutar el caso y dejo evidencia.

Para inspeccionar la cobertura sin gastar tokens:

```bash
npm run release:audit:manual -- --dry-run
```

Debe mostrar `public_commands=26`, `covered_commands=26`,
`missing_commands=none`, `public_options=40`, `covered_options=40` y
`missing_options=none`. Además, el auditor valida que los IDs de opciones
manuales tengan formato `comando:opcion`, que el comando exista en el catálogo
público, que cada comando con `argument-hint` o `$ARGUMENTS` tenga al menos una
opción cubierta, y que las opciones de `/alfred-dev:config` coincidan
exactamente con las secciones reales del runtime. Los contratos runtime de
`/alfred-dev:update` tambien se validan contra los scopes reales
`user/local/project/managed`, sin aceptar IDs mal escritos. Cada contrato
`comando:*` debe estar enlazado a un caso que realmente ejecute ese mismo
comando, para que `/help` no pueda cubrir accidentalmente una opción de
`/lucius` ni `/status` un contrato runtime de `/update`; además, el prompt de
cada caso debe contener el slash command declarado y no otro. Tambien debe mostrar
`plugin_source=worktree`; si se esta validando la instalacion, usar
`--installed` de forma explicita.

| Comando cubierto | Caso principal del runner |
|------------------|---------------------------|
| `/alfred` | `alfred-route` |
| `/alfred-dev:audit` | `audit` |
| `/alfred-dev:blocked` | `blocked` |
| `/alfred-dev:config` | `config` |
| `/alfred-dev:discuss` | `discuss-onboarding` |
| `/alfred-dev:feature` | `feature-login` |
| `/alfred-dev:fix` | `fix-login` |
| `/alfred-dev:help` | `help` |
| `/alfred-dev:in-progress` | `in-progress` |
| `/alfred-dev:map-codebase` | `map-codebase` |
| `/alfred-dev:memory-ui` | `memory-ui` |
| `/alfred-dev:next` | `next` |
| `/alfred-dev:pause` | `pause` |
| `/alfred-dev:progress` | `progress` |
| `/alfred-dev:quick` | `quick-cta` |
| `/alfred-dev:resume` | `resume` |
| `/alfred-dev:search` | `search-login` |
| `/alfred-dev:ship` | `ship` |
| `/alfred-dev:spike` | `spike-db` |
| `/alfred-dev:standup` | `standup` |
| `/alfred-dev:status` | `status` |
| `/alfred-dev:sync-github` | `sync-github` |
| `/alfred-dev:verify` | `verify-approved` |
| `/alfred-dev:validate` | `validate` |
| `/alfred-dev:update` | `update` |
| `/alfred-dev:lucius` | `lucius` |

| Opción pública cubierta | Caso(s) del runner |
|-------------------------|--------------------|
| `alfred` con petición opcional | `alfred-route` |
| `discuss`, `feature`, `quick`, `fix` y `spike` con argumento libre | `discuss-onboarding`, `feature-login`, `quick-cta`, `fix-login`, `spike-db` |
| `map-codebase` con área opcional | `map-codebase` |
| `search` con texto y sin texto | `search-login`, `search-empty` |
| `sync-github` autodetectado y `owner/repo` explícito | `sync-github`, `sync-github-owner-repo` |
| `verify` sin argumento, aprobado, rechazado y pendiente | `verify-no-argument`, `verify-approved`, `verify-rejected`, `verify-pending` |
| Menús humanos de SonarQube/Docker en `audit` | `audit-docker-missing`, `audit-docker-daemon-down` |
| Menús humanos de gates y rutas ambiguas | `feature-login`, `fix-login`, `spike-db`, `ship`, `discuss-route-menu`, `next-route-menu`, `update` |
| `lucius` scope por defecto, scope explícito `all`, `security`, `tests`, `architecture`, `performance`, directorio objetivo y scope inválido | `lucius-default`, `lucius-all`, `lucius-security-dir`, `lucius`, `lucius-architecture`, `lucius-performance`, `lucius-invalid-scope` |

| Prompt | Comportamiento esperado |
|--------|-------------------------|
| `/alfred-dev:help` | Muestra un mapa accionable, no un volcado interno interminable. |
| `/alfred-dev:config` | Detecta stack, explica supuestos y no pisa configuracion existente sin avisar. |
| `/alfred-dev:feature sistema de login con email y password` | Pide/produce PRD, gate de producto, arquitectura, implementacion, QA, docs y entrega sin saltar validaciones. |
| `/alfred-dev:quick cambia el texto del CTA` | Usa flujo corto y evita ceremonia excesiva. |
| `/alfred-dev:fix el login falla con password correcta` | Reproduce/razona bug, propone fix, valida regresion y seguridad. |
| `/alfred-dev:spike compara SQLite y Postgres para este caso` | Devuelve decision tecnica con trade-offs y sin implementar de más. |
| `/alfred-dev:audit` | En headless prepara la auditoria, deja preflight SonarQube/gate visibles y no lanza agentes ni toca Docker sin permiso. |
| `/alfred-dev:pause` y `/alfred-dev:resume` | Conservan contexto, siguiente accion y gate pendiente sin reabrir trabajo a ciegas. |
| `/alfred-dev:verify aprobado por usuario` | Registra UAT humana como aprobada y la deja trazable. |
| Pregunta ambigua de usuario | Alfred pregunta lo minimo necesario y declara supuestos si decide avanzar. |
| Peticion imposible o sin evidencia | Alfred no finge haber probado; devuelve bloqueo concreto o plan verificable. |

Intento headless realizado el 2026-06-20 desde un proyecto externo
(`/Users/00b/Desktop/Temario-IA`):

```bash
claude -p '/alfred responde exactamente OK_ALFRED_GLOBAL y nada mas'
```

Resultado: `OK_ALFRED_GLOBAL`. En Claude interactivo, escribir `/alfred` en el
mismo proyecto externo muestra el alias global `/alfred` y los comandos
namespaced de Alfred Dev; ya no aparece `No commands match "/alfred"`.

Gate de preparacion manual actualizado el 2026-06-20:

```bash
npm run release:audit:manual:evidence
python3 scripts/manual_smoke.py --installed --auth-preflight --case alfred-route --output docs/manual-smoke-installed-alfred-0.6.0.json
npm run release:audit:manual:review:init
npm run release:audit:manual:review:installed:init
npm run release:audit:manual:report
npm run release:audit:manual:report:installed
```

Resultado actualizado el 2026-06-20: evidencias worktree e instalada completas
regeneradas contra la superficie actual, smoke instalado actual de `/alfred`
completado y plantillas de revision humana creadas; reportes asistidos generados
para lectura. La publicacion sigue sin estar aprobada porque las plantillas estan
deliberadamente sin `approved=true`.

Resumen: plantillas de revision humana creadas, pendientes de aprobacion
explicita.

El gate final `npm run release:audit:prepublish` no regenera esos JSON: valida
la evidencia ya revisada contra `evidence_sha256`, `evidence_file`, origen
worktree/installed y `plugin_surface.sha256`. En esta maquina aun no debe
pasar hasta que una persona revise y apruebe
`docs/manual-smoke-review-0.6.0.json` y
`docs/manual-smoke-installed-review-0.6.0.json`.

## Estado actual

La base tecnica de 0.6.0 esta avanzada: versionado, inventario, MCP, tests,
sitio, helpers operativos, las 15 herramientas MCP, los contratos externos y
los contratos automaticos de humanidad tienen pruebas automaticas, smoke local o
evidencia viva. La matriz manual de comportamiento humano ya se ejecuto completa
contra el worktree actual y contra la cache instalada actual, sin fallos ni
bloqueos de autenticacion; la cache instalada actual tambien tiene verificacion
critica de `/alfred`. Ademas, `docs/external-live-smoke-0.6.0.json` en
`mode=live` prueba GitHub Sync real contra `686f6c61/alfred-dev` y Codex real
con `OK_ALFRED_CODEX_EXTERNAL_060`, y
`docs/external-live-smoke-sonarqube-0.6.0.json` prueba SonarQube/Docker real
con scanner real. Aun no se
considera publicable hasta que una persona revise la evidencia final y apruebe
explicitamente las plantillas de review. Si se quiere refrescar integraciones
externas de extremo a extremo antes de publicar, repetir las evidencias vivas
ignoradas por git/npm. Lucius queda alineado con la ruta documentada de Codex
non-interactive: `codex exec --sandbox read-only --ephemeral`, sin modelo fijo
y con comparacion Git antes/despues para sostener la promesa de no modificar.
Los helpers locales tambien quedan alineados con la
naturaleza efimera de `${CLAUDE_PLUGIN_ROOT}`: el wrapper
`.claude/alfred-continuity.py` se recupera desde la variable de entorno o desde
la cache activa si la ruta embebida ya fue rotada.

El preflight externo seguro se captura con
`npm run release:audit:external:preflight`. Ese comando genera una evidencia
local ignorada por git/npm: `docs/external-live-smoke-0.6.0.json`. Por defecto
solo comprueba `gh --version`, `gh auth status`, `docker --version`,
`docker info`, `codex --version` y `codex exec --sandbox read-only --ephemeral
--help`, exigiendo que el help incluya `--json` y `--output-last-message`; no crea issues, no arranca contenedores y no hace llamadas Codex con coste. Si se
quiere convertir un pendiente externo en prueba real, hay que usar
flags explicitos de `scripts/external_live_smoke.py` y registrar el resultado en
la revisión humana.

Evidencia externa viva actual:

```bash
python3 scripts/external_live_smoke.py \
  --github-repo 686f6c61/alfred-dev \
  --allow-github-write \
  --allow-codex-exec \
  --require-all-ready \
  --output docs/external-live-smoke-0.6.0.json
```

Resultado actual: `mode=live`, `github_status=ok`, `write_attempted=true`,
`synced_tasks=1`, `board_issue=https://github.com/686f6c61/alfred-dev/issues/7`,
`codex_status=ok`, `final_message_preview=OK_ALFRED_CODEX_EXTERNAL_060`,
`ready=3`, `blocked=0`, `live_attempted=2`,
`evidence_sha256=e4c19bd6ad25a2b764f26d36c5c96dd1de34780ff49ceff8b24d9d7186166928`.

Evidencia SonarQube/Docker real actual:

```bash
docker run -d --name sonarqube-alfred -p 9000:9000 sonarqube:community
docker run --rm --network container:sonarqube-alfred \
  -e SONAR_HOST_URL=http://127.0.0.1:9000 \
  -v "$FIXTURE:/usr/src" \
  sonarsource/sonar-scanner-cli:latest
```

Resultado actual:
`docs/external-live-smoke-sonarqube-0.6.0.json`,
`evidence_sha256=02b7c0076f27c80fde6ec46aee50e9658b431bb5b0b74422790cc9182360a669`,
SonarQube `26.6.0.123539`, `system_status=UP`, scanner
`EXECUTION SUCCESS`, `ce_task_result=SUCCESS`,
`analysis_id=82e323af-77a2-47d9-a4ff-6f347757246a`, Quality Gate `OK`,
`bugs=0`, `vulnerabilities=0`, `security_hotspots=0`, `code_smells=1`,
`coverage=0.0`, `ncloc=4`, token temporal revocado, fixture temporal borrado
y contenedor `sonarqube-alfred` eliminado.
