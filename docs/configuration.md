# Configuracion

Alfred Dev esta disenado para adaptarse a cada proyecto sin que el desarrollador tenga que rellenar formularios ni editar ficheros de configuracion a mano. Al iniciarse, el plugin analiza el directorio del proyecto, detecta el stack tecnologico y aplica valores por defecto sensatos para cada apartado: autonomia, personalidad, agentes opcionales y memoria. Todo es opcional. Un proyecto sin fichero de configuracion funciona igual de bien que uno con todas las secciones definidas, porque los valores por defecto cubren el caso general.

Cuando el desarrollador quiere personalizar el comportamiento --ajustar el nivel de autonomia, activar agentes especializados o cambiar el tono de las respuestas--, puede hacerlo creando un fichero `.claude/alfred-dev.local.md` en la raiz del proyecto o ejecutando `/alfred config` desde la interfaz del plugin. El formato combina YAML frontmatter para los valores estructurados con Markdown libre para notas de contexto, lo que permite que el mismo fichero sea legible tanto por humanos como por el parser del plugin.


## Deteccion automatica de stack

Antes de que el desarrollador configure nada, `config_loader.py` ejecuta un analisis del directorio del proyecto buscando ficheros indicadores. La razon de esta deteccion automatica es doble: por un lado, evita que el usuario tenga que declarar manualmente informacion que ya esta implicita en su proyecto; por otro, permite que los agentes ajusten sus recomendaciones al stack real (un agente de QA no sugiere Vitest en un proyecto Python, ni pytest en uno Node).

El analisis funciona por prioridad. Primero se comprueba el runtime y lenguaje a traves de ficheros raiz, y despues se profundiza leyendo manifiestos de dependencias (package.json, pyproject.toml, requirements.txt) para identificar framework, ORM, test runner y bundler.

### Ficheros indicadores de runtime y lenguaje

El orden de evaluacion determina la prioridad. Si un proyecto tiene simultaneamente `package.json` y `pyproject.toml`, se clasifica como Node/JavaScript (o TypeScript si existe `tsconfig.json`), porque la comprobacion de Node va primero en la cadena.

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

### Frameworks detectados

Para proyectos Node, el parser lee `dependencies` y `devDependencies` de `package.json`. Para proyectos Python, busca coincidencias en el texto de `pyproject.toml` y `requirements.txt`. El orden de la lista establece la prioridad: si un proyecto tiene tanto Next como React, se clasifica como Next (que es mas especifico).

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


## Fichero de configuracion

La configuracion de Alfred Dev vive en `.claude/alfred-dev.local.md`, dentro del directorio del proyecto. Se utiliza el formato YAML frontmatter (delimitado por `---`) para los valores estructurados, seguido de contenido Markdown libre para notas y contexto adicional.

La razon de este formato hibrido es practica: YAML cubre la configuracion tipada (booleanos, numeros, listas), mientras que el cuerpo Markdown permite al desarrollador anadir instrucciones en lenguaje natural que Alfred inyecta en su contexto. El fichero es editable a mano, pero la forma recomendada de gestionarlo es a traves del comando `/alfred config`, que guia al usuario por cada seccion de forma interactiva.

La fusion con los valores por defecto es recursiva: el desarrollador solo necesita definir las claves que quiere cambiar. El resto se hereda automaticamente del `DEFAULT_CONFIG` del plugin. Esto significa que un fichero con una sola linea (`nivel_sarcasmo: 5`) es perfectamente valido.

### Seccion `autonomia`

La autonomia controla cuanto puede decidir el plugin por su cuenta en cada area funcional del flujo de trabajo. Cada clave representa un dominio y acepta uno de los tres niveles de autonomia descritos mas adelante en este documento.

| Clave        | Descripcion                                           | Valor por defecto |
|--------------|-------------------------------------------------------|-------------------|
| `producto`   | Fase de producto: requisitos, historias de usuario     | `interactivo`     |
| `seguridad`  | Auditorias de seguridad, threat models                 | `autonomo`        |
| `refactor`   | Refactorizaciones y limpieza de codigo                 | `interactivo`     |
| `docs`       | Generacion de documentacion                            | `autonomo`        |
| `tests`      | Ejecucion y generacion de tests                        | `autonomo`        |

Ejemplo:

```yaml
autonomia:
  producto: interactivo
  seguridad: autonomo
  refactor: semi-autonomo
  docs: autonomo
  tests: autonomo
```

