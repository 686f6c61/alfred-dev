# Readiness de release 0.6.0

Este documento resume el estado publicable de Alfred Dev 0.6.0 sin sustituir
la matriz completa de auditoria ni la revision humana final. Su funcion es
responder a una pregunta concreta: que esta probado hoy, que evidencia lo
demuestra y que falta antes de publicar con honestidad.

**Estado actual:** autenticacion de `claude -p` recuperada; matrices worktree e
instalada completas regeneradas contra la superficie actual; GitHub Sync real,
Codex real y SonarQube/Docker real probados; no aprobado para publicar hasta
completar revision humana.

**Fecha de corte:** 2026-06-20.

## Decision de salida

No se debe publicar todavia. La base tecnica, la instalacion global de usuario,
el alias `/alfred`, el empaquetado, los contratos de Claude Code actual, el
preflight headless de Claude y las integraciones externas reales automatizadas
estan cubiertos. La publicacion sigue pendiente por dos motivos honestos:

1. falta revision humana explicita de las 43 respuestas reales del worktree;
2. falta revision humana explicita de las 43 respuestas reales instaladas.

Los reportes Markdown asistidos ayudan a leer la evidencia, pero no aprueban
nada. El gate final correcto es `npm run release:audit:prepublish`; debe seguir
fallando hasta que las plantillas de revision tengan `approved=true`,
`reviewer`, `reviewed_at` y notas humanas por caso.

## Requisitos del objetivo

Nota de superficie: tras limpiar el histórico antiguo del README público y
añadir la sección del equipo, la superficie actual del plugin es
`plugin_surface.sha256=0ec656f2c4bbc1c329d8df142b868a02f272bc68c5d0985696cd98996eb7cd68`.
Las evidencias manuales citadas en esta página que conservan
`plugin_surface.sha256=fb72f4beec3ccba3c35fa2291e1f3b03d80542f3e8a5f5b7f083569c7e5f3de8`
siguen documentando el smoke funcional previo, pero deben regenerarse antes de
aprobar la publicación final.

