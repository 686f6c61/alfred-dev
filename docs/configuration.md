# Configuración

Alfred Dev esta disenado para adaptarse a cada proyecto sin que el desarrollador tenga que rellenar formularios ni editar ficheros de configuración a mano. Al iniciarse, el plugin analiza el directorio del proyecto, detecta el stack tecnologico y aplica valores por defecto sensatos para cada apartado: autonomía, personalidad, agentes opcionales y memoria. `load_config()` puede funcionar sin fichero local, pero `session-bootstrap.sh` y `session-start.sh` materializan `.claude/alfred-dev.local.md` en la primera sesión para dejar un estado operativo explicito y estable.

Cuando el desarrollador quiere personalizar el comportamiento --ajustar el nivel de autonomía, activar Lucius o cambiar el tono de las respuestas--, puede hacerlo editando `.claude/alfred-dev.local.md` o ejecutando `/alfred-dev:ajustes` desde la interfaz del plugin. El formato combina YAML frontmatter para los valores estructurados con Markdown libre para notas de contexto, lo que permite que el mismo fichero sea legible tanto por humanos como por el parser del plugin. Desde la ronda actual, `/alfred-dev:ajustes` ya no depende solo del prompt: `config_loader.py` expone `build_config_section_summaries()`, `build_config_section_menu()`, `apply_config_section_update()`, `build_config_section_change_preview()`, `update_config_section()` y `update_project_config_section()` para resumir el estado real, construir el menú principal navegable, aplicar cambios por sección, confirmar el diff efectivo y persistir el resultado sin reimplementar el round-trip del fichero.


## Detección automática de stack

Antes de que el desarrollador configure nada, `config_loader.py` ejecuta un análisis del directorio del proyecto buscando ficheros indicadores. La razon de esta detección automática es doble: por un lado, evita que el usuario tenga que declarar manualmente información que ya esta implícita en su proyecto; por otro, permite que los agentes ajusten sus recomendaciones al stack real (un agente de QA no sugiere Vitest en un proyecto Python, ni pytest en uno Node).

El análisis funciona por prioridad. Primero se comprueba el runtime y lenguaje a traves de ficheros raiz, y despues se profundiza leyendo manifiestos de dependencias (`package.json`, `pyproject.toml`, `requirements.txt`, `pom.xml`, `build.gradle`, `composer.json`, `.csproj` y `Package.swift`) para identificar framework, ORM, test runner y bundler cuando el ecosistema lo permite.

### Ficheros indicadores de runtime y lenguaje

El orden de evaluación determina la prioridad. Si un proyecto tiene simultaneamente `package.json` y `pyproject.toml`, se clasifica como Node/JavaScript (o TypeScript si existe `tsconfig.json`), porque la comprobacion de Node va primero en la cadena.

| Fichero indicador    | Runtime detectado | Lenguaje detectado         |
|----------------------|-------------------|----------------------------|
| `package.json`       | node              | javascript (o typescript si existe `tsconfig.json`) |
| `pyproject.toml`     | python            | python                     |
| `setup.py`           | python            | python                     |
| `requirements.txt`   | python            | python                     |
| `Cargo.toml`         | rust              | rust                       |
| `go.mod`             | go                | go                         |
| `Gemfile`            | ruby              | ruby                       |
| `mix.exs`            | elixir            | elixir                     |
| `pom.xml`            | jvm               | java                       |
| `build.gradle`       | jvm               | java                       |
| `build.gradle.kts`   | jvm               | kotlin                     |
| `composer.json`      | php               | php                        |
| `*.csproj` / `*.sln` | dotnet            | csharp                    |
| `Package.swift`      | swift             | swift                      |

### Frameworks detectados

Para proyectos Node, el parser lee `dependencies` y `devDependencies` de `package.json`. Para proyectos Python, busca coincidencias en el texto de `pyproject.toml` y `requirements.txt`. El orden de la lista establece la prioridad: si un proyecto tiene tanto Next como React, se clasifica como Next (que es mas específico).

**Node / JavaScript / TypeScript:**

| Framework detectado | Paquete buscado en dependencias |
|---------------------|---------------------------------|
| next                | `next`                          |
| nuxt                | `nuxt`                          |
| astro               | `astro`                         |
| remix               | `remix`                         |
| gatsby              | `gatsby`                        |
| svelte              | `svelte`                        |
| solid-js            | `solid-js`                      |
| qwik                | `qwik`                          |
| hono                | `hono`                          |
| express             | `express`                       |
| fastify             | `fastify`                       |
| koa                 | `koa`                           |
| nestjs              | `nest` o `@nestjs/core`         |
| vue                 | `vue`                           |
| react               | `react`                         |
| angular             | `angular` o `@angular/core`     |

**Python:**