### Seccion `proyecto`

Metadatos del proyecto. Normalmente se rellenan automaticamente con `detect_stack()`, pero el desarrollador puede sobreescribirlos si la deteccion no es precisa o si quiere forzar un valor concreto.

| Clave         | Descripcion                        | Valor por defecto |
|---------------|------------------------------------|-------------------|
| `runtime`     | Entorno de ejecucion               | `desconocido`     |
| `lenguaje`    | Lenguaje principal                  | `desconocido`     |
| `framework`   | Framework web o de aplicacion       | `desconocido`     |
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

### Seccion `personalidad`

Define el tono y el estilo de comunicacion de los agentes. Los detalles de cada nivel de sarcasmo se explican en la seccion dedicada mas adelante.

| Clave             | Descripcion                                          | Valor por defecto |
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

### Seccion `agentes_opcionales`

Activa o desactiva los agentes opcionales del plugin. Cada agente es un especialista que se incorpora a los flujos cuando esta activado. Todos vienen desactivados por defecto y se activan segun las necesidades del proyecto.

| Clave                    | Rol del agente                              | Valor por defecto |
|--------------------------|---------------------------------------------|-------------------|
| `data-engineer`          | Ingeniero de datos (esquemas, migraciones)  | `false`           |
| `ux-reviewer`            | Revisor de UX (accesibilidad, flujos)       | `false`           |
| `performance-engineer`   | Ingeniero de rendimiento (profiling)        | `false`           |
| `github-manager`         | Gestor de GitHub (PRs, issues, releases)    | `false`           |
| `seo-specialist`         | Especialista SEO (meta tags, Core Vitals)   | `false`           |
| `copywriter`             | Copywriter (CTAs, tono, textos publicos)    | `false`           |
| `librarian`              | Bibliotecario (memoria persistente)         | `false`           |

Ejemplo:

```yaml
agentes_opcionales:
  data-engineer: true
  ux-reviewer: false
  performance-engineer: false
  github-manager: true
  seo-specialist: false
  copywriter: false
  librarian: true
```

### Seccion `memoria`

Controla la memoria persistente del proyecto. Cuando esta activa, Alfred registra decisiones de diseno, commits e iteraciones en una base de datos SQLite local (`.claude/alfred-memory.db`). Los detalles completos se explican en la seccion dedicada mas adelante.

| Clave               | Descripcion                                      | Valor por defecto |
|----------------------|--------------------------------------------------|-------------------|
| `enabled`            | Activa o desactiva la memoria persistente        | `false`           |
| `capture_decisions`  | Registrar decisiones de diseno automaticamente   | `true`            |
| `capture_commits`    | Registrar commits automaticamente                | `true`            |
| `retention_days`     | Dias de retencion de eventos (las decisiones se conservan siempre) | `365` |

Ejemplo:

```yaml
memoria:
  enabled: true
  capture_decisions: true
  capture_commits: true
  retention_days: 365
```

### Seccion `compliance`

Reglas de cumplimiento y estilo de codigo.

| Clave            | Descripcion                                | Valor por defecto |
|------------------|-------------------------------------------|-------------------|
| `estilo`         | Guia de estilo: `auto` detecta la del proyecto | `auto`        |
| `lint`           | Ejecutar linter automaticamente            | `true`            |
| `format_on_save` | Formatear al guardar                       | `true`            |

### Seccion `integraciones`

Servicios externos habilitados.

| Clave    | Descripcion                           | Valor por defecto |
|----------|---------------------------------------|-------------------|
| `git`    | Integracion con Git                   | `true`            |
| `ci`     | Integracion con CI/CD                 | `false`           |
| `deploy` | Integracion con despliegue            | `false`           |

### Contexto adicional (notas)

El cuerpo Markdown del fichero, despues del cierre del frontmatter (`---`), se utiliza como notas de texto libre. Si existe una seccion con cabecera que contenga la palabra "Notas", Alfred extrae su contenido y lo inyecta en el contexto del sistema. Esto permite al desarrollador dar instrucciones en lenguaje natural que complementan la configuracion estructurada.

Ejemplo de uso tipico: indicar convenciones del equipo, restricciones de negocio o preferencias que no encajan en ninguna seccion YAML.


## Niveles de autonomia

