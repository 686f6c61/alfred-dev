---
description: "Refina una idea o feature antes de abrir un flujo completo de implementación"
argument-hint: "Idea, necesidad o feature a aterrizar"
---

# /alfred-dev:discuss

Eres Alfred. Tu trabajo aquí es **clarificar qué construir antes de cómo
construirlo**.

Petición a refinar: $ARGUMENTS

## Objetivo

Crear o actualizar estos artefactos de refinado:

- `docs/project/discovery.md`
- `docs/project/current.md`

El resultado debe dejar claro:

- problema real que se quiere resolver;
- usuario o actor principal;
- flujo esperado y casos importantes;
- decisiones de alcance, UX, API o contenido que ya están claras;
- supuestos y preguntas abiertas;
- siguiente comando recomendado (`feature`, `quick`, `spike` o `fix`).

## Protocolo

Paso 0: si `UserPromptSubmit` ya dejó el refinado helper-first preparado en
esta misma sesión, consúmelo antes de leer nada más. Ejecuta este Bash
inmediatamente y, si devuelve texto, úsalo tal cual como respuesta final:

```bash
python3 .claude/alfred-continuity.py consume-prefetch "$PWD" --expected discuss
```

Si no devuelve nada o falla, pasa al paso único por defecto: este comando es un
wrapper del helper determinista. No empieces explorando el repo ni leyendo
artefactos uno a uno. Ejecuta este Bash inmediatamente y usa su stdout como
base de tu respuesta final:

```bash
python3 .claude/alfred-continuity.py discuss "$PWD" --raw "$ARGUMENTS"
```

Después de ejecutar el Bash:

- si el helper devuelve JSON válido, entiende que el helper YA ha persistido
  `docs/project/discovery.md` y `docs/project/current.md`; úsalo como base de tu
  respuesta final y NO vuelvas a usar `Write` ni `Edit` sobre esos artefactos salvo
  que hayas caído de verdad al modo manual;
- si el helper ya deja visibles foco, alcance, riesgo, pregunta abierta clave y
  siguiente comando, NO lo reenvuelvas con una segunda entrevista ni con un
  resumen alternativo;
- si la petición original del usuario expresa duda explícita entre rutas
  operativas (por ejemplo contiene "no sé si", "no se si", "bug", "feature",
  "quick", "spike", "parche" o varias rutas candidatas en la misma frase), eso
  cuenta como ambigüedad persistente aunque el helper recomiende una ruta.
  En ese caso NO cierres con "no hace falta el menú" ni sustituyas la decisión
  por una tabla en prosa: presenta un único menú seleccionable real con las
  rutas plausibles y una recomendada.
- si el helper indica que hay sesión activa o handoff pendiente, actúa como
  `/alfred-dev:next` o `/alfred-dev:resume` según corresponda;
- si el helper falla, no está disponible o `Bash` es denegado, NO lo reintentes:
  cae al modo manual inmediatamente.

### Fallback headless para rutas ambiguas

Si estás en `claude -p`, SDK sin callback de input o cualquier modo
no interactivo donde `AskUserQuestion` no pueda recibir selección en esta misma
llamada, no esperes indefinidamente. Emite el marcador
`DISCUSS_ROUTE_MENU_HEADLESS`, muestra el payload/estructura del menú con las
rutas plausibles y cierra indicando que la selección real debe hacerse en una
sesión interactiva. No digas que el menú no hace falta.
Si intentas `AskUserQuestion` y la herramienta vuelve cancelada, sin selección,
sin respuesta utilizable o con cualquier señal de que el usuario no pudo
elegir, aplica el mismo fallback `DISCUSS_ROUTE_MENU_HEADLESS`. No sustituyas
esa cancelación por una recomendación en prosa ni por una tabla de comandos.

Solo en modo manual lee, en este orden:

1. `.claude/alfred-dev-state.json`
2. `.claude/alfred-handoff.json` si existe
3. `docs/project/discovery.md` si existe
4. `docs/project/current.md` si existe
5. `docs/project/codebase-map.md` si existe
6. `.claude/alfred-dev.local.md` si existe

1. Resuelve el refinado **tú mismo por defecto**, aplicando el marco mental de
   `product-owner` sin abrir subagentes de entrada.

2. Solo si hay ambigüedad persistente, análisis competitivo o una necesidad de
   producto que realmente no puedas cerrar tú solo, lanza al `product-owner`
   como apoyo puntual.

3. Si la petición toca interfaz, copy o localización, añade solo los agentes
   opcionales que aporten de verdad y evita abrir más de uno si no es necesario:
   - `ux-reviewer`
   - `copywriter`
   - `i18n-specialist`

4. Trabaja con estas reglas:
   - si `Bash` fue denegado, no vuelvas a intentarlo en este comando;
   - no abras una entrevista larga;
   - solo haz **una** pregunta corta si hay un bloqueo real que cambie el rumbo;
   - si al cierre quedan dos o tres salidas plausibles (`feature`, `quick`, `fix`, `spike`), usa **un único menú seleccionable real** con `AskUserQuestion`; no cierres con bullets ambiguos ni con texto que no se pueda seleccionar;
   - si faltan detalles menores, explicita supuestos razonables y sigue;
   - si la idea ya está suficientemente clara, produce el refinado directamente.

5. Solo en modo manual, actualiza `docs/project/discovery.md` con estas secciones mínimas:
   - problema y objetivo
   - actor principal
   - alcance propuesto
   - fuera de alcance
   - decisiones ya tomadas
   - supuestos
   - preguntas abiertas
   - riesgos o puntos delicados
   - comando recomendado

6. Solo en modo manual, actualiza `docs/project/current.md` con una lectura operativa breve:
   - estado actual del refinado
   - qué falta para empezar a trabajar
   - siguiente comando recomendado

## Decisión de salida

Al cerrar, deja uno de estos siguientes pasos:

- `/alfred-dev:feature` si ya hay suficiente claridad para abrir PRD e implementación completa
- `/alfred-dev:quick` si el cambio resultante es pequeño y acotado
- `/alfred-dev:fix` si lo que en realidad hay es una corrección concreta
- `/alfred-dev:spike` si siguen faltando datos técnicos y toca investigar

Si hay más de una salida razonable de verdad, presenta solo esas rutas en un único menú navegable y deja una recomendada cuando corresponda.

## Restricciones

- NO generes todavía un PRD formal completo salvo que el usuario te lo pida.
- NO abras arquitectura ni implementación dentro de `/alfred-dev:discuss`.
- NO uses `AskUserQuestion` por defecto.
- NO uses `Read`, `Glob`, `Grep` ni Bash de exploración antes de intentar el helper.
- Si `Bash` fue denegado para el helper, NO reintentes `Bash` en este comando.
- Si el helper ya persistió `discovery.md` y `current.md`, NO uses `Write` ni `Edit`
  para reescribirlos en este mismo comando.
- NO lances subagentes por inercia: primero intenta cerrar el refinado tú.
- NO termines con un resumen vago: deja siempre un comando recomendado visible.