| Requisito | Evidencia actual | Estado |
|-----------|------------------|--------|
| Mantener la version en `0.6.0` hasta publicar | `package.json`, `.claude-plugin/plugin.json`, `tests/test_version_consistency.py`, `npm run release:audit` | Probado |
| Instalar siempre Alfred como global de usuario | `install.sh`, `install.ps1`, `docs/installation.md`, `commands/update.md`, `claude plugin list --json` con `scope=user` para `alfred-dev@alfred-dev`; los instaladores limpian `local/project` heredados antes de reinstalar `user` | Probado |
| Que `/alfred` quede instalado fuera del repo | `~/.claude/skills/alfred/SKILL.md` con `user-invocable: true`, ausencia de shim duplicado en `~/.claude/commands/alfred.md`, `python3 scripts/release_audit.py --with-claude`, `claude plugin list --json` con `scope=user` y `enabled=true` | Probado |
| Que `/alfred` sea descubrible en una sesion interactiva nueva | `npm run release:audit:claude:commands`; PTY real con `claude`: al escribir `/alfred` en el selector aparece una sola entrada `/alfred` junto a comandos `/alfred-dev:*`; no aparece `No commands match` | Probado |
| Que `/alfred` responda en `claude -p` fuera del repo | `docs/manual-smoke-installed-alfred-0.6.0.json`: cache instalada global, `run_status=complete`, `returncode=0`, `failed=0`, `blocked_auth=0`, `plugin_surface.sha256=fb72f4beec3ccba3c35fa2291e1f3b03d80542f3e8a5f5b7f083569c7e5f3de8`; discovery externo: `/alfred visible`, sin `No commands match` | Probado |
| Cubrir todas las rutas publicas | Matriz manual: 26/26 rutas publicas cubiertas, incluidos 25 comandos `/alfred-dev:*` y `/alfred` | Probado por matriz |
| Cubrir todas las opciones publicas | Matriz manual: 40/40 opciones publicas cubiertas y validadas contra comandos reales | Probado por matriz |
| Cubrir contratos runtime de update | Matriz manual: `user`, `local`, `project` y `managed` cubiertos; `local`/`project` normalizan a `--scope user` | Probado por matriz |
| Que Claude vea el inventario real | `claude plugin details`, `release:audit`: 19 agentes, 62 skills, 25 comandos namespaced, 13 hooks visibles y 1 MCP | Probado |
| Alinear con Claude Code actual | Revalidacion oficial 2026-06-20 en `docs/release-audit-0.6.0.md`: plugins, skills, commands, subagents, hooks, MCP, AskUserQuestion y reload | Probado por contrato |
| Alinear Lucius con Codex actual | `codex exec --sandbox read-only --ephemeral --json --output-last-message`, `approval_policy='never'`, sin modelo Codex obsoleto fijo | Probado por contrato |
| Evitar fingir pruebas, deploys o auditorias | `npm run release:audit:human`, antifingimiento en `_composicion.md` y agente Alfred, UAT sin aprobacion implicita | Probado por contrato |
| Probar comportamiento real en Claude CLI | `npm run release:audit:manual:preflight`: `status=ok`, respuesta `OK`; `docs/manual-smoke-0.6.0.json`: 43/43 casos worktree ejecutados, `failed=0`, `blocked_auth=0`; `docs/manual-smoke-installed-0.6.0.json`: 43/43 casos instalados ejecutados, `failed=0`, `blocked_auth=0`; `docs/manual-smoke-installed-alfred-0.6.0.json`: `/alfred` instalado ejecutado, `failed=0`, `blocked_auth=0` | Probado; pendiente revisión humana |
| Pruebas externas reales automatizadas | `docs/external-live-smoke-0.6.0.json`: `mode=live`, GitHub Sync con `gh` autenticado contra repo real, `github_status=ok`, `write_attempted=true`, `synced_tasks=1`, `board_issue=https://github.com/686f6c61/alfred-dev/issues/7`, Lucius contra Codex CLI autenticado, `codex_status=ok`, `final_message_preview=OK_ALFRED_CODEX_EXTERNAL_060`, `ready=3`, `blocked=0`, `live_attempted=2`; `docs/external-live-smoke-sonarqube-0.6.0.json`: SonarQube/Docker real, `status=ok`, scanner `EXECUTION SUCCESS`, Quality Gate `OK`, `bugs=0`, `vulnerabilities=0`, `security_hotspots=0`, `code_smells=1`, `container_removed=true` | Probado |
| Preflight externo seguro | Baseline del mismo runner en modo por defecto: `github_status=ready`, `docker_status=docker_ready`, `codex_status=ready`, `ready=3`, `blocked=0`, `live_attempted=0`; no escribe en GitHub, no arranca SonarQube y no ejecuta Codex | Probado como modo seguro; no sustituye pruebas reales con efectos |
| Proteger secretos y evidencia local | `core/secrets.py`, `scripts/manual_smoke.py`, `scripts/manual_review_gate.py`, permisos `0600`, `.gitignore`/`.npmignore` para evidencias y `docs/project/` | Probado |
| Empaquetar solo superficie publicable | `npm pack --dry-run --json`, `npm run release:audit`: sin caches, sin tests, sin `.claude/`, sin `.crupier/`, sin evidencias manuales | Probado |
| Publicar honestamente | `npm run release:audit:prepublish` valida full audit + preflight + revisiones humanas sin regenerar evidencia | Bloqueado a proposito hasta revision humana |

## Evidencia canonica

- Worktree manual smoke:
  `docs/manual-smoke-0.6.0.json`,
  `evidence_sha256=63cbc3822ac4c4bdb56699427db7fdeefd2fb36a9b4de04a7e6865aad6262008`,
  `plugin_source=worktree`, `run_status=complete`, 43/43 casos, `failed=0`,
  `blocked_auth=0`, coste observado `$33.2240255`,
  `plugin_surface.sha256=fb72f4beec3ccba3c35fa2291e1f3b03d80542f3e8a5f5b7f083569c7e5f3de8`.