La autonomia es uno de los conceptos mas importantes de Alfred Dev porque determina hasta que punto el plugin puede tomar decisiones sin pedir permiso. La razon de ofrecer varios niveles es que cada equipo y cada fase del desarrollo tienen necesidades distintas: la fase de producto requiere validacion humana constante (los requisitos son decisiones de negocio), mientras que la ejecucion de tests es mecanica y no necesita supervision.

Alfred Dev define tres niveles de autonomia que se aplican a cada dominio funcional de forma independiente. Esto significa que un mismo proyecto puede tener la fase de producto en modo interactivo y la de documentacion en modo autonomo.

### Interactivo (valor por defecto para producto y refactor)

En este nivel, Alfred pide confirmacion en cada gate antes de avanzar. Es el modo mas conservador y el recomendado para fases donde las decisiones tienen impacto directo en el negocio o la arquitectura.

En la practica, durante un flujo `/alfred feature`:

- **Producto**: Alfred presenta los requisitos y la historia de usuario, y espera a que el desarrollador los apruebe antes de pasar a arquitectura.
- **Arquitectura**: El diseno tecnico y el threat model se presentan para revision. No se empieza a codificar hasta que el desarrollador da el visto bueno.
- **Desarrollo**: Si el refactor esta en interactivo, cada cambio estructural se propone antes de aplicarse.
- **Entrega**: El changelog y la validacion final requieren aprobacion explicita.

### Semi-autonomo

En este nivel, las gates automaticas (las que dependen de metricas objetivas como tests verdes o pipeline OK) se pasan sin preguntar, pero las gates de usuario (las que requieren juicio humano) siguen pidiendo confirmacion.

Es el nivel recomendado cuando el desarrollador confia en la infraestructura de calidad del proyecto (buena cobertura de tests, linters configurados) pero quiere mantener el control sobre las decisiones de producto y arquitectura.

En la practica:

- **Desarrollo**: Si los tests pasan, la gate se supera automaticamente sin intervencion. Si fallan, se detiene y se informa.
- **Calidad**: La auditoría de calidad y seguridad se ejecutan y, si ambas pasan, el flujo avanza solo.
- **Producto y arquitectura**: Siguen pidiendo confirmacion porque son gates de tipo `usuario`.

### Autonomo

Todo se ejecuta sin interrupciones. El flujo solo se detiene ante errores criticos (tests que fallan, auditoría de seguridad que no pasa). Es el nivel para desarrolladores experimentados que quieren velocidad maxima y confian plenamente en los agentes.

En la practica:

- Todas las fases avanzan automaticamente mientras las condiciones de la gate se cumplan.
- Las unicas paradas son por fallos reales: tests rojos, vulnerabilidades detectadas o errores de build.
- El desarrollador puede revisar el resultado completo al final del flujo en lugar de fase por fase.

### Tipos de gate en el orquestador

Para entender como la autonomia interactua con cada fase, conviene conocer los tipos de gate que define el orquestador. Cada fase de un flujo tiene un tipo de gate que determina las condiciones necesarias para avanzar:

| Tipo de gate             | Condiciones para pasar                                                    |
|--------------------------|---------------------------------------------------------------------------|
| `libre`                  | Se supera siempre que el resultado sea favorable.                          |
| `usuario`                | Requiere aprobacion explicita del desarrollador.                           |
| `automatico`             | Requiere que los tests pasen y el resultado sea favorable.                 |
| `usuario+seguridad`      | Requiere aprobacion del desarrollador y auditoría de seguridad positiva.   |
| `automatico+seguridad`   | Requiere tests verdes, seguridad OK y resultado favorable.                 |

El nivel de autonomia modifica el comportamiento de las gates de tipo `usuario`: en modo interactivo, siempre se pide confirmacion; en semi-autonomo, solo las de usuario; en autonomo, ninguna (salvo fallo en las condiciones automaticas).


## Descubrimiento de agentes opcionales

Alfred Dev incluye 8 agentes de nucleo que siempre estan activos (Alfred, Product Owner, Arquitecto, Senior Dev, Security Officer, QA, DevOps y Tech Writer) y 7 agentes opcionales que el desarrollador activa segun las necesidades de su proyecto. Los agentes opcionales no son genericos: cada uno esta especializado en un dominio concreto y solo tiene sentido en proyectos que lo necesitan.

La funcion `suggest_optional_agents()` en `config_loader.py` analiza el proyecto y sugiere que agentes opcionales podrian ser utiles. La logica de sugerencia se basa en indicadores objetivos del proyecto, no en preferencias arbitrarias. A continuacion se detalla la logica de cada sugerencia:

### Logica de sugerencias

| Agente sugerido        | Condicion de activacion                                                                     | Razon                                                                         |
|------------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `data-engineer`        | El ORM detectado es distinto de `ninguno`                                                   | Si hay ORM, hay base de datos. El agente ayuda con esquemas, migraciones y queries. |
| `ux-reviewer`          | El framework detectado esta en la lista de frameworks frontend (Next, Nuxt, Astro, Remix, Gatsby, Svelte, Solid, Qwik, Vue, React, Angular) | Si hay interfaz de usuario, tiene sentido revisar accesibilidad y flujos.     |
| `seo-specialist`       | Se detectan ficheros HTML publicos (en raiz, `public/`, `site/`, `dist/` o `docs/`)         | Si hay contenido web publico, el SEO importa para la visibilidad.             |
| `copywriter`           | Se detectan ficheros HTML publicos (misma condicion que SEO)                                 | Los textos publicos necesitan cuidar el tono, los CTAs y la coherencia.       |
| `github-manager`       | El proyecto tiene un remote Git configurado (se lee `.git/config`)                          | Si hay remote, hay PRs, issues y releases que gestionar.                      |
| `performance-engineer` | El proyecto tiene mas de 50 ficheros de codigo fuente (hasta 3 niveles de profundidad)      | Los proyectos grandes se benefician de profiling y optimizacion.              |

El recuento de ficheros fuente ignora directorios de dependencias y artefactos (`node_modules`, `.git`, `dist`, `build`, `.next`, `__pycache__`, `.venv`, `venv`, `vendor`, `target`, `.cargo`) para no inflar artificialmente la cuenta.

### Flujo de activacion

El descubrimiento contextual se ejecuta la primera vez que el desarrollador abre `/alfred config` en un proyecto nuevo (o cuando no hay agentes opcionales activados). El flujo es:

1. Se detecta el stack con `detect_stack()`.
2. Se ejecuta `suggest_optional_agents()` con el directorio del proyecto y la configuracion actual.
3. Se presentan las sugerencias al desarrollador con la razon de cada una.
4. El desarrollador elige cuales activar.
5. La seleccion se guarda en el fichero `.claude/alfred-dev.local.md` bajo la clave `agentes_opcionales`.

Los agentes que no se sugieren tambien se pueden activar manualmente. El descubrimiento es una ayuda, no una restriccion.


## Composicion dinamica de equipo

El descubrimiento de agentes opcionales descrito en la seccion anterior resuelve la pregunta «que agentes podrian ser utiles en este proyecto», pero no la pregunta «que agentes necesita esta tarea concreta». Un proyecto Next.js con Prisma siempre tendra las mismas sugerencias, independientemente de si la tarea actual es «anadir pagos con Stripe» o «corregir un typo en el README». La composicion dinamica de equipo cierra esa brecha: analiza la descripcion de la tarea del usuario, la combina con las senales del proyecto y la configuracion activa, y propone un equipo adaptado a cada ejecucion.

La seleccion es efimera: solo aplica a la sesion en curso y no modifica la configuracion persistente del fichero `.claude/alfred-dev.local.md`. Esto evita que una tarea puntual contamine la configuracion del proyecto para todas las sesiones futuras.

### Las cuatro capas de la composicion

La composicion dinamica se ejecuta al invocar cualquier flujo y opera en cuatro capas secuenciales. Cada capa anade informacion a la anterior, refinando la propuesta hasta que el usuario confirma el equipo final.

```
1. CAPA HEURISTICA  (config_loader.py)
   suggest_optional_agents() + match_task_keywords()
   --> propuesta_base con puntuaciones y razones

2. CAPA DE RAZONAMIENTO  (Alfred / skill del comando)
   Alfred recibe propuesta_base como contexto y la refina
   --> propuesta_final (confirma, anade, quita agentes)

3. CAPA DE PRESENTACION  (AskUserQuestion multiSelect)
   Lista con checkboxes: nucleo fijo + opcionales seleccionables
   + infraestructura (memoria, GUI)
   --> equipo_sesion

4. EJECUCION DEL FLUJO  (orchestrator)
   equipo_sesion se pasa como override efimero a run_flow()
   Ajuste opcional por fase segun nivel de autonomia
```