| Framework detectado | Paquete buscado |
|---------------------|-----------------|
| fastapi             | `fastapi`       |
| django              | `django`        |
| flask               | `flask`         |
| starlette           | `starlette`     |
| litestar            | `litestar`      |
| sanic               | `sanic`         |
| tornado             | `tornado`       |
| aiohttp             | `aiohttp`       |

**Java / Kotlin:**

| Framework detectado | Marcador buscado |
|---------------------|------------------|
| spring-boot         | `spring-boot` o `org.springframework.boot` |
| quarkus             | `quarkus` o `io.quarkus` |
| micronaut           | `micronaut` o `io.micronaut` |

**PHP:**

| Framework detectado | Paquete buscado |
|---------------------|-----------------|
| laravel             | `laravel/framework` |
| symfony             | `symfony/framework-bundle` |
| slim                | `slim/slim` |

**C# / .NET:**

| Framework detectado | Marcador buscado |
|---------------------|------------------|
| aspnet              | `Microsoft.NET.Sdk.Web` |
| blazor              | `Microsoft.AspNetCore.Components.WebAssembly` o `blazor` |

**Swift:**

| Framework detectado | Marcador buscado |
|---------------------|------------------|
| vapor               | `vapor` en `Package.swift` |

### ORMs detectados

**Node:**

| ORM detectado | Paquete buscado                     |
|---------------|-------------------------------------|
| drizzle       | `drizzle-orm`                       |
| prisma        | `prisma` o `@prisma/client`         |
| typeorm       | `typeorm`                           |
| sequelize     | `sequelize`                         |
| knex          | `knex`                              |
| mongoose      | `mongoose`                          |
| mikro-orm     | `mikro-orm` o `@mikro-orm/core`     |

**Python:**

| ORM detectado | Paquete buscado |
|---------------|-----------------|
| sqlalchemy    | `sqlalchemy`    |
| sqlmodel      | `sqlmodel`      |
| django-orm    | `django`        |
| tortoise      | `tortoise`      |
| peewee        | `peewee`        |
| pony          | `pony`          |

**PHP / .NET:**

| ORM detectado | Paquete o marcador buscado |
|---------------|----------------------------|
| doctrine      | `doctrine/orm`             |
| entity-framework | `Microsoft.EntityFrameworkCore` |

### Test runners detectados

**Node:**

| Test runner | Paquete buscado |
|-------------|-----------------|
| vitest      | `vitest`        |
| jest        | `jest`          |
| mocha       | `mocha`         |
| ava         | `ava`           |
| tap         | `tap`           |
| playwright  | `playwright`    |
| cypress     | `cypress`       |

**Python:**

| Test runner | Paquete buscado |
|-------------|-----------------|
| pytest      | `pytest`        |
| unittest    | `unittest`      |
| nose        | `nose`          |

**Otros ecosistemas:**

| Test runner | Marcador buscado |
|-------------|------------------|
| junit       | `junit` en Maven/Gradle |
| kotest      | `kotest` en Maven/Gradle |
| phpunit     | `phpunit/phpunit` en Composer |
| pest        | `pestphp/pest` en Composer |
| xunit       | `xunit` en `.csproj` |
| nunit       | `nunit` en `.csproj` |
| mstest      | `mstest` en `.csproj` |
| swift-test  | `.testTarget` o `swift-testing` en `Package.swift` |

### Bundlers detectados (solo Node)

| Bundler   | Paquete buscado |
|-----------|-----------------|
| vite      | `vite`          |
| webpack   | `webpack`       |
| esbuild   | `esbuild`       |
| rollup    | `rollup`        |
| parcel    | `parcel`        |
| turbopack | `turbopack`     |
| tsup      | `tsup`          |
| unbuild   | `unbuild`       |


## Fichero de configuración

La configuración de Alfred Dev vive en `.claude/alfred-dev.local.md`, dentro del directorio del proyecto. Se utiliza el formato YAML frontmatter (delimitado por `---`) para los valores estructurados, seguido de contenido Markdown libre para notas y contexto adicional.

La razon de este formato hibrido es practica: YAML cubre la configuración tipada (booleanos, números, listas), mientras que el cuerpo Markdown permite al desarrollador añadir instrucciones en lenguaje natural que Alfred inyecta en su contexto. El fichero es editable a mano, pero la forma recomendada de gestionarlo es a traves del comando `/alfred-dev:ajustes`, que guia al usuario por cada sección de forma interactiva. El menú principal de secciones y sus descripciones ya salen de `build_config_section_menu()` / `build_config_section_summaries()`, la confirmación de cambios puede apoyarse en `build_config_section_change_preview()`, y la persistencia final en `update_config_section()` / `update_project_config_section()`, así que la UX de `ajustes` no depende de reescribir a mano el estado actual, el diff esperado ni el guardado final en cada prompt.

