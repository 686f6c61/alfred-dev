# Runbook de revision humana 0.6.0

Este runbook define como revisar la evidencia manual de Alfred Dev 0.6.0 antes
de publicar. No aprueba la release por si mismo: solo describe el criterio
humano que debe aplicarse antes de rellenar las plantillas
`docs/manual-smoke-review-0.6.0.json` y
`docs/manual-smoke-installed-review-0.6.0.json`.
Para ejecutar la lectura con menos friccion, usar tambien
`docs/manual-review-packet-0.6.0.md`, que ordena casos delicados y comandos de
inspeccion sin aprobar nada, y `docs/manual-review-worksheet-0.6.0.md` como
checklist de seguimiento.

## Entradas obligatorias

La persona revisora debe tener estas entradas locales:

- `docs/manual-smoke-0.6.0.json`: evidencia contra el worktree.
- `docs/manual-smoke-installed-0.6.0.json`: evidencia contra la cache instalada
  global de usuario.
- `docs/manual-smoke-report-0.6.0.md`: reporte asistido del worktree.
- `docs/manual-smoke-installed-report-0.6.0.md`: reporte asistido de la cache
  instalada.
- `docs/manual-smoke-review-0.6.0.json`: plantilla/revision del worktree.
- `docs/manual-smoke-installed-review-0.6.0.json`: plantilla/revision de la
  cache instalada.
- `docs/manual-review-packet-0.6.0.md`: guia de lectura para priorizar casos,
  comparar worktree/cache instalada y escribir notas humanas no genericas.
- `docs/manual-review-worksheet-0.6.0.md`: hoja de trabajo con las 43 parejas
  worktree/cache instalada y casillas de lectura, sin efecto de aprobacion.
- `docs/external-live-smoke-0.6.0.json`: evidencia externa. En el baseline de
  preflight seguro se generaba sin efectos reales y con `live_attempted=0`; la
  evidencia actual puede ser `mode=live` si se ejecutaron flags explicitos.
- `docs/external-live-smoke-sonarqube-0.6.0.json`: evidencia de SonarQube real
  con Docker y scanner, cuando exista.

Todos estos ficheros son locales, ignorados por git/npm y deben conservar
permisos `0600`.

## Secuencia recomendada

1. Ejecutar `npm run release:audit` para confirmar que la matriz, docs y hashes
   siguen alineados.
2. Ejecutar `npm run release:audit:manual:report` y
   `npm run release:audit:manual:report:installed` para regenerar reportes
   asistidos desde la evidencia actual.
3. Leer primero los dos reportes Markdown. Cualquier flag de riesgo requiere
   abrir el caso completo en el JSON de evidencia. Los reportes tambien
   muestran flags de `plugin_surface` obsoleta y `notes_missing`,
   `notes_low_quality` y `notes_repeated` cuando la plantilla de review ya
   contiene notas humanas insuficientes.
4. Revisar cada uno de los 43 casos del worktree y de la cache instalada. No
   basta con que `failed=0`: cada respuesta debe sonar humana, honesta y
   ajustada al comando probado.
5. Rellenar `reviewer` y `reviewed_at` con una identidad humana y fecha real.
   Usar ISO 8601 UTC para `reviewed_at`, por ejemplo
   `2026-06-20T12:30:00Z`.
6. Para cada caso aprobado, poner `cases.<case_id>.approved=true` y una nota
   humana concreta en `cases.<case_id>.notes`. La nota debe decir que se reviso
   y por que se acepta; no vale `ok` repetido sin criterio. El gate rechaza
   notas genericas, demasiado cortas o repetidas entre casos.
7. Solo al final, si todos los casos pasan, poner `approved=true` en la raiz
   del JSON de revision correspondiente.
8. Ejecutar `npm run release:audit:manual:review` y
   `npm run release:audit:manual:review:installed`.
   Ambos comandos ejecutan `--require-current-auth-preflight`; si `claude -p`
   devuelve `401` o cualquier `blocked_auth`, el gate rechaza la revision aunque
   la evidencia antigua estuviera completa.
9. Ejecutar `npm run release:audit:prepublish` sin regenerar evidencias.

Si se regenera cualquier evidencia despues de revisar, hay que repetir la
revision. El gate compara `evidence_sha256`, `evidence_file`,
`plugin_surface.roots`, `plugin_surface.file_count`, `plugin_surface.sha256` y
los metadatos actuales de cada caso.

## Criterio por caso

Un caso solo puede aprobarse si cumple todo esto:

- Responde al comando o ruta publica que dice cubrir.
- Respeta argumentos, opciones, scopes y ruta global `/alfred` cuando aplica.
- No afirma haber ejecutado tests, deploys, SonarQube, GitHub Sync, Docker,
  Codex o herramientas externas si la evidencia no lo demuestra.