La primera capa es determinista y rapida (regex + diccionarios). La segunda aprovecha la capacidad de razonamiento de Alfred (Opus) sin coste adicional, porque la propuesta heuristica se inyecta como contexto en el mismo prompt que ya procesa la tarea. La tercera da al usuario la decision final. La cuarta ejecuta el flujo con el equipo elegido.

### Capa heuristica: match_task_keywords

La funcion `match_task_keywords()` en `config_loader.py` es el corazon de la capa heuristica. Recibe la descripcion en lenguaje natural de la tarea del usuario y devuelve una puntuacion por cada agente opcional, combinando tres fuentes de informacion:

**Senal textual (keywords).** La constante `TASK_KEYWORDS` define un mapa de 7 agentes con listas de palabras clave y un peso base. Las keywords se buscan con *word boundary regex* (`\b`) sobre la descripcion en minusculas. Si coincide al menos una keyword, se suma el peso base del agente; si coinciden dos o mas, se suma un bonus adicional de +0.1.

**Senal de proyecto.** Si `suggest_optional_agents()` recomienda el agente (porque detecto ORM, frontend, HTML publico, etc.), se suman +0.4 puntos. Esta senal aporta contexto del proyecto que las keywords por si solas no capturan.

**Senal de configuracion.** Si el agente ya esta activado en el fichero `.claude/alfred-dev.local.md`, se suman +0.3 puntos. Esto refleja la intencion explicita del usuario de usar ese agente en el proyecto.

Un agente se marca como `sugerido` cuando su puntuacion acumulada alcanza o supera 0.5.

#### Tabla de puntuaciones

| Fuente | Condicion | Puntuacion |
|--------|-----------|------------|
| Proyecto | `suggest_optional_agents()` lo recomienda | +0.4 |
| Tarea | Una keyword coincide | +`peso_base` |
| Tarea | Dos o mas keywords coinciden | +`peso_base` + 0.1 |
| Config | Ya estaba activo en `alfred-dev.local.md` | +0.3 |

Ejemplos de combinaciones y resultado:

| Combinacion | Puntuacion tipica | Sugerido |
|-------------|-------------------|----------|
| Solo proyecto (sin keywords ni config) | 0.4 | No |
| Solo keyword (peso_base 0.6) | 0.6 | Si |
| Solo config activa | 0.3 | No |
| Proyecto + config activa | 0.7 | Si |
| Proyecto + keyword | 1.0 | Si |
| Keyword + config activa | 0.9 | Si |

La razon mostrada al usuario concatena las fuentes: «ORM detectado (Prisma) + la tarea menciona 'base de datos'».

#### Mapa de keywords por agente

| Agente | Keywords (extracto) | peso_base |
|--------|---------------------|-----------|
| `data-engineer` | bd, database, migracion, esquema, orm, prisma, sql, pagos, facturacion, stripe | 0.6 |
| `ux-reviewer` | interfaz, ui, ux, formulario, accesibilidad, responsive, onboarding, checkout | 0.6 |
| `performance-engineer` | rendimiento, lento, optimizar, cache, latencia, benchmark, bundle, profiling | 0.7 |
| `github-manager` | release, pr, pull request, deploy, publicar, tag, version, changelog | 0.5 |
| `seo-specialist` | seo, meta tags, lighthouse, posicionamiento, sitemap, json-ld, google | 0.7 |
| `copywriter` | textos, copy, landing, cta, tono, redaccion, marketing, newsletter | 0.6 |
| `librarian` | historial, decision, por que, antecedente, contexto historico, que se decidio | 0.5 |

La tabla completa de keywords se encuentra en la constante `TASK_KEYWORDS` de `core/config_loader.py`. Las keywords incluyen variantes con y sin tilde para garantizar la coincidencia independientemente de como escriba el usuario.

### Capa de razonamiento: Alfred como refinador

Alfred (Opus) recibe la propuesta heuristica como contexto estructurado dentro del prompt del skill del comando. No se realiza una llamada adicional al modelo: la propuesta es contexto extra en el mismo prompt que Alfred ya procesa para decidir que flujo lanzar.

Alfred puede realizar cuatro acciones sobre la propuesta:

| Accion | Ejemplo |
|--------|---------|
| Confirmar | Propuesta correcta, la presenta sin cambios |
| Anadir agente | «mejorar experiencia de checkout» -- las heuristicas no detectan «ux» pero Alfred entiende que checkout implica interfaz y anade ux-reviewer |
| Quitar agente | Heuristicas sugieren seo-specialist por HTML publico, pero la tarea es backend puro -- Alfred lo quita |
| Ajustar razon | Cambiar razon generica por una mas especifica al contexto |