La fusion con los valores por defecto es recursiva: el desarrollador solo necesita definir las claves que quiere cambiar. El resto se hereda automáticamente del `DEFAULT_CONFIG` del plugin. El runtime acepta alias legacy como `autonomía`, pero la escritura canónica del plugin es `autonomia`.

El menú principal de `/alfred-dev:ajustes` expone estas 7 secciones canónicas:
Autonomía por fase, Proyecto, Agentes opcionales, Memoria persistente,
Compliance, Integraciones y Personalidad.

### Sección `autonomia`

La autonomía controla cuanto puede decidir el plugin por su cuenta en cada fase canónica del flujo de trabajo. Cada clave representa una fase real del orquestador y acepta uno de los tres niveles de autonomía descritos mas adelante en este documento.

| Clave            | Descripción                                                     | Valor por defecto |
|------------------|-----------------------------------------------------------------|-------------------|
| `producto`       | Descubrimiento y definición funcional                            | `autonomo`        |
| `arquitectura`   | Diseño técnico y validación arquitectónica                       | `autonomo`        |
| `desarrollo`     | Implementación, TDD y cambios de código                          | `autonomo`        |
| `calidad`        | QA, seguridad operativa y revisión de calidad                    | `autonomo`        |
| `documentacion`  | Documentación y artefactos de soporte                            | `autonomo`        |
| `entrega`        | Validación final, ship y cierre                                  | `autonomo`        |

Alias legacy aceptados al leer configuración existente:

- `refactor` -> `desarrollo`
- `tests` -> `calidad`
- `docs` / `documentación` -> `documentacion`
- `devops` -> `entrega`
- `seguridad` -> se proyecta sobre `arquitectura`, `calidad` y `entrega`

Ejemplo:

```yaml
autonomia:
  producto: interactivo
  arquitectura: interactivo
  desarrollo: semi-autonomo
  calidad: semi-autonomo
  documentacion: autonomo
  entrega: semi-autonomo
```

### Sección `proyecto`

Metadatos del proyecto. Normalmente se rellenan automáticamente con `detect_stack()`, pero el desarrollador puede sobreescribirlos si la detección no es precisa o si quiere forzar un valor concreto.

| Clave         | Descripción                        | Valor por defecto |
|---------------|------------------------------------|-------------------|
| `runtime`     | Entorno de ejecución               | `desconocido`     |
| `lenguaje`    | Lenguaje principal                  | `desconocido`     |
| `framework`   | Framework web o de aplicación       | `desconocido`     |
| `orm`         | ORM o query builder                 | `ninguno`         |
| `test_runner` | Framework de tests                  | `desconocido`     |
| `bundler`     | Bundler o empaquetador              | `desconocido`     |

Ejemplo:

```yaml
proyecto:
  runtime: node
  lenguaje: typescript
  framework: next
  orm: prisma
  test_runner: vitest
  bundler: vite
```

### Sección `personalidad`

Define el tono y el estilo de comunicación de los agentes. Los detalles de cada nivel de sarcasmo se explican en la sección dedicada mas adelante.

| Clave             | Descripción                                          | Valor por defecto |
|-------------------|------------------------------------------------------|-------------------|
| `nivel_sarcasmo`  | Nivel de sarcasmo de 1 (formal) a 5 (acido)          | `3`               |
| `verbosidad`      | Nivel de detalle en las respuestas: `normal`, etc.    | `normal`          |
| `idioma`          | Idioma de las respuestas                              | `es`              |
| `celebrar_victorias` | Celebrar cuando se completan fases o flujos        | `true`            |
| `insultar_malas_practicas` | Comentar con sarcasmo las malas practicas     | `true`            |

Ejemplo:

```yaml
personalidad:
  nivel_sarcasmo: 4
  celebrar_victorias: true
  insultar_malas_practicas: true
```

### Sección `agentes_opcionales`

Activa o desactiva el único agente opcional del runtime. Lucius viene desactivado por defecto.

| Clave                    | Rol del agente                              | Valor por defecto |
|--------------------------|---------------------------------------------|-------------------|
| `lucius`                 | Director técnico externo (segunda opinión)  | `false`           |

Ejemplo:

```yaml
agentes_opcionales:
  lucius: false
```

La memoria persistente no depende de un agente bibliotecario. Activar `memoria.enabled` hace que Alfred registre y exponga historial; las consultas van por MCP o `/alfred-dev:memory-ui`.

### Sección `memoria`

Controla la memoria persistente del proyecto. Cuando esta activa, Alfred registra decisiones de diseño, commits e iteraciones en una base de datos SQLite local (`.claude/alfred-memory.db`). Los detalles completos se explican en la sección dedicada mas adelante.