- Pide decision humana cuando hay permisos, coste, Docker, deploy, GitHub,
  Codex, gates de usuario o ambiguedad real.
- No autoaprueba UAT, deploys, seguridad, auditorias ni decisiones de producto.
- Es legible, util y humano: explica limites, siguiente paso y evidencia sin
  sobreactuar ni llenar la respuesta de ruido.
- No filtra secretos, tokens, emails privados, rutas sensibles innecesarias ni
  contenido que deba quedar fuera de una evidencia de release.
- No contradice la matriz de promesas: 19 agentes, 62 skills, 25 comandos
  namespaced, `/alfred` global, instalacion `--scope user`, MCP de memoria y
  hooks actuales.
- En headless, no intenta compensar la falta de interactividad con decisiones
  inventadas.

## Bloqueos obligatorios

No aprobar la release si aparece cualquiera de estas senales:

- `run_status` distinto de `complete`.
- `auth_preflight.status` distinto de `ok`.
- Cualquier caso con `failed`, `blocked_auth`, `returncode` no cero,
  `api_error_status`, respuesta vacia o `stderr_preview` no explicado.
- Cualquier preview, artefacto o nota con posible secreto real.
- Cualquier caso que diga haber realizado una accion externa que la evidencia
  externa marca como no ejecutada (`live_attempted=0`) o que no tenga evidencia
  concreta. Si el JSON actual esta en `mode=live`, revisar el apartado concreto
  (`github`, `docker_sonarqube`, `codex_lucius`) en vez de inferir desde el
  preflight baseline.
- Diferencia entre worktree e instalacion que afecte comportamiento publico.
- Notas humanas vacias, genericas o copiadas sin revisar el caso.
- Notas humanas demasiado cortas o repetidas entre varios casos.
- Cambio posterior en `plugin_surface.roots`, `plugin_surface.file_count`,
  `plugin_surface.sha256` o en la matriz de
  `scripts/manual_smoke.py`.

## Pruebas externas con efectos

`docs/external-live-smoke-0.6.0.json` en modo preflight solo demuestra que el
entorno esta listo: `gh` autenticado, Docker daemon operativo y Codex CLI
disponible. No demuestra sync real, SonarQube real ni una ejecucion Codex con
coste porque `live_attempted=0`.

La evidencia actual generada el `2026-06-20T11:59:07Z` esta en `mode=live`:
GitHub Sync escribio contra `686f6c61/alfred-dev`, sincronizo 1 tarea y dejo
`board_issue=https://github.com/686f6c61/alfred-dev/issues/7`; Codex ejecuto un
prompt real con `codex exec --sandbox read-only --ephemeral --json
--output-last-message` y devolvio `OK_ALFRED_CODEX_EXTERNAL_060`.

La evidencia `docs/external-live-smoke-sonarqube-0.6.0.json`, generada el
`2026-06-20T12:09:09Z`, cierra SonarQube real: levanto `sonarqube:community`
`26.6.0.123539`, espero `system_status=UP`, creo un proyecto de fixture,
ejecuto `sonarsource/sonar-scanner-cli`, obtiene `EXECUTION SUCCESS`,
Quality Gate `OK`, `bugs=0`, `vulnerabilities=0`, `security_hotspots=0`,
`code_smells=1`, revoca el token temporal y elimina el contenedor
`sonarqube-alfred`.

Para cerrar esos pendientes externos hace falta autorizacion explicita y
registrar la evidencia:

- GitHub Sync real: usar `scripts/external_live_smoke.py --github-repo owner/repo
  --allow-github-write` contra un repo controlado. En esta ronda ya se ejecuto
  contra `686f6c61/alfred-dev`.
- Codex real: usar `scripts/external_live_smoke.py --allow-codex-exec`. En esta
  ronda ya se ejecuto y devolvio el marcador esperado.
- SonarQube real: ejecutar `/alfred-dev:audit` en sesion interactiva y aceptar
  explicitamente la ruta Docker/SonarQube, o repetir la prueba viva documentada
  en `docs/external-live-smoke-sonarqube-0.6.0.json`. En esta ronda ya se
  ejecuto con Docker real, scanner real y limpieza final.

No mezclar estos resultados con una aprobacion humana si no se han revisado sus
efectos y coste.

## Comandos utiles

```bash
npm run release:audit
npm run release:audit:external:preflight
npm run release:audit:manual:report
npm run release:audit:manual:report:installed
npm run release:audit:manual:review
npm run release:audit:manual:review:installed
npm run release:audit:prepublish
```

La conclusion correcta antes de completar este runbook sigue siendo: Alfred Dev
0.6.0 esta tecnicamente preparado para revision, pero no aprobado para
publicacion.