Restricciones que Alfred debe respetar: nunca quita agentes de nucleo, no puede activar agentes que no existan en el plugin, y si modifica la propuesta debe explicar el cambio al usuario.

### Capa de presentacion: checkboxes

Los skills de los comandos (`feature.md`, `fix.md`, `spike.md`, `ship.md`, `audit.md` y `alfred.md`) presentan al usuario una lista con checkboxes antes de arrancar el flujo. Los agentes de nucleo aparecen como texto introductorio (siempre activos, no seleccionables). Los opcionales e infraestructura son seleccionables:

```
Alfred analizo: "anadir sistema de pagos con Stripe"

Equipo de nucleo (siempre activos):
  Alfred, Product Owner, Arquitecto, Senior Dev,
  Security Officer, QA Engineer, Tech Writer, DevOps

Agentes opcionales:
  [x] Data Engineer  - ORM Prisma + pagos
  [ ] UX Reviewer
  [ ] Performance Engineer
  [x] GitHub Manager - remote git configurado
  [ ] SEO Specialist
  [ ] Copywriter
  [x] Bibliotecario  - memoria activa

Infraestructura:
  [x] Memoria persistente
  [ ] Dashboard GUI

Confirmas este equipo?
```

La infraestructura (memoria y GUI) se presenta junto con los agentes para que el usuario vea el «equipo» completo de un vistazo. La memoria se sugiere cuando no esta activa pero la tarea indica trazabilidad (keywords de librarian) o el flujo es feature/ship. La GUI se sugiere cuando el flujo tiene 3 o mas fases y la memoria esta activa.

### Ejecucion: equipo efimero en el orquestador

La seleccion del usuario se traduce en un diccionario `equipo_sesion` que se pasa como parametro opcional a `run_flow()` en `core/orchestrator.py`. La estructura del diccionario es:

```python
equipo_sesion = {
    "opcionales_activos": {
        "data-engineer": True,
        "ux-reviewer": False,
        "performance-engineer": False,
        "github-manager": True,
        "seo-specialist": False,
        "copywriter": False,
        "librarian": True,
    },
    "infra": {
        "memoria": True,
        "gui": False,
    },
    "fuente": "composicion_dinamica",
}
```

Antes de inyectar el equipo en la sesion, `run_flow()` lo valida con `_validate_equipo_sesion()`. Las reglas de validacion son:

- El primer nivel exige exactamente tres claves: `opcionales_activos`, `infra` y `fuente`.
- `opcionales_activos` exige como minimo las claves de los 7 agentes opcionales conocidos (derivados de `TASK_KEYWORDS`). Acepta claves extra con aviso a stderr, lo que permite extensiones futuras sin romper la validacion.
- `infra` exige exactamente `memoria` y `gui`, ambos booleanos.
- `fuente` debe ser la cadena `"composicion_dinamica"`.

Si la validacion falla, el equipo se descarta con un aviso a stderr y el motivo se registra en `session["equipo_sesion_error"]` para que los consumidores downstream puedan informar al usuario. La sesion se crea igualmente, pero sin agentes opcionales, lo que garantiza que un equipo mal formado nunca rompe el flujo.

### Retrocompatibilidad

La composicion dinamica es un camino nuevo, no un reemplazo del existente. Si `equipo_sesion` no se pasa a `run_flow()`, la sesion se crea exactamente como antes (leyendo la configuracion persistente). Un proyecto que ya tiene agentes configurados en `.claude/alfred-dev.local.md` sigue funcionando sin cambios.

Los tres mecanismos de seleccion de agentes opcionales coexisten:

| Mecanismo | Persistencia | Contexto |
|-----------|--------------|----------|
| `/alfred config` | Persistente (fichero `.local.md`) | Proyecto |
| Descubrimiento (`suggest_optional_agents`) | Persistente (se guarda al confirmar) | Proyecto |
| Composicion dinamica (`match_task_keywords` + Alfred) | Efimera (solo la sesion) | Tarea |

### Ficheros involucrados