| Clave               | Descripción                                      | Valor por defecto |
|----------------------|--------------------------------------------------|-------------------|
| `enabled`            | Activa o desactiva la memoria persistente        | `false` en `load_config()` |
| `sync_to_native`     | Proyectar SQLite a memorias `.md` nativas de Claude Code | `true` |
| `sync_commits_limit` | Numero de commits recientes a proyectar en la memoria nativa | `10` |
| `capture_decisions`  | Registrar decisiones de diseño automáticamente   | `true`            |
| `capture_commits`    | Registrar commits automáticamente                | `true`            |
| `retention_days`     | Dias de retención de eventos (las decisiones se conservan siempre) | `365` |

Ejemplo:

```yaml
memoria:
  enabled: true
  sync_to_native: true
  sync_commits_limit: 10
  capture_decisions: true
  capture_commits: true
  retention_days: 365
```

Aunque `DEFAULT_MEMORY_CONFIG` parte de `enabled: false`, la primera sesión del proyecto siembra `.claude/alfred-dev.local.md` con `memoria.enabled: true` si el fichero local no existía. A partir de ese momento, cualquier `enabled: false` explícito del usuario se respeta y no se vuelve a sobrescribir.

### Sección `compliance`

Reglas de cumplimiento y estilo de código.

| Clave            | Descripción                                | Valor por defecto |
|------------------|-------------------------------------------|-------------------|
| `estilo`         | Guia de estilo: `auto` detecta la del proyecto | `auto`        |
| `lint`           | Ejecutar linter automáticamente            | `true`            |
| `format_on_save` | Formatear al guardar                       | `true`            |

### Sección `integraciones`

Servicios externos habilitados.

| Clave    | Descripción                           | Valor por defecto |
|----------|---------------------------------------|-------------------|
| `git`    | Integración con Git                   | `true`            |
| `ci`     | Integración con CI/CD                 | `false`           |
| `deploy` | Integración con despliegue            | `false`           |

### Contexto adicional (notas)

El cuerpo Markdown del fichero, despues del cierre del frontmatter (`---`), se utiliza como notas de texto libre. Si existe una sección con cabecera que contenga la palabra "Notas", Alfred extrae su contenido y lo inyecta en el contexto del sistema. Esto permite al desarrollador dar instrucciones en lenguaje natural que complementan la configuración estructurada.

Ejemplo de uso típico: indicar convenciones del equipo, restricciones de negocio o preferencias que no encajan en ninguna sección YAML.


## Niveles de autonomía

La autonomía es uno de los conceptos mas importantes de Alfred Dev porque determina hasta que punto el plugin puede tomar decisiones sin pedir permiso. La razon de ofrecer varios niveles es que cada equipo y cada fase del desarrollo tienen necesidades distintas: la fase de producto requiere validación humana constante (los requisitos son decisiones de negocio), mientras que la ejecución de tests es mecánica y no necesita supervision.

Alfred Dev define tres niveles de autonomía que se aplican a cada fase de forma independiente. Esto significa que un mismo proyecto puede tener `producto` en modo interactivo y `documentacion` en modo autonomo.

### Interactivo

En este nivel, Alfred pide confirmacion en cada gate antes de avanzar. Es el modo mas conservador y el recomendado para fases donde las decisiones tienen impacto directo en el negocio o la arquitectura.

En la practica, durante un flujo `/alfred-dev:feature`:

- **Producto**: Alfred presenta los requisitos y la historia de usuario, y espera a que el desarrollador los apruebe antes de pasar a arquitectura.
- **Arquitectura**: El diseño técnico y el threat model se presentan para revision. No se empieza a codificar hasta que el desarrollador da el visto bueno.
- **Desarrollo**: Si `desarrollo` esta en interactivo, los cambios estructurales relevantes se proponen antes de aplicarse.
- **Entrega**: El changelog y la validación final requieren aprobacion explícita.

### Semi-autonomo

En este nivel, las gates automáticas (las que dependen de metricas objetivas como tests verdes o pipeline OK) se pasan sin preguntar, pero las gates de usuario (las que requieren juicio humano) siguen pidiendo confirmacion.

Es el nivel recomendado cuando el desarrollador confia en la infraestructura de calidad del proyecto (buena cobertura de tests, linters configurados) pero quiere mantener el control sobre las decisiones de producto y arquitectura.

En la practica:

- **Desarrollo**: Si los tests pasan, la gate se supera automáticamente sin intervencion. Si fallan, se detiene y se informa.
- **Calidad**: La auditoría de calidad y seguridad se ejecutan y, si ambas pasan, el flujo avanza solo.
- **Producto y arquitectura**: Siguen pidiendo confirmacion porque son gates de tipo `usuario`.

### Autonomo

Todo se ejecuta sin interrupciones. El flujo solo se detiene ante errores críticos (tests que fallan, auditoría de seguridad que no pasa). Es el nivel para desarrolladores experimentados que quieren velocidad máxima y confian plenamente en los agentes.