- Cache instalada smoke critico de `/alfred`:
  `docs/manual-smoke-installed-alfred-0.6.0.json`,
  `evidence_sha256=b63b82d537ab4c66a2be33d718dd53d6c3279f10ad1839665cf8c81a480b7092`,
  `plugin_source=installed-cache`, `run_status=complete`, 1/1 caso,
  `failed=0`, `blocked_auth=0`, coste observado `$1.1070825`.
- Cache instalada manual smoke:
  `docs/manual-smoke-installed-0.6.0.json`,
  `evidence_sha256=778add69bebd84e7bf6fbd79be045ed6dc5d60ccf1d738da1c89bfc2c3a6a9b8`,
  `plugin_source=installed-cache`, 43/43 casos, `failed=0`, `blocked_auth=0`,
  coste observado `$32.414956`,
  `plugin_surface.sha256=fb72f4beec3ccba3c35fa2291e1f3b03d80542f3e8a5f5b7f083569c7e5f3de8`.
- Historial sustituido:
  las evidencias previas
  `evidence_sha256=1acb7d9937862acf9470c2df0cf22f2aa18478c8fe6818490ee91b85007461e7`
  y
  `evidence_sha256=c96d9895b9c76125a3b04fa653976c351a2b9cee4c1d7f46f305aefd077bd292`
  quedan conservadas solo como referencia historica; el bloqueo anterior
  "matriz instalada completa actual" queda cerrado por la evidencia instalada
  actual indicada arriba.
- Superficie de plugin:
  `plugin_surface.sha256=fb72f4beec3ccba3c35fa2291e1f3b03d80542f3e8a5f5b7f083569c7e5f3de8`,
  165 ficheros en `.claude-plugin`, `.mcp.json`, `agents`, `commands`, `core`,
  `hooks`, `mcp`, `skills`, `templates`, `package.json`, `README.md` y
  `scripts`.
- Descubrimiento interactivo de `/alfred`:
  `npm run release:audit:claude:commands` arranca Claude en PTY real desde
  `/tmp/alfred-command-discovery-test`; tras aceptar la carpeta de prueba si
  Claude lo solicita y escribir `/alfred`, Claude muestra `/alfred` como alias
  global y comandos `/alfred-dev:*` relacionados. El smoke falla si aparece
  `No commands match` o si el selector muestra mas de una entrada `/alfred`.
- Revision humana worktree:
  `docs/manual-smoke-review-0.6.0.json`, `approved=false`, 43 casos sin aprobar.
- Revision humana cache instalada:
  `docs/manual-smoke-installed-review-0.6.0.json`, `approved=false`, 43 casos
  sin aprobar.
- Paquete de revision humana:
  `docs/manual-review-packet-0.6.0.md`, guia de lectura sin capacidad de
  aprobacion; prioriza casos delicados y comandos para inspeccionar worktree y
  cache instalada.
- Worksheet de revision humana:
  `docs/manual-review-worksheet-0.6.0.md`, checklist operativa de las 43 parejas
  worktree/cache instalada; no sustituye las notas en los JSON.
- Pruebas externas reales automatizadas:
  `docs/external-live-smoke-0.6.0.json`, generado el
  `2026-06-20T11:59:07Z`, `mode=live`,
  `evidence_sha256=e4c19bd6ad25a2b764f26d36c5c96dd1de34780ff49ceff8b24d9d7186166928`,
  `github_status=ok`, `write_attempted=true`, `synced_tasks=1`,
  `board_issue=https://github.com/686f6c61/alfred-dev/issues/7`,
  `retired=0`, `remote_drift=0`, `docker_status=docker_ready`,
  `sonarqube_autorizado=true`, `sonarqube_live_attempted=false`,
  `codex_status=ok`, `codex_live_attempted=true`,
  `final_message_preview=OK_ALFRED_CODEX_EXTERNAL_060`, `ready=3`,
  `blocked=0`, `live_attempted=2`; el fichero queda ignorado por git/npm y con
  permisos `0600`.