| Fichero | Componente | Rol en la composicion dinamica |
|---------|------------|--------------------------------|
| `core/config_loader.py` | `TASK_KEYWORDS` | Mapa de keywords por agente con peso base |
| `core/config_loader.py` | `match_task_keywords()` | Puntuacion heuristica por agente |
| `core/config_loader.py` | `suggest_optional_agents()` | Senales de proyecto (existente, sin cambios) |
| `core/orchestrator.py` | `_validate_equipo_sesion()` | Validacion de la estructura del equipo efimero |
| `core/orchestrator.py` | `run_flow()` | Punto de entrada con inyeccion de equipo de sesion |
| `commands/alfred.md` | Skill de triaje | Inyecta propuesta heuristica en el contexto |
| `commands/feature.md` | Skill de feature | Presenta checkboxes y arranca flujo con equipo |
| `commands/fix.md` | Skill de fix | Presenta checkboxes y arranca flujo con equipo |
| `commands/spike.md` | Skill de spike | Presenta checkboxes y arranca flujo con equipo |
| `commands/ship.md` | Skill de ship | Presenta checkboxes y arranca flujo con equipo |
| `commands/audit.md` | Skill de audit | Presenta checkboxes y arranca flujo con equipo |


## Configuracion de memoria

La memoria persistente es una capa lateral que permite a Alfred Dev conservar el historial del proyecto entre sesiones: decisiones de diseno, commits, iteraciones y eventos del flujo de trabajo. Sin memoria, cada sesion de Alfred empieza de cero; con memoria, el plugin puede responder preguntas como "por que decidimos usar SQLite en vez de PostgreSQL" o "que se implemento en la iteracion 3" con evidencia verificable.

La razon de que sea opcional y este desactivada por defecto es que no todos los proyectos necesitan trazabilidad formal. Un script de 50 lineas no necesita memoria persistente; un proyecto de equipo con decisiones arquitectonicas recurrentes, si.

### Activacion

Para activar la memoria, se anade la seccion `memoria` al frontmatter del fichero de configuracion con `enabled: true`. Tambien se puede activar de forma interactiva con `/alfred config` eligiendo la seccion de memoria.

Al activarse, Alfred crea automaticamente la base de datos SQLite en `.claude/alfred-memory.db` con permisos `0600` (solo el propietario puede leer y escribir). El esquema incluye tablas para iteraciones, decisiones, commits, eventos y vinculos entre commits y decisiones.

### Que captura

La memoria captura dos tipos de informacion controlados por su propia clave de configuracion:

- **`capture_decisions`**: cuando esta activo, cada decision de diseno que se toma durante un flujo (que framework usar, que patron aplicar, que alternativa descartar) se registra con su titulo, contexto, opcion elegida, alternativas descartadas, justificacion e impacto. Las decisiones se conservan siempre, independientemente de la retencion.

- **`capture_commits`**: cuando esta activo, cada commit se registra con su SHA, mensaje, autor, ficheros modificados y lineas anadidas/eliminadas. Los commits se vinculan automaticamente a la iteracion activa y pueden enlazarse con decisiones concretas para establecer trazabilidad completa.

Ademas, la memoria registra automaticamente eventos del flujo de trabajo (fases completadas, gates superadas, aprobaciones) que permiten reconstruir la cronologia detallada de cada iteracion.

### Retencion

La clave `retention_days` controla cuantos dias se conservan los eventos del flujo. Pasado ese periodo, los eventos antiguos se purgan automaticamente. Sin embargo, las decisiones e iteraciones no se borran nunca, porque su valor para la trazabilidad es permanente: saber por que se tomo una decision hace seis meses es tan util como saber por que se tomo ayer.

El valor por defecto es 365 dias. Para proyectos de larga duracion, se puede aumentar sin limite. Para proyectos efimeros, se puede reducir a 30 o 60 dias.

### Busqueda

La memoria soporta dos modos de busqueda, determinados automaticamente por las capacidades del entorno SQLite:

- **FTS5 (busqueda de texto completo)**: si el entorno SQLite soporta la extension FTS5, la memoria crea automaticamente una tabla virtual con indice de texto completo que indexa decisiones y commits. Las busquedas son rapidas y soportan frases literales.

- **LIKE (fallback basico)**: si FTS5 no esta disponible, las busquedas se realizan con `LIKE %termino%`, que es mas lento pero funcional en cualquier entorno SQLite.

La deteccion del modo es automatica al inicializar la base de datos. El plugin registra el resultado en la tabla `meta` para que otros componentes (como el agente Bibliotecario) sepan que modo esta activo sin tener que volver a comprobarlo.

### El agente Bibliotecario