En la practica:

- Todas las fases avanzan automáticamente mientras las condiciones de la gate se cumplan.
- Las unicas paradas son por fallos reales: tests rojos, vulnerabilidades detectadas o errores de build.
- El desarrollador puede revisar el resultado completo al final del flujo en lugar de fase por fase.

### Tipos de gate en el orquestador

Para entender como la autonomía interactua con cada fase, conviene conocer los tipos de gate que define el orquestador. Cada fase de un flujo tiene un tipo de gate que determina las condiciones necesarias para avanzar:

| Tipo de gate             | Condiciones para pasar                                                    |
|--------------------------|---------------------------------------------------------------------------|
| `libre`                  | Requiere resultado favorable y evidencia/checklist; no pide aprobacion humana. |
| `usuario`                | Requiere aprobacion explícita del desarrollador.                           |
| `automático`             | Requiere que los tests pasen y el resultado sea favorable.                 |
| `usuario+seguridad`      | Requiere aprobacion del desarrollador y auditoría de seguridad positiva.   |
| `automático+seguridad`   | Requiere tests verdes, seguridad OK y resultado favorable.                 |

El nivel de autonomía modifica el comportamiento de las gates de tipo `usuario`: en modo interactivo, siempre se pide confirmacion; en semi-autonomo, solo las de usuario; en autonomo, ninguna (salvo fallo en las condiciones automáticas). La excepción explícita es `ship:despliegue`: aunque el flujo esté en autopilot, esa fase mantiene confirmación humana obligatoria antes de publicar.


## Descubrimiento de agentes opcionales

Alfred Dev incluye 8 agentes de nucleo más Selina si hay frontend. El único opcional es Lucius. El kanban lo escribe el runtime, no un agente aparte.

La función `suggest_optional_agents()` en `config_loader.py` no propone el catálogo 0.6. Lucius no se decide por I/O del proyecto: su valor depende de si el usuario quiere una segunda opinión externa en un cierre.

### Flujo de activacion

El descubrimiento contextual se ejecuta la primera vez que el desarrollador abre `/alfred-dev:ajustes` en un proyecto nuevo (o cuando Lucius no está configurado). El flujo es:

1. Se detecta el stack con `detect_stack()`.
2. Se ejecuta `suggest_optional_agents()` con el directorio del proyecto y la configuración actual.
3. Se presentan las sugerencias al desarrollador con la razon de cada una.
4. El desarrollador elige cuales activar.
5. La seleccion se guarda en el fichero `.claude/alfred-dev.local.md` bajo la clave `agentes_opcionales`.

Los agentes que no se sugieren también se pueden activar manualmente. El descubrimiento es una ayuda, no una restricción.


## Composicion dinámica de equipo

El descubrimiento de agentes opcionales descrito en la sección anterior resuelve la pregunta «que agentes podrian ser utiles en este proyecto», pero no la pregunta «que agentes necesita esta tarea concreta». Un proyecto Next.js con Prisma siempre tendra las mismas sugerencias, independientemente de si la tarea actual es «añadir pagos con Stripe» o «corregir un typo en el README». La composicion dinámica de equipo cierra esa brecha: analiza la descripción de la tarea del usuario, la combina con las señales del proyecto y la configuración activa, y propone un equipo adaptado a cada ejecución.

La seleccion es efímera: solo aplica a la sesión en curso y no modifica la configuración persistente del fichero `.claude/alfred-dev.local.md`. Esto evita que una tarea puntual contamine la configuración del proyecto para todas las sesiones futuras.

### Las tres capas de la composicion

La composicion dinámica se ejecuta al invocar cualquier flujo y opera en tres capas. El protocolo esta centralizado en `commands/_composicion.md` y todos los comandos lo referencian, eliminando la duplicacion anterior.

```
1. CONTEXTO DEL PROYECTO  (config_loader.py)
   suggest_optional_agents() -- señales basadas en I/O
   --> ORM detectado, frontend, HTML público, remote GitHub, etc.

2. RAZONAMIENTO SEMÁNTICO  (Alfred)
   Alfred analiza la tarea + señales del proyecto y decide
   que agentes son relevantes usando comprension semántica.
   --> preseleccion razonada, no por keywords

3. PRESENTACION + EJECUCIÓN
   Lucius se presenta con AskUserQuestion en un menú del grupo Auditoria.
   Si el usuario no quiere activarlo, elige «Seguir sin activar más».
   --> equipo_sesion efimero
```

La primera capa proporciona señales objetivas del proyecto (I/O de ficheros). La segunda aprovecha la capacidad de comprension semántica de Alfred para decidir que agentes son relevantes para la tarea concreta, sin depender de un diccionario de keywords. La tercera da al usuario la decisión final sobre Lucius.

### Capa de proyecto: suggest_optional_agents