- Preflight externo seguro baseline:
  el mismo runner en modo por defecto genero una evidencia anterior sin efectos
  externos (`github_status=ready`, `docker_status=docker_ready`,
  `codex_status=ready`, `ready=3`, `blocked=0`, `live_attempted=0`). Ese
  baseline demuestra que el modo seguro no escribe en GitHub, no arranca
  SonarQube y no ejecuta Codex; la evidencia viva actual indicada arriba lo
  sustituye para GitHub Sync y Codex real.
- SonarQube/Docker real:
  `docs/external-live-smoke-sonarqube-0.6.0.json`, generado el
  `2026-06-20T12:09:09Z`,
  `evidence_sha256=02b7c0076f27c80fde6ec46aee50e9658b431bb5b0b74422790cc9182360a669`,
  `status=ok`, SonarQube `26.6.0.123539`, `system_status=UP`,
  scanner `EXECUTION SUCCESS`, `ce_task_result=SUCCESS`,
  `analysis_id=82e323af-77a2-47d9-a4ff-6f347757246a`, Quality Gate `OK`,
  `bugs=0`, `vulnerabilities=0`, `security_hotspots=0`, `code_smells=1`,
  `coverage=0.0`, `ncloc=4`, token temporal revocado, fixture temporal borrado
  y contenedor `sonarqube-alfred` eliminado. El fichero queda ignorado por
  git/npm y con permisos `0600`.
- Auditoria tecnica completa actual:
  `npm test` ejecutado el `2026-06-20T02:31:55Z`, `1274 passed, 15 subtests
  passed`; `npm run release:audit:full` ejecutado despues de refrescar la cache
  instalada global de usuario desde el worktree y devuelve
  `release-audit 0.6.0 ok`.

## Estado actual de Claude CLI

Bloqueo historico observado el `2026-06-20T02:31:55Z`:

```bash
claude auth status
claude -p 'responde solo OK'
claude -p --safe-mode --no-session-persistence --max-budget-usd 0.01 --output-format json 'responde solo OK'
npm run release:audit:manual:preflight:diagnose
npm run release:audit:manual:auth:diagnose
```

Resultado:

- `claude auth status` devuelve `loggedIn=true`, `authMethod=claude.ai`,
  `apiProvider=firstParty`, `subscriptionType=max`.
- `claude -p` falla con `Failed to authenticate. API Error: 401 Invalid
  authentication credentials`.
- `--safe-mode`, `--model sonnet` y `--model opus` fallan igual, por lo que no
  apunta a Alfred Dev, MCP, hooks ni modelo concreto.
- `--bare` informa `Not logged in`, comportamiento esperado porque bare no lee
  OAuth/Keychain.
- `claude doctor` no devuelve salida visible en 45 s ni desde la raiz del
  plugin ni desde `/tmp`; no debe usarse como unico gate de recuperacion en
  este entorno.
- `--debug-file` saneado confirma que Claude intenta usar OAuth first-party y
  recibe `authentication_error` 401 del backend antes de consumir tokens.
- `scripts/manual_smoke.py --auth-preflight --preflight-only
  --allow-auth-failure` clasifica el problema como
  `first_party_oauth_token_rejected`.
- `scripts/claude_auth_recovery.py` resume el bloqueo sin secretos y devuelve
  los comandos interactivos exactos para diagnosticar con `claude doctor`,
  desbloquear Keychain en macOS si procede, refrescar login y regenerar
  evidencia. Tambien documenta que, si `doctor` no emite salida, hay que pasar
  a refrescar login o usar el fallback `claude setup-token` +
  `CLAUDE_CODE_OAUTH_TOKEN` para evidencias headless si el flujo de navegador
  sigue bloqueado.

Recuperacion ejecutada el `2026-06-20T10:13:08Z`:

```bash
claude auth logout
claude auth login
npm run release:audit:manual:preflight
npm run release:audit:manual:evidence
python3 scripts/manual_smoke.py --installed --auth-preflight --case alfred-route --output docs/manual-smoke-installed-alfred-0.6.0.json
```

Resultado actual:

- `npm run release:audit:manual:preflight` pasa con `auth_preflight.status=ok`,
  `response_preview=OK`, `api_error_status=null`, Claude Code `2.1.183`,
  `authMethod=claude.ai`, `apiProvider=firstParty`, `subscriptionType=max`.
- La prueba directa con presupuesto artificial de `$0.01` ya no devuelve 401;
  falla por `error_max_budget_usd`, que confirma inferencia real y no bloqueo
  de autenticacion.
- `docs/manual-smoke-0.6.0.json` conserva la matriz worktree actual:
  43/43 casos ejecutados, `failed=0`, `blocked_auth=0`.
- `docs/manual-smoke-installed-alfred-0.6.0.json` prueba el alias instalado
  global `/alfred` contra la cache actual: `returncode=0`, `failed=0`,
  `blocked_auth=0`.
- `docs/manual-smoke-installed-0.6.0.json` conserva la matriz instalada actual:
  43/43 casos ejecutados, `failed=0`, `blocked_auth=0`.

Los comandos `npm run release:audit:manual:review` y
`npm run release:audit:manual:review:installed` siguen usando
`--require-current-auth-preflight`; ahora esa gate de auth pasa, pero la
publicacion debe seguir bloqueada hasta que haya evidencia instalada final y
revision humana explicita.

## Fuentes oficiales revalidadas

La revalidacion documental del 2026-06-20 se basa en fuentes oficiales vivas:

- `https://code.claude.com/docs/en/plugins-reference`
- `https://code.claude.com/docs/en/skills`
- `https://code.claude.com/docs/en/hooks`
- `https://code.claude.com/docs/en/mcp`
- `https://code.claude.com/docs/en/sub-agents`
- `https://code.claude.com/docs/en/commands`
- `https://code.claude.com/docs/en/agent-sdk/user-input`
- `https://code.claude.com/docs/en/best-practices`
- `https://developers.openai.com/codex/noninteractive`
- `https://developers.openai.com/codex/cli/reference`

## Pendientes antes de publicar

1. Revisar `docs/manual-smoke-report-0.6.0.md` y completar
   `docs/manual-smoke-review-0.6.0.json` con aprobacion humana caso por caso,
   siguiendo `docs/manual-review-0.6.0.md`.
2. Revisar `docs/manual-smoke-installed-report-0.6.0.md` y completar
   `docs/manual-smoke-installed-review-0.6.0.json` con aprobacion humana caso
   por caso, siguiendo `docs/manual-review-0.6.0.md`.
3. Reejecutar `npm run release:audit:external:preflight` si cambia el entorno
   externo antes de publicar. Este preflight no escribe en GitHub, no arranca
   SonarQube y no ejecuta Codex; las acciones reales requieren flags explicitos
   en `scripts/external_live_smoke.py`. Si cambia Docker/SonarQube, repetir
   tambien la prueba registrada en `docs/external-live-smoke-sonarqube-0.6.0.json`.
4. Revisar manualmente las plantillas `docs/manual-smoke-review-0.6.0.json` y
   `docs/manual-smoke-installed-review-0.6.0.json`; rellenar notas humanas por
   caso, `reviewer`, `reviewed_at` y `approved=true` solo tras revision real.
   Usar `docs/manual-review-packet-0.6.0.md` como orden de lectura, no como
   sustituto de la revision, y `docs/manual-review-worksheet-0.6.0.md` para
   llevar el seguimiento de lectura.
5. Reejecutar `npm run release:audit:prepublish` sin regenerar evidencias solo
   despues de regenerar/revisar la evidencia nueva.

Hasta que esos puntos esten completos, la conclusion correcta es: 0.6.0 tiene
la base tecnica preparada y Claude headless recuperado, pero la revision humana
e instalada final no esta aprobada para publicacion.