Cuando la memoria esta activa, el agente opcional `librarian` (El Bibliotecario) se convierte en la interfaz de consulta. Es un archivista riguroso que solo responde con datos verificables de la base de datos, citando siempre la fuente con identificadores formales (`[D#12]` para decisiones, `[C#a1b2c3d]` para commits, `[I#5]` para iteraciones). Si la memoria no tiene registros sobre algo, lo dice sin rodeos en lugar de inferir.


## Personalidad

La personalidad de los agentes es uno de los aspectos que distingue a Alfred Dev de un asistente generico. Cada agente tiene un perfil unico con nombre, rol, frases caracteristicas y un tono que se adapta al nivel de sarcasmo configurado por el desarrollador. La razon de ofrecer esta personalizacion es que el tono afecta directamente a la experiencia de uso: un desarrollador que lleva ocho horas depurando un bug necesita un tono diferente al de alguien que esta explorando ideas en un spike.

### Niveles de sarcasmo

El nivel de sarcasmo es un entero de 1 a 5 que modifica el tono de todos los agentes de forma coherente. No cambia lo que dicen los agentes (sus recomendaciones tecnicas son las mismas), sino como lo dicen.

| Nivel | Etiqueta         | Descripcion                                                                                              |
|-------|------------------|----------------------------------------------------------------------------------------------------------|
| 1     | Formal           | Tono profesional y neutro. Las respuestas son directas, sin humor ni coletillas. Ideal para entornos corporativos o documentacion oficial. |
| 2     | Cordial          | Ligeramente mas cercano que el formal. Algun comentario amable, pero sin chistes. Adecuado para equipos que prefieren un tono serio pero no frio. |
| 3     | Colega (defecto) | El punto medio. Los agentes se expresan con naturalidad, alguna broma puntual y un tono de companero de equipo. Es el valor por defecto. |
| 4     | Mordaz           | Los agentes empiezan a soltar comentarios acidos. Las malas practicas se senalan con ironia y las frases de sarcasmo alto se anaden al repertorio. |
| 5     | Erudito ironico  | Sarcasmo maximo. Los agentes no se cortan: comentarios acidos, ironia elaborada y criticas con estilo. Solo para desarrolladores que aprecian el humor negro tecnico. |

Tecnicamente, el umbral esta en el nivel 4. A partir de ese nivel, la funcion `get_agent_voice()` del modulo `personality.py` anade las frases de `frases_sarcasmo_alto` al repertorio del agente, y `get_agent_intro()` incluye una coletilla acida en la presentacion. Por debajo de 4, solo se usan las frases base.

### Celebrar victorias

Cuando `celebrar_victorias` esta activo (`true`), los agentes reaccionan de forma positiva al completar fases y flujos: reconocen el progreso, destacan los hitos y animan al equipo. Cuando esta desactivado, el avance se comunica de forma factual sin celebraciones.

La razon de este ajuste es que no todos los desarrolladores responden igual al refuerzo positivo. Algunos lo valoran; otros lo perciben como ruido. Dejarlo configurable respeta ambas preferencias.

### Insultar malas practicas

Cuando `insultar_malas_practicas` esta activo y el nivel de sarcasmo es suficientemente alto (>= 4), los agentes comentan con ironia las practicas cuestionables que detectan: un `SELECT *` sin `WHERE`, un push directo a main, un README vacio o un token en el repositorio. Es una forma de senalar problemas con humor, no con hostilidad. Si se desactiva, los agentes informan de los problemas sin el componente sarcastico.


## Ejemplo completo de fichero `.claude/alfred-dev.local.md`

El siguiente ejemplo muestra un fichero de configuracion con todas las secciones definidas. En la practica, el desarrollador solo necesita incluir las secciones que quiere personalizar; todo lo demas hereda los valores por defecto.

```yaml
---
autonomia:
  producto: interactivo
  arquitectura: interactivo
  seguridad: autonomo
  refactor: semi-autonomo
  docs: autonomo
  tests: autonomo

proyecto:
  runtime: node
  lenguaje: typescript
  framework: next
  orm: prisma
  test_runner: vitest
  bundler: vite

agentes_opcionales:
  data-engineer: true
  ux-reviewer: false
  performance-engineer: false
  github-manager: true
  seo-specialist: false
  copywriter: false
  librarian: true

memoria:
  enabled: true
  capture_decisions: true
  capture_commits: true
  retention_days: 365

personalidad:
  nivel_sarcasmo: 3
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