La función `suggest_optional_agents()` en `config_loader.py` analiza el proyecto de forma estática para generar señales contextuales. No analiza la descripción de la tarea; eso lo hace Alfred semanticamente.

`suggest_optional_agents()` ya no propone el catálogo 0.6. El único opcional es Lucius, y queda fuera de las señales estáticas: se activa por contexto de tarea o desde `/alfred-dev:ajustes`, no porque el repo tenga ORM, frontend o remoto GitHub.

### Capa semántica: Alfred como razonador

Alfred analiza la descripción de la tarea con comprension semántica completa. No busca keywords; entiende la intencion. El catalogo de agentes en `commands/_composicion.md` le proporciona el contexto necesario para decidir.

Ejemplos de razonamiento semántico:

| Tarea | Decisión de Alfred | Por que |
|-------|--------------------|---------|
| "Implementar pagos con Stripe" | senior-dev | Entiende que "pagos" es lógica de negocio del nucleo |
| "Dark mode en el dashboard" | selina si hay frontend, luego senior-dev | Entiende que afecta a la interfaz |
| "¿Por que se eligio SQLite?" | memory-ui / MCP | Consulta histórica, no un agente bibliotecario |
| "Segunda opinión antes de cerrar" | lucius | Único opcional, activado por tarea o ajustes |

### Capa de presentacion: todos los agentes visibles

Los comandos presentan Lucius mediante `AskUserQuestion` con un menú del grupo `Auditoria`. El menú se construye como payload actual de Claude Code (`questions[]` con `multiSelect: false`) y conserva `question`/`header`/`options` en raíz solo como compatibilidad interna de lectura. Si el usuario no quiere activarlo, elige `Seguir sin activar más`.

Desde v0.6, esa UX ya no depende solo del prompt: `core/optional_agents.py`
actúa como fuente canónica del menú con `build_optional_agent_group_menu()` y
`build_optional_agent_group_menus()`, que fijan grupos, orden, labels visibles,
descripciones base y opción de salida.

```
Menú Auditoría:
  Seguir sin activar más
  Lucius            -- "Segunda opinión técnica externa para esta tarea"
```

### Ejecución: equipo efimero en el orquestador

La seleccion del usuario se traduce en un diccionario `equipo_sesion` que se pasa como parámetro opcional a `run_flow()` en `core/orchestrator.py`. La estructura del diccionario es:

```python
equipo_sesion = {
    "opcionales_activos": {
        "lucius": False,
    },
    "infra": {
        "memoria": True,
    },
    "fuente": "composicion_dinamica",
}
```

Antes de inyectar el equipo en la sesión, `run_flow()` lo valida con `_validate_equipo_sesion()`. Las reglas de validación son:

- El primer nivel exige exactamente tres claves: `opcionales_activos`, `infra` y `fuente`.
- `opcionales_activos` exige como mínimo la clave `lucius`. Acepta claves extra con aviso a stderr, lo que permite extensiones futuras sin romper la validación.
- `infra` exige exactamente `memoria`, de tipo booleano.
- `fuente` debe ser una fuente runtime reconocida: `"composicion_dinamica"` para composicion efimera o `"config_persistida"` cuando el equipo se deriva de `.claude/alfred-dev.local.md`.

Si la validación falla, el equipo se descarta con un aviso a stderr y el motivo se registra en `session["equipo_sesion_error"]` para que los consumidores downstream puedan informar al usuario. Si existía configuración persistida válida en el proyecto, `run_flow()` hace fallback a esa configuración antes de quedarse sin equipo.

### Retrocompatibilidad

La composicion dinámica es un camino nuevo, no un reemplazo del existente. Si `equipo_sesion` no se pasa a `run_flow()`, el orquestador intenta derivar el equipo desde la configuración persistente del proyecto actual (o del `project_dir` explícito si se pasa). Un proyecto que ya tiene agentes configurados en `.claude/alfred-dev.local.md` sigue funcionando sin cambios y deja ese equipo reflejado también en `alfred-dev-state.json`.

Los mecanismos de seleccion de agentes opcionales coexisten:

| Mecanismo | Persistencia | Contexto |
|-----------|--------------|----------|
| `/alfred-dev:ajustes` | Persistente (fichero `.local.md`) | Proyecto |
| Descubrimiento (`suggest_optional_agents`) | Persistente (se guarda al confirmar) | Proyecto |
| Composicion dinámica (Alfred semántico) | Efímera (solo la sesión) | Tarea |

### Ficheros involucrados

| Fichero | Componente | Rol en la composicion dinámica |
|---------|------------|--------------------------------|
| `commands/_composicion.md` | Protocolo compartido | Catalogo de agentes, criterios de decisión, formato de presentacion |
| `core/config_loader.py` | `suggest_optional_agents()` | Señales de proyecto basadas en I/O |
| `core/orchestrator.py` | `_validate_equipo_sesion()` | Validación de la estructura del equipo efimero |
| `core/orchestrator.py` | `run_flow()` | Punto de entrada con inyección de equipo de sesión |
| `commands/*.md` | Skills de cada flujo | Referencian `_composicion.md` y arrancan flujo con equipo |


## Configuración de memoria

La memoria persistente es una capa lateral que permite a Alfred Dev conservar el historial del proyecto entre sesiones: decisiones de diseño, commits, iteraciones y eventos del flujo de trabajo. Sin memoria, cada sesión de Alfred empieza de cero; con memoria, el plugin puede responder preguntas como "por que decidimos usar SQLite en vez de PostgreSQL" o "que se implemento en la iteracion 3" con evidencia verificable.

La razón de que siga siendo configurable es que no todos los proyectos necesitan la misma persistencia. Un script de 50 lineas no necesita la misma trazabilidad que un producto con varias iteraciones y decisiones arquitectonicas. Por eso el primer arranque la activa para ofrecer continuidad desde el minuto uno, pero el usuario puede desactivarla en cuanto quiera con `memoria.enabled: false`.

### Activacion

Para activar la memoria, se añade la sección `memoria` al frontmatter del fichero de configuración con `enabled: true`. También se puede activar de forma interactiva con `/alfred-dev:ajustes` eligiendo la sección de memoria. Si el proyecto nunca tuvo fichero local, los hooks de arranque ya lo habrán sembrado con `enabled: true`; desactivarla consiste en escribir `enabled: false`, no en borrar la base de datos.

Al activarse, Alfred crea automáticamente la base de datos SQLite en `.claude/alfred-memory.db` con permisos `0600` (solo el propietario puede leer y escribir). El esquema incluye tablas para iteraciones, decisiones, commits, eventos y vinculos entre commits y decisiones.

### Que captura

La memoria captura dos tipos de información controlados por su propia clave de configuración:

- **`sync_to_native`**: cuando esta activo, Alfred proyecta decisiones, iteracion activa, resumen y commits recientes a `~/.claude/projects/<hash>/memory/` con formato nativo de Claude Code. Si se desactiva, SQLite sigue siendo la fuente de verdad pero no se generan los `.md`.

- **`sync_commits_limit`**: controla cuantos commits recientes se proyectan al fichero nativo `alfred-commits-recent.md`. No limita la memoria SQLite; solo la vista resumida para Claude Code.

- **`capture_decisions`**: cuando esta activo, las llamadas a `memory_log_decision` persisten decisiones en SQLite y quedan disponibles para MCP, Memory UI, la sync nativa y las consultas historicas. Si se desactiva, Alfred responde con `skipped` y no escribe la decision.

- **`capture_commits`**: cuando esta activo, el hook de actividad registra `git commit` y la herramienta MCP `memory_log_commit` persiste commits con SHA, mensaje, autor y ficheros afectados. Si se desactiva, la captura se omite sin tocar la DB.

Además, la memoria registra automáticamente eventos del flujo de trabajo (fases completadas, gates superadas, aprobaciones) que permiten reconstruir la cronología detallada de cada iteracion.

### Retención

La clave `retention_days` controla cuantos dias se conservan los eventos del flujo. Pasado ese periodo, los eventos antiguos se purgan automáticamente. Sin embargo, las decisiones e iteraciones no se borran nunca, porque su valor para la trazabilidad es permanente: saber por que se tomo una decisión hace seis meses es tan util como saber por que se tomo ayer.

El valor por defecto es 365 dias. Para proyectos de larga duracion, se puede aumentar sin limite. Para proyectos efimeros, se puede reducir a 30 o 60 dias.

### Busqueda

La memoria soporta dos modos de busqueda, determinados automáticamente por las capacidades del entorno SQLite:

- **FTS5 (busqueda de texto completo)**: si el entorno SQLite soporta la extensión FTS5, la memoria crea automáticamente una tabla virtual con índice de texto completo que indexa decisiones, commits y eventos con contenido. Las busquedas son rapidas y soportan frases literales.

- **LIKE (fallback básico)**: si FTS5 no esta disponible, las busquedas se realizan con `LIKE %termino%`, que es mas lento pero funcional en cualquier entorno SQLite.

La detección del modo es automática al inicializar la base de datos. El plugin registra el resultado en la tabla `meta` para que MCP y Memory UI sepan que modo esta activo sin tener que volver a comprobarlo.

### Consulta de memoria

No hay agente `librarian`. Las consultas van por el servidor MCP (`alfred-memory`) o por `/alfred-dev:memory-ui`. Las citas verificables usan `[D#12]`, `[C#a1b2c3d]` e `[I#5]` cuando el runtime o el visor muestran un registro concreto.


## Personalidad

La personalidad de los agentes es uno de los aspectos que distingue a Alfred Dev de un asistente genérico. Cada agente tiene un perfil único con nombre, rol, frases caracteristicas y un tono que se adapta al nivel de sarcasmo configurado por el desarrollador. La razon de ofrecer esta personalizacion es que el tono afecta directamente a la experiencia de uso: un desarrollador que lleva ocho horas depurando un bug necesita un tono diferente al de alguien que esta explorando ideas en un spike.

### Niveles de sarcasmo

El nivel de sarcasmo es un entero de 1 a 5 que modifica el tono de todos los agentes de forma coherente. No cambia lo que dicen los agentes (sus recomendaciones técnicas son las mismas), sino como lo dicen.

| Nivel | Etiqueta         | Descripción                                                                                              |
|-------|------------------|----------------------------------------------------------------------------------------------------------|
| 1     | Formal           | Tono profesional y neutro. Las respuestas son directas, sin humor ni coletillas. Ideal para entornos corporativos o documentación oficial. |
| 2     | Cordial          | Ligeramente mas cercano que el formal. Algun comentario amable, pero sin chistes. Adecuado para equipos que prefieren un tono serio pero no frio. |
| 3     | Colega (defecto) | El punto medio. Los agentes se expresan con naturalidad, alguna broma puntual y un tono de compañero de equipo. Es el valor por defecto. |
| 4     | Mordaz           | Los agentes empiezan a soltar comentarios acidos. Las malas practicas se senalan con ironia y las frases de sarcasmo alto se añaden al repertorio. |
| 5     | Erudito ironico  | Sarcasmo máximo. Los agentes no se cortan: comentarios acidos, ironia elaborada y críticas con estilo. Solo para desarrolladores que aprecian el humor negro técnico. |

Tecnicamente, el umbral esta en el nivel 4. A partir de ese nivel, la función `get_agent_voice()` del modulo `personality.py` añade las frases de `frases_sarcasmo_alto` al repertorio del agente, y `get_agent_intro()` incluye una coletilla acida en la presentacion. Por debajo de 4, solo se usan las frases base.

### Celebrar victorias

Cuando `celebrar_victorias` esta activo (`true`), los agentes reaccionan de forma positiva al completar fases y flujos: reconocen el progreso, destacan los hitos y animan al equipo. Cuando esta desactivado, el avance se comunica de forma factual sin celebraciones.

La razon de este ajuste es que no todos los desarrolladores responden igual al refuerzo positivo. Algunos lo valoran; otros lo perciben como ruido. Dejarlo configurable respeta ambas preferencias.

### Insultar malas practicas

Cuando `insultar_malas_practicas` esta activo y el nivel de sarcasmo es suficientemente alto (>= 4), los agentes comentan con ironia las practicas cuestionables que detectan: un `SELECT *` sin `WHERE`, un push directo a main, un README vacio o un token en el repositorio. Es una forma de senalar problemas con humor, no con hostilidad. Si se desactiva, los agentes informan de los problemas sin el componente sarcastico.


## Ejemplo completo de fichero `.claude/alfred-dev.local.md`

El siguiente ejemplo muestra un fichero de configuración con todas las secciones definidas. En la practica, el desarrollador solo necesita incluir las secciones que quiere personalizar; todo lo demas hereda los valores por defecto.

```yaml
---
autonomia:
  producto: interactivo
  arquitectura: interactivo
  desarrollo: semi-autonomo
  calidad: semi-autonomo
  documentacion: autonomo
  entrega: semi-autonomo

proyecto:
  runtime: node
  lenguaje: typescript
  framework: next
  orm: prisma
  test_runner: vitest
  bundler: vite

agentes_opcionales:
  lucius: false

memoria:
  enabled: true
  sync_to_native: true
  sync_commits_limit: 10
  capture_decisions: true
  capture_commits: true
  retention_days: 365

personalidad:
  nivel_sarcasmo: 3
  verbosidad: normal
  idioma: es
  celebrar_victorias: true
  insultar_malas_practicas: true

compliance:
  estilo: auto
  lint: true
  format_on_save: true

integraciones:
  git: true
  ci: false
  deploy: false
---

## Notas

Este proyecto usa el App Router de Next.js 15 con Server Components por defecto.
Las rutas de API estan en `app/api/` y usan Hono como framework HTTP.
La base de datos es PostgreSQL gestionada con Prisma; las migraciones se aplican
con `prisma migrate deploy` en el pipeline de CI.

Convenciones del equipo:
- Los componentes de UI van en `components/ui/` con barrel exports.
- Los hooks personalizados en `hooks/` con prefijo `use`.
- Las utilidades compartidas en `lib/` con tests unitarios obligatorios.
- Los mensajes de commit siguen la convencion de tipos semanticos (feat, fix, refactor, etc.).
```
