/**
 * Datos de contenido de la landing page en castellano de Espana.
 *
 * Fuente de contenido en castellano. Los claims publicos deben coincidir
 * con plugin.json 0.7.0, README.md y docs/release.md.
 *
 * @module i18n/data.es
 */

import type { PageData } from '../types/index';

const data: PageData = {
  meta: {
    title: 'Alfred Dev - plugin de Claude Code alineado con el SDK',
    description: 'Plugin de Claude Code con 10 agentes, 11 skills planas, 18 comandos y memoria local. Quality gates con evidencia, MCP oficial y sin alias global /alfred.',
    canonical: 'https://alfred-dev.com/',
    locale: 'es_ES',
    og: {
      type: 'website',
      title: 'Alfred Dev - plugin de Claude Code alineado con el SDK',
      description: 'Un equipo corto para Claude Code: 8 de núcleo, Selina si hay frontend y Lucius bajo demanda. Habla en castellano, gates con evidencia y memoria SQLite por proyecto.',
      url: 'https://alfred-dev.com/',
      siteName: 'Alfred Dev',
      locale: 'es_ES',
      image: 'https://alfred-dev.com/screenshots/alfred-dev-share-es.png',
      imageWidth: 2400,
      imageHeight: 1260,
      imageType: 'image/png',
      imageAlt: 'Landing de Alfred Dev: un sistema de trabajo para Claude Code',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Alfred Dev - plugin de Claude Code alineado con el SDK',
      description: '10 agentes, 11 skills, 18 comandos /alfred-dev:*. MCP oficial, secret-guard y quality gates verificables.',
      image: 'https://alfred-dev.com/screenshots/alfred-dev-share-es.png',
      imageAlt: 'Landing de Alfred Dev: un sistema de trabajo para Claude Code',
      site: '@686f6c61',
      creator: '@686f6c61',
    },
  },

  nav: [
    { href: '#agentes', label: 'Agentes', svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>' },
    { href: '#flujos', label: 'Flujos', svgContent: '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>' },
    { href: '#skills', label: 'Skills', svgContent: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>' },
    { href: '#gates', label: 'Gates', svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>' },
    { href: '#infra', label: 'Infra', svgContent: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>' },
    { href: '#uso', label: 'Uso', svgContent: '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>' },
    { href: '#memoria', label: 'Memoria', svgContent: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>' },
    { href: '#instalar', label: 'Instalar', svgContent: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>' },
    { href: '#faq', label: 'FAQ', svgContent: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>' },
  ],

  hero: {
    titleHtml: 'Tus compañeros de<br>desarrollo en un <em>plugin</em>',
    platformHtml: 'para <span style="color: var(--blue);">Claude Code</span>',
    subtitle: '10 agentes (8 de núcleo, Selina si hay frontend, Lucius bajo demanda). 11 skills planas, 18 comandos /alfred-dev:*. Habla en castellano: no hace falta memorizar slashes. Quality gates con evidencia y MCP oficial.',
    ctas: [
      { label: 'macOS / Linux', command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash', ariaLabel: 'Copiar comando de instalación para macOS y Linux' },
      { label: 'Windows', command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex', ariaLabel: 'Copiar comando de instalación para Windows' },
    ],
    features: {
      label: 'Por qué se queda instalado',
      items: [
        { title: 'Alineado con el SDK de Anthropic', description: 'commands/, skills planas, hooks en exec form con args y timeout, MCP con FastMCP. No muta settings.json ni inventa un alias global /alfred.', svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>', tag: { text: '0.7.0', href: '#infra' } },
        { title: 'Habla, no recites comandos', description: 'Escribe «el login peta» o «sigue donde lo dejé». prompt-route sugiere fix, quick o retomar. SessionStart inyecta el briefing real.', svgContent: '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>', tag: { text: 'Nuevo', href: '#uso' } },
        { title: 'Núcleo corto, no un catálogo inflado', description: 'Diez roles de verdad. El kanban lo escribe el runtime. El único opcional es Lucius. Sin data-engineer, github-manager ni bibliotecario.', svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>' },
        { title: 'Gates que no se creen un «tests OK»', description: 'Autopilot solo resuelve gates de usuario. Tests, seguridad, evidencia y el deploy humano no se saltan.', svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>' },
        { title: 'Selina cuando hay UI', description: 'Tres propuestas en el navegador y docs/style-direction.md antes de que el architect dibuje cajas. Si no hay frontend, se salta.', svgContent: '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/>' },
        { title: 'Lucius, segunda opinión', description: 'Codex CLI en solo lectura. Diagnóstico y prescripción. Tú decides qué aplicar. Se activa con /alfred-dev:ajustes.', svgContent: '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>' },
        { title: 'Memoria local y Memory UI', description: 'SQLite por proyecto, 15 tools MCP y un visor GET en localhost. No importa el git log. SessionEnd apaga la UI.', svgContent: '<rect x="3" y="4" width="18" height="12" rx="1"/><path d="M8 20h8"/>' },
        { title: 'Docs que se actualizan solas', description: 'Arquitectura, compliance, threat-model y ADRs en tu repo. El Escriba los sincroniza por fase. Hygiene bloquea ship si siguen en esqueleto.', svgContent: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>' },
        { title: 'Secret-guard de verdad', description: 'Bloquea secretos en Write, Edit, Bash y tools MCP. Fail-closed. No es un aviso decorativo.', svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>' },
      ],
    },
  },

  stats: [
    { number: 10, label: 'Agentes' },
    { number: 11, label: 'Skills' },
    { number: 6, label: 'Flujos' },
    { number: 18, label: 'Comandos' },
    { number: 8, label: 'Templates' },
    { number: 10, label: 'Hooks' },
    { number: 5, label: 'Gates tipo' },
  ],

  coreAgents: {
    header: {
      label: 'El equipo',
      title: '8 de núcleo + Selina',
      description: 'Cada agente tiene un rol delimitado y quality gates verificables. Alfred coordina. El kanban lo escribe el runtime, no un project-manager.',
    },
    agents: [
      { name: 'Alfred', model: 'inherit', alias: 'Mayordomo jefe', role: 'Orquesta flujos, elige quién entra y evalúa las gates. No redefine alcance ni arquitectura.', phrase: '"He tomado la libertad de preparar un plan."', color: 'var(--blue)' },
      { name: 'El buscador de problemas', model: 'inherit', alias: 'Product Owner', role: 'PRDs, historias, criterios. Decide qué problema se resuelve y por qué.', phrase: '"Antes de diseñar nada, el problema real."', color: 'var(--purple)' },
      { name: 'El dibujante de cajas', model: 'inherit', alias: 'Arquitecto', role: 'Sistemas, ADRs, diagramas, threat model con seguridad.', phrase: '"Si no está en el diagrama, es deuda."', color: 'var(--green)' },
      { name: 'El artesano', model: 'inherit', alias: 'Senior Dev', role: 'TDD, commits atómicos, implementación mantenible.', phrase: '"Los tests ya están preparados."', color: 'var(--orange)' },
      { name: 'El paranoico', model: 'inherit', alias: 'Security Officer', role: 'OWASP, STRIDE, SBOM, RGPD/NIS2/CRA. Transversal en arquitectura, calidad y entrega.', phrase: '"Eso no se hardcodea."', color: 'var(--red)' },
      { name: 'El rompe-cosas', model: 'inherit', alias: 'QA Engineer', role: 'Test plans, review, exploración, regresión.', phrase: '"Ese edge case que no contemplaste? Lo encontré."', color: 'var(--gold)' },
      { name: 'El fontanero', model: 'inherit', alias: 'DevOps Engineer', role: 'Docker, CI/CD, empaquetado, deploy. El deploy pide confirmación humana.', phrase: '"Si lo despliegas a mano, lo despliegas mal."', color: 'var(--cyan)' },
      { name: 'El traductor', model: 'inherit', alias: 'Tech Writer', role: 'Docs del código y del proyecto. Sincroniza docs/project y ADRs.', phrase: '"Si no está escrito, no existe."', color: 'var(--white)' },
      { name: 'Selina', model: 'inherit', alias: 'Dirección visual', role: 'Tres propuestas en navegador y docs/style-direction.md. Solo si hay frontend.', phrase: '"El estilo no es decoración: es comunicación."', color: 'var(--purple)' },
    ],
  },

  optionalAgents: {
    header: {
      label: 'Bajo demanda',
      labelColor: 'var(--gold)',
      title: '1 opcional: Lucius',
      description: 'Segunda opinión vía Codex CLI. Se activa con <strong style="color: var(--blue);">/alfred-dev:ajustes</strong>. No hay catálogo 0.6.',
    },
    agents: [
      { name: 'Lucius', model: 'inherit', alias: 'Director técnico externo', role: 'Audita en solo lectura con Codex CLI. Diagnóstico y prescripción. No sustituye el sign-off del flujo.', phrase: '"Desde fuera se ve un punto débil que desde dentro no."', color: '#d97706' },
    ],
  },

  composition: {
    header: {
      label: 'Composición',
      labelColor: 'var(--gold)',
      title: 'El núcleo siempre. Lucius si lo pides.',
    description: 'Alfred no ofrece menús de 9 especialistas. El runtime solo admite Lucius. Selina entra sola si hay frontend.',
    },
    introHtml: 'Cuando <code>/alfred-dev:alfred</code> o un flujo deciden abrir trabajo, el equipo de núcleo está listo. Si quieres segunda opinión externa, Alfred pregunta por Lucius:',
    terminalPrompt: '$ /alfred-dev:feature',
    terminalText: 'Login con email y password, TDD y threat model',
    coreTeamText: 'Equipo de núcleo: Alfred, Product Owner, Architect, Senior Dev, Security, QA, Tech Writer, DevOps. Selina si hay UI.',
    techQuestion: 'Quieres activar Lucius como segunda opinión externa?',
    techOptions: [
      { label: 'Lucius', desc: 'Codex CLI, solo lectura (Recomendado si hay cierre)', selected: false },
    ],
    contentQuestion: 'Listo con este grupo',
    contentOptions: [
      { label: 'Seguir sin activar más', desc: 'Mantener solo el núcleo', selected: true },
    ],
    confirmText: 'Equipo: núcleo + Lucius opcional',
    productQuestion: 'Quién es el usuario principal?',
    productOptions: [
      { label: 'Usuario final', desc: '', selected: true },
      { label: 'Administrador', desc: '', selected: false },
      { label: 'Equipo interno', desc: '', selected: false },
    ],
  },

  workflows: {
    header: {
      label: 'Flujos de trabajo',
      title: '6 flujos, gates entre fases',
      description: 'feature hasta 7 fases. Fuera de los flujos: <code>progress</code>, <code>pause</code> y <code>retomar</code>. No hay slash público next/standup/validate.',
    },
    flows: [
      { command: '/alfred-dev:feature', subtitle: 'Ciclo completo o parcial', description: 'Hasta 7 fases: producto, estilo visual (Selina, condicional), arquitectura, desarrollo TDD, calidad, documentación, entrega.', stages: ['Producto', 'Estilo visual', 'Arquitectura', 'Desarrollo', 'Calidad', 'Documentación', 'Entrega'] },
      { command: '/alfred-dev:quick', subtitle: 'Cambio pequeño', description: '2 fases: ejecución acotada y validación rápida. Tests y seguridad, menos ceremonia.', stages: ['Ejecución acotada', 'Validación rápida'] },
      { command: '/alfred-dev:fix', subtitle: 'Bug', description: 'Causa raíz, test que reproduce, corrección mínima, validación.', stages: ['Diagnóstico', 'Corrección TDD', 'Validación'] },
      { command: '/alfred-dev:spike', subtitle: 'Investigación', description: 'Sin compromiso de implementación. Hallazgos y ADR si toca decidir.', stages: ['Investigación', 'Hallazgos'] },
      { command: '/alfred-dev:ship', subtitle: 'Release', description: 'Auditoría, changelog, empaquetado, deploy. Hygiene bloquea si la UAT está abierta o los docs vivos siguen en esqueleto.', stages: ['Auditoría', 'Documentación', 'Empaquetado', 'Despliegue'] },
      { command: '/alfred-dev:audit', subtitle: 'Auditoría', description: 'Calidad, seguridad, arquitectura y documentación en paralelo. SonarQube solo con decisión humana.', stages: ['Auditoría paralela'] },
    ],
  },

  gates: {
    header: {
      label: 'Quality gates',
      title: 'Evidencia antes que afirmaciones',
      description: 'Autopilot solo resuelve gates de usuario configuradas. No salta tests, seguridad, evidencia ni la confirmación humana de despliegue.',
    },
    coreLabel: 'Núcleo',
    core: [
      { text: 'Producto: el usuario aprueba el PRD antes de diseñar' },
      { text: 'Selina: el usuario elige dirección visual si hay frontend' },
      { text: 'Arquitectura: diseño + threat model, gate de usuario' },
      { text: 'Desarrollo: tests verdes (automático)' },
      { text: 'Calidad: tests + seguridad (automático + seguridad)' },
      { text: 'Documentación: gate libre con checklist, no bloqueo mudo' },
      { text: 'Entrega: usuario + seguridad. Deploy nunca en silencio' },
      { text: 'evidence-guard registra runners reales; no vale «tests OK» de palabra' },
      { text: 'secret-guard bloquea secretos en Write, Edit, Bash y MCP' },
      { text: 'Hygiene impide ship con UAT abierta o docs/project en esqueleto' },
    ],
    optionalLabel: 'Lucius',
    optional: [
      { text: 'Segunda opinión externa: no sustituye el sign-off del flujo', optional: true },
    ],
  },

  skills: {
    header: {
      label: 'Capacidades',
      title: '11 skills planas',
      description: 'Cada skill es skills/&lt;nombre&gt;/SKILL.md. No hay 62 skills en 15 dominios. Las de side effects van con disable-model-invocation.',
    },
    domains: [
      {
        name: 'Proceso',
        skills: [
          { name: 'write-adr', description: 'ADRs en docs/adr/' },
          { name: 'evaluate-dependency', description: 'Veredicto de paquetes nuevos' },
          { name: 'sync-project-docs', description: 'Índice y sync de docs/project/' },
          { name: 'memory', description: 'Consulta y política de escritura SQLite' },
        ],
      },
      {
        name: 'Seguridad y compliance',
        skills: [
          { name: 'threat-model', description: 'STRIDE' },
          { name: 'compliance-check', description: 'RGPD, NIS2, CRA' },
          { name: 'sbom-generate', description: 'Software Bill of Materials' },
        ],
      },
      {
        name: 'Calidad y entrega',
        skills: [
          { name: 'sonarqube', description: 'Preflight y análisis (manual)' },
          { name: 'incident-response', description: 'Incidente (manual)' },
          { name: 'pr-workflow', description: 'Pull request (manual)' },
        ],
      },
      {
        name: 'Visual',
        skills: [
          { name: 'style-direction', description: 'Dirección visual de Selina (manual)' },
        ],
      },
    ],
  },

  infra: {
    header: {
      label: 'Bajo el capó',
      title: '10 hooks, 8 templates, core Python',
      description: 'Lo que Claude Code ejecuta de verdad. Sin stop-hook Ralph, sin PreCompact, sin hooks de ortografía o dependencias.',
    },
    groups: [
      {
        title: '10 hooks',
        items: [
          { name: 'session-bootstrap.sh', label: 'SessionStart' },
          { name: 'session-start.sh', label: 'SessionStart' },
          { name: 'session-end.py', label: 'SessionEnd' },
          { name: 'activity-capture.py', label: 'UserPromptSubmit + PostToolUse' },
          { name: 'prompt-route.py', label: 'UserPromptSubmit' },
          { name: 'secret-guard.py', label: 'PreToolUse Write/Edit/Bash/MCP' },
          { name: 'dangerous-command-guard.py', label: 'PreToolUse Bash' },
          { name: 'sensitive-read-guard.py', label: 'PreToolUse Read' },
          { name: 'quality-gate.py', label: 'PostToolUse Bash' },
          { name: 'evidence-guard.py', label: 'PostToolUse Bash' },
        ],
      },
      {
        title: '8 templates',
        items: [
          { name: 'prd.md', label: 'Product Requirements' },
          { name: 'adr.md', label: 'Architecture Decision' },
          { name: 'test-plan.md', label: 'Plan de testing' },
          { name: 'threat-model.md', label: 'STRIDE' },
          { name: 'sbom.md', label: 'Bill of Materials' },
          { name: 'compliance.md', label: 'Checklist de cumplimiento' },
          { name: 'changelog-entry.md', label: 'Entrada de changelog' },
          { name: 'release-notes.md', label: 'Notas de release' },
        ],
      },
      {
        title: 'Core Python',
        items: [
          { name: 'orchestrator.py', label: 'Flujos, fases, gates, autopilot' },
          { name: 'continuity.py', label: 'Kanban, handoff, UAT, sync GitHub' },
          { name: 'prompt_route.py', label: 'Ruta sin slash' },
          { name: 'session_brief.py', label: 'Briefing de sesión' },
          { name: 'project_docs.py', label: 'Docs vivas y ADRs' },
          { name: 'memory*.py', label: 'SQLite, MCP y Memory UI' },
        ],
      },
    ],
  },

  commands: {
    header: {
      label: 'Interfaz',
      title: '18 comandos /alfred-dev:*',
      description: 'La entrada es /alfred-dev:alfred. No hay alias global /alfred. next y search son helpers internos.',
    },
    groups: [
      {
        label: 'Entrada',
        color: 'var(--blue)',
        commands: [
          { command: '/alfred-dev:alfred', description: 'Decide si mapear, retomar, abrir un flujo o responder en corto.' },
          { command: '/alfred-dev:ajustes', description: 'Autonomía, Lucius, memoria y personalidad. Antes /alfred-dev:config.' },
          { command: '/alfred-dev:update', description: 'Semver real y un menú: actualizar ahora o no.' },
        ],
      },
      {
        label: 'Flujos',
        color: 'var(--green)',
        commands: [
          { command: '/alfred-dev:feature', description: 'Hasta 7 fases. Selina si hay UI.' },
          { command: '/alfred-dev:quick', description: 'Cambio pequeño, 2 fases.' },
          { command: '/alfred-dev:fix', description: 'Bug con TDD.' },
          { command: '/alfred-dev:spike', description: 'Investigación sin compromiso.' },
          { command: '/alfred-dev:ship', description: 'Release. Hygiene puede bloquear.' },
          { command: '/alfred-dev:audit', description: '4 ejes en paralelo.' },
        ],
      },
      {
        label: 'Continuidad',
        color: 'var(--cyan)',
        commands: [
          { command: '/alfred-dev:progress', description: 'Kanban, bloqueos, UAT y trazabilidad. Absorbe standup/validate.' },
          { command: '/alfred-dev:pause', description: 'Handoff en JSON y Markdown.' },
          { command: '/alfred-dev:retomar', description: 'Vuelve al handoff. Antes /alfred-dev:resume.' },
          { command: '/alfred-dev:map-codebase', description: 'Mapa brownfield persistente.' },
          { command: '/alfred-dev:discuss', description: 'Refinado antes de feature.' },
        ],
      },
      {
        label: 'Operación',
        color: 'var(--gold)',
        commands: [
          { command: '/alfred-dev:uat', description: 'Validación humana. Antes /alfred-dev:verify.' },
          { command: '/alfred-dev:memory-ui', description: 'Visor local GET de la SQLite.' },
          { command: '/alfred-dev:sync-github', description: 'Espejo del tablero local en Issues.' },
          { command: '/alfred-dev:lucius', description: 'Segunda opinión Codex CLI.' },
        ],
      },
    ],
    optionalNote: 'El único opcional es <strong>Lucius</strong>, con <strong>/alfred-dev:ajustes</strong>. Selina entra sola si hay frontend.',
  },

  stacks: {
    header: {
      label: 'Detección automática',
      title: 'Se adapta a tu proyecto',
      description: 'Detecta el stack y adapta artefactos. No inventa especialistas 0.6 por cada señal.',
    },
    list: [
      { name: 'Node.js', description: 'npm, pnpm, bun, yarn. Express, Next.js, Fastify, Hono.' },
      { name: 'Python', description: 'pip, poetry, uv. Django, Flask, FastAPI.' },
      { name: 'Rust', description: 'cargo. Actix, Axum, Rocket.' },
      { name: 'Go', description: 'go mod. Gin, Echo, Fiber.' },
      { name: 'Ruby', description: 'bundler. Rails, Sinatra.' },
      { name: 'Elixir', description: 'mix. Phoenix.' },
      { name: 'Java / Kotlin', description: 'Maven, Gradle. Spring Boot, Quarkus, Micronaut.' },
      { name: 'PHP', description: 'Composer. Laravel, Symfony.' },
      { name: 'C# / .NET', description: 'dotnet, NuGet. ASP.NET, Blazor.' },
      { name: 'Swift', description: 'SPM. Vapor.' },
    ],
  },

  useCases: {
    header: {
      label: 'En la práctica',
      labelColor: 'var(--cyan)',
      title: 'Cómo se usa',
      description: 'Habla en castellano o usa /alfred-dev:*. Estos son recorridos reales de 0.7.0.',
    },
    cases: [
      { category: 'Conversacional', color: 'var(--gold)', background: 'rgba(201,169,110,0.08)', title: 'Sin memorizar slashes', command: 'el login peta con eñes', steps: ['prompt-route clasifica la frase como fix', 'Alfred entra en diagnóstico TDD', 'No hace falta escribir /alfred-dev:fix si la señal es clara'] },
      { category: 'Desarrollo', color: 'var(--blue)', background: 'rgba(91,156,245,0.08)', title: 'Feature completa', command: '/alfred-dev:feature sistema de notificaciones push', steps: ['Product Owner cierra el PRD', 'Selina solo si hay UI', 'Architect + Security, TDD, QA, docs, entrega'] },
      { category: 'Corrección', color: 'var(--red)', background: 'rgba(229,86,79,0.08)', title: 'Corregir un bug', command: '/alfred-dev:fix el login falla con tildes', steps: ['Reproduce y aísla la causa', 'Test que falla, corrección mínima', 'QA y seguridad revisan regresión'] },
      { category: 'Investigación', color: 'var(--purple)', background: 'rgba(160,126,232,0.08)', title: 'Spike', command: '/alfred-dev:spike REST frente a gRPC', steps: ['Exploración sin compromiso', 'Hallazgos y ADR si hay que decidir'] },
      { category: 'Auditoría', color: 'var(--orange)', background: 'rgba(232,164,74,0.08)', title: 'Auditar', command: '/alfred-dev:audit', steps: ['Cuatro ejes en paralelo', 'SonarQube solo si el usuario lo decide', 'Informe priorizado'] },
      { category: 'Entrega', color: 'var(--green)', background: 'rgba(78,201,144,0.08)', title: 'Ship', command: '/alfred-dev:ship', steps: ['Hygiene: UAT y docs vivos', 'Changelog y empaquetado', 'Deploy con confirmación humana'] },
      { category: 'Brownfield', color: 'var(--cyan)', background: 'rgba(78,201,201,0.08)', title: 'Repo existente', command: '/alfred-dev:map-codebase', steps: ['Mapa persistente en docs/project/', 'Luego feature o fix no arrancan a ciegas'] },
      { category: 'Continuidad', color: 'var(--green)', background: 'rgba(78,201,144,0.08)', title: 'Pausar y retomar', command: '/alfred-dev:pause', steps: ['Handoff JSON + Markdown', '/alfred-dev:retomar o «sigue donde lo dejé»'] },
      { category: 'Estado', color: 'var(--magenta)', background: 'rgba(214,106,214,0.08)', title: 'Qué hay en curso', command: '/alfred-dev:progress', steps: ['Kanban, bloqueos, UAT, trazabilidad', 'Absorbe standup, blocked y validate'] },
      { category: 'UAT', color: 'var(--red)', background: 'rgba(229,86,79,0.08)', title: 'Aceptación humana', command: '/alfred-dev:uat', steps: ['Separa tests automáticos de la validación humana', 'pending / approved / rejected'] },
      { category: 'Memoria', color: 'var(--blue)', background: 'rgba(84,196,255,0.08)', title: 'Memory UI', command: '/alfred-dev:memory-ui', wide: true, steps: ['Visor GET en localhost sobre la SQLite real', 'No importa git log', 'SessionEnd la apaga'] },
      { category: 'Visual', color: 'var(--purple)', background: 'rgba(160,126,232,0.08)', title: 'Selina', command: '/alfred-dev:feature app con UI', wide: true, image: { src: '/screenshots/selina-style-direction.svg', alt: 'Selina mostrando propuestas visuales', caption: 'Tres finalistas y docs/style-direction.md antes de implementar.' }, steps: ['Tres propuestas en el navegador', 'El usuario elige', 'Architect lee esa dirección'] },
      { category: 'GitHub', color: 'var(--text-muted)', background: 'rgba(110,115,138,0.08)', title: 'Espejo de tablero', command: '/alfred-dev:sync-github owner/repo', wide: true, image: { src: '/screenshots/sonia-sync-github.png', alt: 'Tablero local reflejado en GitHub Issues', caption: 'GitHub es espejo. La verdad sigue en docs/project y SQLite.' }, steps: ['Proyecta el tablero local con gh', 'No hay agente github-manager'] },
      { category: 'Automático', color: 'var(--cyan)', background: 'rgba(78,201,201,0.08)', title: 'Lo que corre solo', wide: true, description: 'Hooks registrados. Sin Ralph, sin compactación, sin corrector de tildes.', steps: ['secret-guard bloquea secretos (fail-closed)', 'dangerous-command-guard bloquea rm -rf / y similares', 'quality-gate y evidence-guard vigilan tests', 'prompt-route sugiere ruta sin slash', 'activity-capture registra Write/Edit/Bash y prompts', 'session-end cierra Memory UI y escribe el cierre'] },
      { category: 'Autonomía', color: 'var(--green)', background: 'rgba(78,201,126,0.08)', title: 'Autopilot honesto', command: '/alfred-dev:ajustes', steps: ['No hay flag mágico por comando', 'Autoaprueba solo gates de usuario', 'Tests, seguridad y deploy humano siguen'] },
    ],
  },

  memory: {
    sectionLabel: 'Memoria persistente por proyecto',
    title: 'Memoria local, MCP oficial, UI GET',
    descriptionHtml: 'SQLite en <code>.claude/alfred-memory.db</code>. FastMCP si el paquete <code>mcp</code> está instalado. Memory UI no importa el historial de Git.',
    traceability: {
      title: 'Trazabilidad',
      descriptionHtml: 'Problema, decisión, commit y validación con IDs citables.',
      nodes: [
        { label: 'Problema', color: 'var(--purple)', background: 'rgba(160,126,232,0.08)', borderColor: 'rgba(160,126,232,0.15)' },
        { label: 'Decisión [D#id]', color: 'var(--gold)', background: 'rgba(201,169,110,0.08)', borderColor: 'rgba(201,169,110,0.15)' },
        { label: 'Commit [C#sha]', color: 'var(--green)', background: 'rgba(78,201,144,0.08)', borderColor: 'rgba(78,201,144,0.15)' },
        { label: 'Validación', color: 'var(--blue)', background: 'rgba(91,156,245,0.08)', borderColor: 'rgba(91,156,245,0.15)' },
      ],
    },
    cards: [
      { title: 'SQLite local', descriptionHtml: 'WAL, FTS5, permisos 0600. Nada sale del proyecto.' },
      { title: 'MCP oficial', descriptionHtml: '15 tools. Arranca con FastMCP si <code>mcp</code> está instalado; si no, el servidor compatible sigue ahí.' },
      { title: 'Captura acotada', descriptionHtml: '<code>activity-capture.py</code> en UserPromptSubmit y PostToolUse (Write/Edit/Bash). No está en Stop ni PreCompact.' },
      { title: 'Briefing de sesión', descriptionHtml: 'SessionStart inyecta estado, última decisión y ADRs. No llama a GitHub.' },
      { title: 'Cierre', descriptionHtml: 'SessionEnd escribe <code>.claude/alfred-last-cierre.md</code> si hubo sesión o evidencia.' },
      { title: 'Secretos', descriptionHtml: 'Misma sanitización que <code>secret-guard.py</code> antes de persistir.' },
    ],
    librarian: {
      title: 'Consulta: MCP y Memory UI',
      subtitle: 'No hay agente Bibliotecario',
      descriptionHtml: [
        'Las consultas van por las tools MCP o por <code>/alfred-dev:memory-ui</code>. Si no hay evidencia, se dice. Las citas usan <code>[D#id]</code>, <code>[C#sha]</code>, <code>[I#id]</code>.',
        'Memory UI es un visor GET en localhost. No importa git log. Si la memoria está vacía, se ve vacía.',
      ],
      example: {
        label: 'Ejemplo:',
        question: '> Por qué SQLite y no PostgreSQL?',
        answerHtml: 'Porque el requisito era cero servicios externos <span style="color: var(--gold);">[D#12]</span>. Implementado en <span style="color: var(--green);">[C#1833e83]</span>.',
      },
      activationHtml: '<strong>Activación:</strong> <code>/alfred-dev:ajustes</code>, sección memoria. El primer arranque puede sembrarla a <code>enabled: true</code>.',
    },
    faq: [
      { question: 'Dónde se guardan los datos?', answerHtml: 'En <code>.claude/alfred-memory.db</code> del proyecto. No hay servicio remoto.' },
      { question: 'Se activa sola?', answerHtml: 'El primer SessionStart puede sembrar <code>memoria.enabled: true</code>. Después manda lo que pongas en <code>/alfred-dev:ajustes</code>.' },
      { question: 'Qué pasa con los secretos?', answerHtml: 'Pasan por <code>core/secrets.py</code>, los mismos patrones que el hook. El fichero queda en 0600.' },
      { question: 'Puedo borrar la memoria?', answerHtml: 'Sí: borra el <code>.db</code> o pon <code>enabled: false</code>. Memory UI no rellena huecos con git log.' },
    ],
  },

  install: {
    sectionLabel: 'Primeros pasos',
    title: 'Instalación',
    description: 'Un comando. Scope user. El script 0.7.0 no pisa ~/.claude/skills ni crea /alfred. Hoy GitHub main aún puede servir otra versión.',
    tabs: [
      { id: 'macos', label: 'macOS', command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash', requirementsHtml: '<strong>Requisitos:</strong> Python 3.10+, Claude Code con plugins/skills/hooks/MCP.<br>Luego <strong>/reload-plugins</strong> y <strong>/alfred-dev:alfred</strong>.' },
      { id: 'linux', label: 'Linux', command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash', requirementsHtml: '<strong>Requisitos:</strong> Python 3.10+, Claude Code con plugins/skills/hooks/MCP.<br>Luego <strong>/reload-plugins</strong> y <strong>/alfred-dev:alfred</strong>.' },
      { id: 'windows', label: 'Windows', command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex', requirementsHtml: '<strong>Requisitos:</strong> PowerShell 5.1+, Python 3.10+, Claude Code reciente.<br>Luego <strong>/reload-plugins</strong> y <strong>/alfred-dev:alfred</strong>.' },
    ],
    uninstall: {
      title: 'Desinstalación',
      description: 'Quita plugin, marketplace y caché. No borra .claude/ del proyecto.',
      cards: [
        { title: 'macOS / Linux', command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash', ariaLabel: 'Copiar desinstalación macOS/Linux' },
        { title: 'Windows (PowerShell)', command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.ps1 | iex', ariaLabel: 'Copiar desinstalación Windows' },
      ],
    },
    update: {
      title: 'Actualización',
      descriptionHtml: '<strong>/alfred-dev:update</strong> compara semver y ofrece un menú. Normaliza a <code>--scope user</code>. No recrea un alias /alfred.',
    },
  },

  config: {
    sectionLabel: 'Personalización',
    title: 'Configuración por proyecto',
    descriptionHtml: '<code>.claude/alfred-dev.local.md</code>. Primera sesión lo siembra. Después <strong>/alfred-dev:ajustes</strong>.',
    yamlExample: `---
autonomia:
  producto: interactivo
  arquitectura: interactivo
  desarrollo: semi-autonomo
  calidad: semi-autonomo
  documentacion: autonomo
  entrega: semi-autonomo

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
  celebrar_victorias: true
  insultar_malas_practicas: true
---`,
    blocks: [
      { title: 'Bootstrap', descriptionHtml: 'SessionStart crea el fichero si falta. No reescribe settings.json.' },
      { title: 'Autonomía', descriptionHtml: 'Por fase. Autopilot solo autoaprueba gates de usuario.' },
      { title: 'Lucius', descriptionHtml: 'Único opcional. Codex CLI, solo lectura.' },
      { title: 'Memoria y docs', descriptionHtml: 'SQLite + docs/project y docs/adr.' },
      { title: 'Personalidad', descriptionHtml: 'Sarcasmo 1-5. Las celebraciones van aparte.' },
    ],
  },

  faq: {
    header: { label: 'Preguntas frecuentes', title: 'FAQ' },
    items: [
      {
        svgContent: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/>',
        question: 'Cómo se instala?',
        answerHtml: '<p>macOS y Linux:</p><pre>curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash</pre><p>Windows:</p><pre>irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex</pre><p>Hace falta Claude CLI en el PATH, Python 3.10+ y <code>~/.claude</code>. El script instala <code>alfred-dev@alfred-dev</code> con <code>--scope user</code>. Luego <code>/reload-plugins</code> y <code>/alfred-dev:alfred</code>.</p>',
      },
      {
        svgContent: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>',
        question: 'Ese curl instala ya la 0.7.0?',
        answerHtml: '<p>No necesariamente. El comando lee la rama <code>main</code> de GitHub, no esta landing.</p><p>Al generar esta página, <code>main</code> publica <strong>{{GITHUB_MAIN_VERSION}}</strong> ({{GITHUB_MAIN_COMMANDS}} comandos). Esta página describe <strong>{{LANDING_VERSION}}</strong>.</p><p>Si no coinciden, el one-liner instala lo de <code>main</code>. La 0.6.1 crea el alias <code>/alfred</code>. La 0.7.0 no lo crea y no pisa <code>~/.claude/skills</code>.</p>',
      },
      {
        svgContent: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>',
        question: 'Qué hace falta?',
        answerHtml: '<p>Claude Code reciente con plugins, skills, hooks y MCP. Python 3.10 o superior. El instalador busca <code>python3.13</code> … <code>python3.10</code> si <code>python3</code> es viejo.</p><p>El paquete Python <code>mcp</code> activa FastMCP; si no está, el servidor de memoria sigue con el fallback. En Windows: PowerShell 5.1+ o bash en WSL.</p>',
      },
      {
        svgContent: '<rect x="2" y="3" width="20" height="14" rx="2"/>',
        question: 'Funciona en Windows?',
        answerHtml: '<p>Sí. Usa <code>install.ps1</code>, o <code>install.sh</code> dentro de WSL.</p><p>Después: <code>/reload-plugins</code> y <code>/alfred-dev:alfred</code>. Si el inventario no carga, reinicia Claude Code.</p>',
      },
      {
        svgContent: '<polyline points="23 4 23 10 17 10"/>',
        question: 'Cómo se actualiza y se desinstala?',
        answerHtml: '<p>Actualizar: <code>/alfred-dev:update</code> compara semver con GitHub Releases y, si aceptas, relanza el instalador de <code>main</code> con <code>--scope user</code>. En 0.7.0 no recrea <code>/alfred</code>.</p><p>Desinstalar:</p><pre>curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash</pre><pre>irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.ps1 | iex</pre><p>Quita plugin, marketplace, caché y el alias <code>/alfred</code> de 0.6.1 si queda. No borra el <code>.claude/</code> del proyecto.</p>',
      },
      {
        svgContent: '<path d="M3 12h18"/>',
        question: 'Hay un alias /alfred?',
        answerHtml: '<p>En 0.7.0 no. La entrada es <code>/alfred-dev:alfred</code>. El instalador 0.7.0 no escribe en <code>~/.claude/skills</code>.</p><p>Si vienes de 0.6.1, el desinstalador borra ese alias solo cuando el fichero lleva la marca «Alfred Dev global alias».</p>',
      },
      {
        svgContent: '<polyline points="4 17 10 11 4 5"/>',
        question: 'Tengo que aprender los 18 comandos?',
        answerHtml: '<p>No. Escribe en castellano. <code>prompt-route</code> sugiere la ruta (fix, quick, retomar, ship…).</p><p>SessionStart inyecta el briefing. Si quieres el slash, empieza por <code>/alfred-dev:alfred</code>.</p>',
      },
      {
        svgContent: '<path d="M8 6h13"/>',
        question: 'Cuándo quick y cuándo feature?',
        answerHtml: '<p><code>quick</code> es un cambio acotado: dos fases, tests y seguridad, menos ceremonia.</p><p><code>feature</code> si cruza producto, arquitectura o varias fases (hasta 7, con Selina solo si hay frontend).</p>',
      },
      {
        svgContent: '<path d="M12 2v4"/>',
        question: 'Cómo retomo una sesión?',
        answerHtml: '<p><code>/alfred-dev:retomar</code> o «sigue donde lo dejé». Lee <code>.claude/alfred-handoff.json</code>.</p><p>Antes de cortar: <code>/alfred-dev:pause</code>. El tablero está en <code>/alfred-dev:progress</code>.</p>',
      },
      {
        svgContent: '<path d="M3 3v18h18"/>',
        question: 'Qué son progress y uat?',
        answerHtml: '<p><code>progress</code> resume kanban, bloqueos, UAT y trazabilidad. Sustituye standup, blocked, in-progress y validate como slash públicos.</p><p><code>uat</code> registra la aceptación humana: <code>pending</code>, <code>approved</code> o <code>rejected</code>. Los tests automáticos no cierran la UAT.</p>',
      },
      {
        svgContent: '<rect x="3" y="4" width="18" height="12" rx="2"/>',
        question: 'Dónde está la memoria?',
        answerHtml: '<p>En <code>.claude/alfred-memory.db</code> del proyecto (SQLite, WAL, FTS5, 0600). Hay 15 tools MCP.</p><p><code>/alfred-dev:memory-ui</code> abre un visor GET en localhost. No importa el git log. <code>/alfred-dev:memory-ui stop</code> o SessionEnd la cierran. Si está vacía, se ve vacía.</p>',
      },
      {
        svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>',
        question: 'Cuántos agentes y skills hay?',
        answerHtml: '<p>10 agentes: 8 de núcleo, Selina si hay frontend y Lucius bajo demanda (<code>/alfred-dev:ajustes</code>).</p><p>11 skills planas. Las de efectos (SonarQube, estilo, incidente, PR) piden invocación explícita. 18 comandos publicados <code>/alfred-dev:*</code>.</p>',
      },
      {
        svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        question: 'Está alineado con el SDK de Anthropic?',
        answerHtml: '<p>Sí. <code>plugin.json</code> lista los 18 comandos, las skills se descubren solas, los hooks van como <code>command</code> + <code>args</code> y el MCP es oficial.</p><p>No hay alias global <code>/alfred</code>, ni Stop hook tipo Ralph, ni reescritura de <code>settings.json</code> para instalar.</p>',
      },
      {
        svgContent: '<line x1="12" y1="1" x2="12" y2="23"/>',
        question: 'Cuánto cuesta y en qué idioma responde?',
        answerHtml: '<p>El plugin es MIT. El coste es el de tu sesión de Claude Code.</p><p>Responde en castellano de España por defecto. Se ajusta en <code>/alfred-dev:ajustes</code>.</p>',
      },
      {
        svgContent: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>',
        question: 'Qué pasa si una gate falla?',
        answerHtml: '<p>El flujo se para y explica el motivo.</p><p>Autopilot solo autoaprueba gates de usuario configuradas. No salta tests, seguridad, evidencia ni la confirmación humana de despliegue.</p>',
      },
      {
        svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>',
        question: 'Puedo contribuir?',
        answerHtml: '<p>Sí. MIT. Issues y PRs en <a href="https://github.com/686f6c61/alfred-dev" target="_blank" rel="noopener noreferrer">github.com/686f6c61/alfred-dev</a>.</p>',
      },
    ],
  },

  changelog: [
    {
      version: '0.7.0',
      date: '2026-08-15',
      added: [
        '<strong>Alineado con el SDK de Claude Code</strong>: comandos, skills planas, hooks en exec form y MCP oficial (FastMCP) si el paquete <code>mcp</code> está instalado.',
        '<strong>Habla sin slash</strong>: SessionStart inyecta el protocolo y <code>prompt-route.py</code> sugiere fix, quick o retomar cuando escribes en castellano.',
        '<strong>Documentación viva</strong>: índice, arquitectura, compliance, threat-model y ADRs en el repo del usuario, sincronizados por fase.',
        '<strong>Cierre de sesión</strong>: SessionEnd escribe <code>.claude/alfred-last-cierre.md</code> y detiene Memory UI.',
      ],
      changed: [
        'Superficie pública recortada: 10 agentes, 11 skills planas, 18 comandos. Entrada <code>/alfred-dev:alfred</code>.',
        'Continuidad pública: <code>alfred</code>, <code>progress</code> y <code>retomar</code>. <code>config</code> pasa a <code>ajustes</code>, <code>verify</code> a <code>uat</code>.',
        'Sin stop-hook Ralph y sin reescribir <code>settings.json</code>. Secret-guard cubre Write, Edit, Bash y tools MCP.',
        'Agent Teams solo si el usuario ya lo tiene activo. Memory UI no importa el historial de Git.',
      ],
      removed: [
        'Alias global <code>/alfred</code> y el catálogo 0.6 de 9 opcionales (data-engineer, github-manager, librarian y el resto).',
        'Comandos públicos <code>next</code>, <code>search</code>, <code>standup</code>, <code>validate</code>, <code>help</code> y <code>status</code>.',
      ],
    },
    {
      version: '0.6.1',
      date: '2026-06-22',
      changed: [
        '<strong>Instaladores más resistentes</strong>: Bash y PowerShell limpian checkouts locales obsoletos del marketplace de Claude Code antes de reinstalar.',
        '<strong>Actualización global normalizada</strong>: el flujo vuelve a registrar la fuente GitHub, refresca el marketplace <code>alfred-dev</code> y mantiene la instalación en scope <code>user</code>.',
      ],
      fixed: [
        'Corrige el caso donde Claude Code mostraba <code>Successfully installed plugin: alfred-dev@alfred-dev</code>, pero la caché instalada seguía resolviendo una versión antigua como <code>0.5.2</code>.',
        'El alias <code>/alfred</code> vuelve a materializarse desde la raíz correcta del plugin tras actualizar desde versiones antiguas o cachés locales heredadas.',
      ],
    },
    {
      version: '0.6.0',
      date: '2026-06-19',
      changed: [
        '<strong>Agentes cargados desde la raíz</strong>: los 9 agentes opcionales pasan a <code>agents/</code> para que Claude Code descubra los 19 agentes del plugin.',
        '<strong>MCP compatible con la CLI actual</strong>: <code>alfred-memory</code> se declara en <code>.mcp.json</code> con un lanzador portable que usa <code>CLAUDE_PLUGIN_ROOT</code> instalado y <code>cwd</code> en desarrollo local.',
        '<strong>Nomenclatura actualizada</strong>: comandos, agentes y documentación operativa sustituyen referencias obsoletas a <code>Task</code> por <code>Agent</code>.',
        '<strong>Nombre humano en la UI</strong>: <code>plugin.json</code> y <code>marketplace.json</code> declaran <code>displayName: "Alfred Dev"</code> para que Claude Code muestre <code>Alfred Dev (alfred-dev)</code> sin cambiar el namespace técnico.',
        'Release de estabilización 0.6.0: <code>plugin.json</code> queda como fuente canónica de versión y el marketplace no duplica <code>version</code>.',
        'El servidor MCP de memoria habla JSONL stdio moderno y mantiene lectura compatible con <code>Content-Length</code> heredado.',
      ],
      fixed: [
        'Claude Code ya puede mostrar los 19 agentes en el inventario del plugin.',
        'Claude Code vuelve a contar <code>alfred-memory</code> dentro del inventario del plugin.',
        '<code>claude mcp get plugin:alfred-dev:alfred-memory</code> conecta correctamente contra el servidor real.',
      ],
    },
    {
      version: '0.5.2',
      date: '2026-04-11',
      added: [
        '<strong>Catálogo completo de skills publicado</strong>: <code>plugin.json</code> deja de enumerar una muestra parcial y pasa a exponer los 15 dominios completos de <code>skills/</code>.',
        '<strong>Contratos de superficie pública más estrictos</strong>: la suite valida catálogo publicado, frontmatters canónicos, skills manuales y ausencia de colisiones con comandos.',
        '<strong>Selina con flujo guiado real</strong>: primero sistema base, luego tipografía y paleta, y solo después tres propuestas finales comparables dentro de esa misma familia.',
      ],
      changed: [
        'Los skills más pesados o con side effects claros quedan publicados, pero forzados a activación manual con <code>disable-model-invocation: true</code>.',
        'La ayuda y la documentación pública agrupan ahora los comandos por valor real: core, operativos avanzados y vistas/aliases.',
        'Las propuestas finales de Selina ya respetan el sistema visual elegido y dejan de recolorear la misma maqueta genérica.',
        'La landing deja de presentar el catálogo como una muestra interna/parcial y refleja ya las 62 skills publicadas de la release.',
        'Versionado coherente a 0.5.2 en plugin, marketplace, instaladores, paquetes, docs, changelog y landing.',
      ],
      fixed: [
        '<code>style-direction</code> ya declara un frontmatter canónico y no depende de inferencias implícitas.',
        'La superficie pública de skills deja de depender de listas parciales desalineadas con el repositorio real.',
        'El companion visual de Selina registra la elección humana incluso cuando el WebSocket local no completa el handshake y necesita fallback HTTP.',
      ],
    },
    {
      version: '0.5.1',
      date: '2026-04-10',
      added: [
        '<strong>Catálogo canónico de Selina con 10 sistemas de diseño base</strong>: <code>core/selina_style_catalog.py</code> reúne el modo libre/contextual y nueve familias visuales guiadas por tendencia para que la fase visual parta de un vocabulario explícito.',
        '<strong>Galería de demos visuales</strong>: <code>core/selina_style_demo.py</code> y <code>visual/scripts/write-style-demo-gallery.py</code> generan una muestra navegable del catálogo antes de cerrar las tres propuestas finales.',
        '<strong>Paletas y tipografías por familia</strong>: cada sistema de diseño declara modos cromáticos, pairing tipográfico y enlaces a referencias o Google Fonts.',
      ],
      changed: [
        'Selina deja de presentarse como “tres estilos” aislados: ahora trabaja con 10 sistemas de diseño base y los reduce a tres propuestas comparables según PRD, audiencia y stack.',
        'Versionado coherente a 0.5.1: plugin, marketplace, instaladores, paquetes, memoria MCP, session report, README, changelog, docs y landing quedan alineados.',
        'La landing explica mejor cómo entra Selina en el flujo y qué significa realmente cerrar un sistema de diseño antes de tocar frontend.',
      ],
      fixed: [
        'Superficie de actualización sin drift: los puntos internos que todavía caían por defecto a una release anterior pasan a reflejar la release actual.',
        'Tests de release menos frágiles: la suite deja de depender de wrappers finos de Astro o rutas hardcodeadas por versión cuando la fuente de verdad es el manifiesto.',
      ],
    },
    {
      version: '0.5.0',
      date: '2026-03-31',
      added: [
        '<strong>Lucius — El Director Técnico</strong>: nuevo agente opcional que actúa como segunda opinión técnica externa. Invoca <code>codex exec</code> con sandbox explícito de solo lectura, usa el modelo configurado en Codex CLI y entrega diagnóstico + prescripción por ítem.',
        '<strong>Comando <code>/alfred-dev:lucius</code></strong>: punto de entrada para invocar la auditoría. Acepta directorio objetivo y scope opcionales (<code>all</code>, <code>security</code>, <code>tests</code>, <code>architecture</code>, <code>performance</code>).',
        '<strong>Informe estructurado por ítem</strong>: Lucius devuelve diagnóstico + prescripción + esfuerzo (S/M/L) + sugerencia de con quién implementar (Alfred o Codex) en cuatro secciones: Crítico, Relevante, Oportunidades y Lo que está bien.',
        '<strong>Preflight de prerequisitos</strong>: verifica que <code>codex</code> está en el PATH y autenticado. Si falta algún requisito, para con instrucciones claras de instalación.',
        '<strong>HARD-GATE sin modificaciones</strong>: Lucius compara el estado Git antes y después de ejecutar Codex CLI en <code>--sandbox read-only</code>; si detecta diferencias, lo reporta y no oculta el problema.',
        '<strong>Selina — La Estilista</strong>: nuevo agente de núcleo (10.º) que ocupa la fase 1b del flujo <code>feature</code> y presenta tres direcciones de estilo visual antes de diseñar componentes.',
        '<strong>Servidor visual local</strong>: servidor HTTP + WebSocket de dependencias cero en <code>visual/scripts/server.cjs</code> con hot-reload, sesiones por proyecto y cierre limpio.',
        '<strong>Skill de estilo visual</strong>: <code>skills/estilo/style-direction/SKILL.md</code> guía a Selina para arrancar el servidor, proponer opciones, recoger la elección y generar <code>docs/style-direction.md</code>.',
        '<strong>Fase condicional <code>estilo_visual</code></strong>: el orquestador la activa sólo cuando <code>config_loader.has_frontend(stack)</code> detecta interfaz de usuario.',
        '<strong>Helper <code>_advance_skipping_phases</code></strong>: función extraída del orquestador para gestionar saltos de fase cuando una condición no se cumple y reducir complejidad cognitiva.',
      ],
      changed: [
        '19 agentes totales: el plugin pasa de 18 a 19 agentes (10 de núcleo + 9 opcionales) con la incorporación de Lucius.',
        '26 comandos: <code>/alfred-dev:lucius</code> entra en el manifiesto y en la superficie pública del plugin.',
        'Versionado coherente a 0.5.0: plugin, marketplace, instaladores, paquetes, README, changelog, docs y landing quedan alineados.',
        'Landing actualizada: tarjeta de Lucius antes de Selina con badge «Nuevo», agente opcional con casos de uso y contadores ajustados a 19 agentes y 26 comandos.',
      ],
      fixed: [
        'Imports de módulos nativos en <code>server.cjs</code>: prefijo <code>node:</code> obligatorio (<code>node:http</code>, <code>node:crypto</code>, <code>node:fs</code>, <code>node:path</code>).',
        '<code>Number.parseInt</code> en lugar de <code>parseInt</code> en <code>server.cjs</code> (regla de linting SonarQube).',
        'Complejidad cognitiva de <code>handleRequest</code> reducida: el bloque <code>/files/*</code> se extrae a <code>serveStaticFile()</code>.',
        'Bloque <code>catch</code> sin variable no usada: <code>catch (e)</code> pasa a <code>catch {}</code> en <code>serveStaticFile</code>.',
        'Complejidad cognitiva en <code>config_loader.py</code>: <code>_count_source_files</code> y <code>suggest_optional_agents</code> bajan extrayendo helpers reutilizables.',
        'Skill de SonarQube registrado en <code>plugin.json</code>: el fichero existía pero no estaba en el manifiesto del plugin.',
        'Ejecución de Docker en subagentes: entradas acotadas <code>Bash(docker ...)</code> permiten que <code>security-officer</code> ejecute el flujo de SonarQube después de que <code>/audit</code> confirme Docker operativo o el usuario autorice prepararlo.',
      ],
    },
    {
      version: '0.4.7',
      date: '2026-03-31',
      fixed: [
        'Hook SessionStart corregido: la emisión JSON del contexto de sesión ya no se trunca cuando el contenido supera ARG_MAX del kernel o contiene caracteres especiales.',
      ],
      changed: [
        'La generación JSON del hook pasa de interpolación en heredoc bash a emisión directa por stdin con json.dumps, eliminando la clase de error por completo.',
        'Versionado coherente a 0.4.7: plugin, marketplace, instaladores, paquetes, metadata estructurada, README, changelog, docs y landing quedan alineados.',
      ],
    },
    {
      version: '0.4.6',
      date: '2026-03-23',
      added: [
        'Nueva Memory UI local: /alfred-dev:memory-ui abre overview, timeline, decisiones, commits, búsqueda y health directamente sobre la SQLite del proyecto.',
        'La Memory UI ya nace con datos útiles: map-codebase, discuss y quick siembran progreso, trazabilidad, kanban e iteraciones ligeras de forma natural.',
        'La UI importa commits Git recientes cuando la memoria aún no tenía commits enlazados y muestra mejor los estados vacíos en workspaces temporales o sin repo.',
        'Cobertura E2E ampliada para Memory UI, siembra helper-first y renderizado visual del servidor local.',
      ],
      changed: [
        'Alfred pasa a reflejar 25 comandos visibles y añade memory-ui como superficie pública de primer nivel en web, README, help y session-start.',
        'La release limpia docs internas de planificación y alinea homepage, metadata y documentación operativa para 0.4.6.',
      ],
    },
    {
      version: '0.4.5',
      date: '2026-03-22',
      added: [
        'Nueva capa PM para SonIA: /alfred-dev:standup, /alfred-dev:blocked, /alfred-dev:in-progress, /alfred-dev:validate y /alfred-dev:search.',
        'SonIA Sync para GitHub mediante /alfred-dev:sync-github, manteniendo docs/project y SQLite como fuente de verdad.',
        'Cobertura E2E ampliada para helpers PM, parsing del tablero y sincronización de Issues.',
      ],
      changed: [
        'Alfred expone ahora 24 comandos y 13 hooks visibles: continuidad, PM operativo, memoria persistente y flujos multiagente en una sola interfaz.',
        'La web, el README y la documentación se alinean con SonIA operativa en CLI y con la nueva capa de colaboración en GitHub.',
      ],
    },
    {
      version: '0.4.4',
      date: '2026-03-22',
      added: [
        'Capa operativa de continuidad: nuevos comandos /alfred-dev:map-codebase, /alfred-dev:next, /alfred-dev:pause, /alfred-dev:resume, /alfred-dev:verify y /alfred-dev:progress.',
        'Comando /alfred-dev:discuss para refinar ideas antes de construir, con artefactos discovery.md y current.md.',
        'Nuevo flujo /alfred-dev:quick de 2 fases para cambios pequeños con tests y revisión de seguridad.',
        'Parser compartido de configuración de memoria y nueva cobertura para FTS de eventos, purge + health, import Git con "|" y sync más allá de 1000 decisiones.',
      ],
      changed: [
        '/alfred pasa a ser un router contextual: decide si toca continuidad, brownfield, refinado o flujo multiagente.',
        'SessionStart bootstrappea la configuración local y recomienda el siguiente paso desde la primera sesión.',
        'La web se alinea con el modelo actual: 6 flujos de ejecución, 18 comandos y capa operativa visible.',
        'La memoria persistente deja de dar falsos errores: los eventos con content son buscables, la purga limpia FTS, retention_days se lee desde la config del proyecto y size_bytes incluye WAL.',
      ],
    },
    {
      version: '0.4.2',
      date: '2026-03-14',
      fixed: [
        'Falso positivo en evidence guard: el patron de deteccion de fallos detectaba "0 failures" como fallo. Corregido para excluir el cero.',
        'Gate de arquitectura mal tipada: la fase de arquitectura tenia gate "usuario" en lugar de "usuario+seguridad", haciendo inoperante la validacion de seguridad.',
        'Patrones divergentes: quality-gate.py tenia patrones propios que divergian de evidence_guard_lib.py. Unificado para usar una sola fuente de verdad.',
        'Clave de autopilot inconsistente: los comandos buscaban "modo: autopilot" pero el codigo escribia "autopilot: true". Corregido.',
      ],
      added: [
        'Soporte para go test en evidence guard: la salida de go test se detecta correctamente como exito.',
        'Informe de sesiones parciales: el stop-hook genera informe cuando una sesion se interrumpe, no solo cuando se completa.',
        'Modo autopilot e iteraciones en informes: los informes muestran si la sesion fue autopilot y cuantos reintentos tuvo cada fase.',
        'Verificacion de evidencia en markdown: instruccion explicita para que se lea alfred-evidence.json antes de avanzar gates automaticas.',
        'Loop iterativo documentado en los comandos feature, fix y ship (max 5 reintentos por fase).',
      ],
      changed: [
        'Stop-hook refactorizado en funciones testables: should_block, build_block_message, handle_session_report.',
        'Mensaje de bloqueo adaptado a autopilot: no pide confirmacion del usuario sino que indica investigar el error.',
        'Version dinamica en informes: el template lee la version de plugin.json.',
        'Limpieza de evidencia entre sesiones para evitar contaminacion cruzada.',
      ],
    },
    {
      version: '0.4.1',
      date: '2026-03-13',
      added: [
        'Configuracion inicial automatica: al usar Alfred por primera vez en un proyecto, pregunta si se quiere modo interactivo o autopilot. Sin pasos manuales previos.',
      ],
      fixed: [
        'Modo autopilot desconectado del flujo real: la deteccion de autopilot no llegaba a la composicion. Corregido para que las gates de usuario se aprueben automaticamente cuando el modo es autopilot.',
      ],
    },
    {
      version: '0.4.0',
      date: '2026-03-13',
      added: [
        'Verificacion de evidencia (evidence guard): hook que registra cada ejecucion de tests como evidencia verificable. Cuando un agente afirma que los tests pasan, el sistema comprueba que efectivamente se ejecutaron.',
        'Informe de sesion al cierre: resumen automatico en docs/alfred-reports/ con fases, evidencia de tests, equipo y artefactos.',
        'Loop iterativo dentro de fases: los agentes iteran hasta 5 veces dentro de una fase hasta superar la gate, habilitando ciclos TDD naturales.',
        'Modo autopilot: ejecucion completa sin interrupcion humana. Las gates de usuario se aprueban automaticamente; las automaticas y de seguridad se evaluan normalmente.',
      ],
      changed: [
        '17 personalidades reescritas con tono Alfred Pennyworth: servicio impecable, ironia sutil, precision tecnica.',
        'Orquestador ampliado con funciones de loop iterativo (should_retry_phase, reset_phase_iterations) y autopilot (is_autopilot_gate_passable, run_flow_autopilot).',
        'Stop-hook genera informe de sesion automaticamente al cerrar una sesion completada.',
      ],
    },
    {
      version: '0.3.9',
      date: '2026-03-13',
      added: [
        'Agente opcional i18n-specialist para proyectos multiidioma: deteccion automatica de señales i18n (directorios i18n/, locales/, translations/), integracion en fases de desarrollo y calidad.',
        'Deteccion automatica de i18n en suggest_optional_agents(): analiza directorios y ficheros de configuracion i18n del proyecto.',
      ],
      changed: [
        'Seleccion de agentes opcionales rediseñada: 2 preguntas multiSelect agrupadas por tema (técnicos + contenido/UX) en vez de una lista larga, compatible con el limite de 4 opciones de AskUserQuestion.',
        'Product Owner reformulado: las preguntas de la fase de producto se hacen una a una (una por turno) en vez de en bloque, siguiendo el patron de refinamiento progresivo de superpowers:brainstorming.',
        '8 agentes opcionales (antes 7): añadido i18n-specialist al catalogo, config, orquestador, documentacion y tests.',
      ],
    },
    {
      version: '0.3.8',
      date: '2026-03-13',
      added: [
        'Capa de sincronizacion SQLite a memoria nativa: las decisiones, iteraciones y commits almacenados en alfred-memory.db se proyectan automaticamente como ficheros .md en ~/.claude/projects/<hash>/memory/ con formato nativo de Claude Code.',
        'Sincronizacion hibrida: regeneracion completa al arrancar la sesion + actualizaciones incrementales tras cada escritura en SQLite.',
        'Gestion segura de MEMORY.md con marcadores delimitados que preservan el contenido manual del usuario.',
        'Creacion automatica del directorio de memoria al cargar Alfred por primera vez.',
        'Nuevo skill de testing E2E (calidad/e2e-testing) para configurar Playwright o Cypress.',
      ],
      changed: [
        '60 skills revisadas y mejoradas: descriptions enriquecidas para mejor triggering, seccion "Que NO hacer" en 51 skills, integracion con memoria persistente en 10 skills, referencia a detect_stack en 9 skills.',
        '3 protocolos sueltos (incident-response, dependency-strategy, release-planning) reorganizados en sus categorias logicas (calidad/, seguridad/, devops/).',
        'Solapamientos entre skills documentados explicitamente. Versiones normativas (RGPD, NIS2, CRA, OWASP, WCAG) añadidas.',
      ],
    },
    {
      version: '0.3.7',
      date: '2026-03-12',
      added: [
        '<strong>SonIA -- Project Manager</strong> -- nuevo agente de nucleo transversal. Descompone el PRD en tareas, gestiona un kanban en <code>docs/project/kanban/</code> con 4 ficheros MD (backlog, in-progress, done, blocked), mantiene la matriz de trazabilidad (criterio -- tarea -- test -- doc) y genera informes de progreso por fase.',
        '<strong>La Intérprete -- i18n Specialist</strong> -- nuevo agente opcional para internacionalización. Auditoría de claves i18n, detección de cadenas hardcodeadas, validación de formatos por locale, generación de esqueletos para nuevos idiomas. HARD-GATE: completitud de claves (N en base = N en todos los idiomas).',
        '<strong>QA Engineer ampliado</strong> -- nueva seccion de testing de integracion y E2E con estrategias para Playwright/Cypress, tabla de decision entre tipos de test (unitario, integracion, E2E, regresion) y criterios de seleccion.',
      ],
      changed: [
        '<strong>El Escriba (antes El Traductor)</strong> -- tech-writer reescrito como agente de nucleo con doble activacion: fase 3b (documentacion inline de codigo: cabeceras, docstrings, comentarios de contexto) y fase 5 (documentacion de proyecto: API, arquitectura con diagramas Mermaid, guias, changelogs). Guia de estilo estricta: castellano sin latinismos, anglicismos permitidos, sin emojis.',
        '<strong>HARD-GATEs en 5 agentes opcionales</strong> -- data-engineer (integridad de migraciones), ux-reviewer (WCAG 2.1 nivel A), performance-engineer (umbrales de rendimiento), seo-specialist (requisitos minimos de indexacion), github-manager (operaciones destructivas requieren confirmacion).',
        '<strong>Equipo ampliado a 17 agentes</strong> -- 9 de nucleo (antes 8) + 8 opcionales (antes 7). Todos los conteos actualizados en web, README y manifiesto.',
        '<strong>Colores de agentes unificados</strong> -- QA Engineer de red a amber (conflicto con security-officer), performance-engineer y copywriter alineados entre frontmatter y cuerpo del agente.',
        '<strong>Memoria persistente mejorada</strong> -- optimizaciones en el modulo SQLite, consultas mas eficientes y mejor gestion de la base de datos entre sesiones.',
        '<strong>Hooks de captura unificados</strong> -- <code>memory-capture.py</code> y <code>commit-capture.py</code> fusionados en <code>activity-capture.py</code>, un unico hook con dispatch interno por tipo de evento. De 11 a 10 hooks.',
        '<strong>Todos los agentes revisados</strong> -- inconsistencias corregidas en frontmatter, descripciones alineadas con las capacidades reales, personalidades refinadas y cadenas de integracion actualizadas.',
      ],
      removed: [
        '<strong>Dashboard GUI eliminado</strong> -- la interfaz web del dashboard (introducida en v0.3.0) se retira por no cumplir las expectativas de usabilidad. La funcionalidad de estado se cubre con <code>/alfred-dev:status</code>.',
      ],
    },
    {
      version: '0.3.6',
      date: '2026-03-10',
      fixed: [
        '<strong>Agentes de nucleo registrados</strong> -- los 7 agentes de nucleo no estaban en el manifiesto del plugin y Claude Code no cargaba sus system prompts. Ahora los 15 agentes (8 nucleo + 7 opcionales) estan registrados y operativos.',
        '<strong>Herramientas MCP del librarian</strong> -- el agente librarian referenciaba 5 herramientas MCP con nombres incorrectos. Corregidos a los nombres reales del servidor.',
        '<strong>Dashboard vacio en primera sesion</strong> -- el pipeline de datos fallaba en cascada: config sin memoria, commits sin iteracion y consultas vacias. Corregido con auto-creacion de config, iteracion automatica y fallback global.',
        '<strong>Conflicto de puertos</strong> -- si otro proyecto usaba los puertos del dashboard, ahora se detecta y se buscan alternativas automaticamente.',
      ],
    },
    {
      version: '0.3.5',
      date: '2026-03-10',
      changed: [
        '<strong>SonarQube movido al security-officer</strong> -- el análisis de SonarQube lo ejecuta ahora el security-officer en lugar del qa-engineer durante <code>/alfred-dev:audit</code>. Cuando Docker está operativo o autorizado, ejecuta el scanner e integra los hallazgos en su informe de seguridad.',
        '<strong>Instrucciones imperativas</strong> -- el subagente recibe pasos explícitos y secuenciales (leer el skill, ejecutar los 7 pasos, integrar resultados) en lugar de una referencia textual que podía ignorarse.',
      ],
    },
    {
      version: '0.3.4',
      date: '2026-03-03',
      fixed: [
        '<strong>Nomenclatura de comandos</strong> -- todos los comandos de la web actualizados de <code>/alfred X</code> a <code>/alfred-dev:X</code> para reflejar la convención real de Claude Code.',
        '<strong>Stats corregidos</strong> -- skills de 56 a 59, comandos de 10 a 11, hooks de 7 a 11. Alineados con la implementación real.',
        '<strong>Comando /alfred-dev:gui visible</strong> -- añadido a la tabla pública de comandos en ambos idiomas.',
        '<strong>SonarQube integrado en audit</strong> -- el security-officer ejecuta el skill de SonarQube después de que el preflight de audit confirme Docker operativo o el usuario autorice prepararlo.',
        '<strong>Fichero de puertos del dashboard</strong> -- <code>session-start.sh</code> crea <code>.claude/alfred-gui-port</code> y verifica la conexión real al servidor en vez de confiar en <code>kill -0</code>.',
        '<strong>Colores de agentes opcionales</strong> -- los 5 agentes sin color en el frontmatter ahora tienen colores asignados para el dashboard.',
      ],
    },
    {
      version: '0.3.3',
      date: '2026-02-24',
      fixed: [
        '<strong>Inicialización de SQLite al arrancar</strong> -- la BD de memoria se crea automáticamente en cada sesión si no existe. Elimina la dependencia circular que impedía arrancar el servidor GUI en la primera sesión.',
        '<strong>Servidor GUI siempre operativo</strong> -- el dashboard arranca desde el minuto 1. El WebSocket está disponible inmediatamente para el cliente.',
        '<strong>Agentes servidos por WebSocket</strong> -- el catálogo de 15 agentes se envía desde el servidor en el mensaje <code>init</code>, eliminando la lista hardcodeada en el dashboard.',
        '<strong>Hooks resilientes a actualizaciones</strong> -- guardas <code>test -f</code> en todos los hooks para degradación graceful cuando el directorio del plugin ha cambiado.',
      ],
    },
    {
      version: '0.3.2',
      date: '2026-02-23',
      added: [
        '<strong>Composición dinámica de equipo</strong> -- sistema de 4 capas (heurística, razonamiento, presentación, ejecución) que sugiere agentes opcionales según la descripción de la tarea. La selección es efímera y no modifica la configuración persistente.',
        '<strong>Función run_flow()</strong> -- punto de entrada para flujos con equipo de sesión efímero. Valida la estructura, inyecta el equipo y registra diagnósticos de error.',
        '<strong>Tabla TASK_KEYWORDS</strong> -- mapa de 8 agentes opcionales con keywords contextuales y pesos base para la composición dinámica.',
      ],
      fixed: [
        '<strong>Matching por palabra completa</strong> -- <code>match_task_keywords()</code> usa word boundary en vez de subcadena, eliminando falsos positivos para keywords cortas.',
        '<strong>Retroalimentación de validación</strong> -- el motivo del descarte del equipo se registra en la sesión para diagnóstico.',
        '<strong>Aviso al truncar</strong> -- descripciones de tarea mayores de 10 000 caracteres emiten aviso en vez de truncarse silenciosamente.',
      ],
      changed: [
        '<code>_KNOWN_OPTIONAL_AGENTS</code> derivado de <code>TASK_KEYWORDS</code> (fuente única de verdad). 6 skills de comandos actualizados. 326 tests.',
      ],
    },
    {
      version: '0.3.1',
      date: '2026-02-23',
      fixed: [
        '<strong>Lectura robusta de frames WebSocket</strong> -- reescrito con <code>readexactly()</code> para eliminar desconexiones por fragmentación TCP.',
        '<strong>Conexión SQLite cross-thread</strong> -- añadido <code>check_same_thread=False</code> para evitar errores en Python 3.12+.',
        '<strong>Consistencia en get_full_state()</strong> -- todas las consultas usan la misma conexión de polling.',
        '<strong>Polling de marcados</strong> -- los elementos marcados ahora se propagan en tiempo real.',
        '<strong>Formato de timestamps</strong> -- detección automática de epoch (s/ms) y cadenas ISO sin zona horaria.',
        '<strong>Validación de tipos en acciones GUI</strong> -- casts explícitos para prevenir inyección de tipos.',
        '<strong>Buffer de handshake WebSocket</strong> -- ampliado a 8192 bytes.',
        '<strong>Limpieza de writers WebSocket</strong> -- cierre explícito de sockets al parar el servidor.',
      ],
      added: [
        '<strong>Soporte móvil</strong> -- menú hamburguesa con sidebar deslizante para pantallas estrechas.',
        '<strong>Cabeceras de seguridad HTTP</strong> -- X-Content-Type-Options, Cache-Control y Content-Security-Policy.',
        '<strong>Inyección dinámica</strong> -- versión y puerto WebSocket inyectados desde el servidor, sin valores hardcodeados.',
        '<strong>Icono SVG de marcado</strong> -- sustituido <code>[*]</code> por icono de pin en timeline y decisiones.',
        '<strong>Auditoría SEO</strong> -- canonical, og:image, FAQPage schema, hreflang, dimensiones de imágenes (CLS).',
      ],
    },
    {
      version: '0.3.0',
      date: '2026-02-22',
      added: [
        '<strong>Dashboard GUI</strong> (Fase Alpha) -- dashboard web en tiempo real con 7 vistas: estado, timeline, decisiones, agentes, memoria, commits y marcados. Se lanza con <code>/alfred-dev:gui</code>.',
        '<strong>Servidor monolítico Python</strong> -- HTTP + WebSocket RFC 6455 manual + SQLite watcher. Sin dependencias externas.',
        '<strong>Protocolo WebSocket bidireccional</strong> -- mensajes <code>init</code>, <code>update</code>, <code>action</code> y <code>action_ack</code>. Reconexión con backoff exponencial.',
        '<strong>Sistema de marcado</strong> -- elementos marcados sobreviven a la compactación del contexto.',
        '<strong>Tablas SQLite nuevas</strong> -- <code>gui_actions</code> y <code>pinned_items</code>. Migración automática a esquema v3.',
        '<strong>Arranque automático</strong> -- el servidor GUI se levanta con cada sesión y se para al cerrar.',
        'Principio fail-open: si la GUI falla, Alfred funciona igual. 297 tests.',
      ],
      changed: [
        'README y documentación ampliados con capturas del dashboard y guía del protocolo WebSocket.',
      ],
    },
    {
      version: '0.2.3',
      date: '2026-02-21',
      added: [
        '<strong>Memoria persistente v2</strong> -- migración de esquema, etiquetas, estado y relaciones entre decisiones.',
        '<strong>5 herramientas MCP nuevas</strong> -- total 15: update, link, health, export, import.',
        '<strong>Filtros de búsqueda</strong> -- parámetros <code>since</code>, <code>until</code>, <code>tags</code>, <code>status</code>.',
        '<strong>Export/Import</strong> -- decisiones a Markdown (ADR), import desde Git y ADRs.',
        '<strong>Hook activity-capture.py</strong> -- hook unificado de captura (eventos del flujo + commits).',
        '<strong>Hook memory-compact.py</strong> -- protege decisiones durante la compactación.',
        'Inyección de contexto por iteración activa. ~268 tests.',
      ],
      changed: [
        'El Bibliotecario ampliado: ciclo de vida de decisiones, integridad, export/import.',
      ],
    },
    {
      version: '0.2.2',
      date: '2026-02-21',
      added: [
        '<strong>Hook dangerous-command-guard.py</strong> -- bloquea <code>rm -rf /</code>, force push, <code>DROP DATABASE</code>, fork bombs y más.',
        '<strong>Hook sensitive-read-guard.py</strong> -- aviso al leer claves privadas, <code>.env</code>, credenciales.',
        '<strong>4 herramientas MCP nuevas</strong> -- total 10: stats, iteraciones, abandon.',
        '<strong>3 skills nuevos</strong> -- incident-response, release-planning, dependency-strategy.',
        '<code>/alfred-dev:feature</code> permite seleccionar fase de inicio.',
        'Test de consistencia de versión. 219 tests en total.',
      ],
      fixed: [
        '<strong>quality-gate.py</strong> -- ancla de posición para runners, <code>re.IGNORECASE</code> en fallos.',
        'Respuestas MCP con <code>isError: true</code> para errores.',
        '8 incidencias de deuda técnica: logging, encapsulación, recuperación.',
      ],
    },
    {
      version: '0.2.1',
      date: '2026-02-21',
      fixed: [
        '<strong>Ruta de caché en Windows</strong> -- install.ps1 y uninstall.ps1 alineados con la convención de Claude Code.',
        '<strong>activity-capture.py</strong> -- diagnóstico en bloques except silenciosos.',
        '<strong>session-start.sh</strong> -- catches específicos en vez de Exception genérico.',
      ],
    },
    {
      version: '0.2.0',
      date: '2026-02-20',
      added: [
        '<strong>Memoria persistente</strong> -- SQLite local por proyecto con decisiones, commits, iteraciones y eventos.',
        '<strong>Servidor MCP</strong> -- 6 herramientas stdio: buscar, registrar, consultar.',
        '<strong>El Bibliotecario</strong> -- agente opcional para consultas históricas.',
        '<strong>Hook activity-capture.py</strong> -- captura automática de eventos del flujo.',
        'Búsqueda FTS5, sanitización de secretos, permisos 0600.',
        '114 tests (58 nuevos para memoria).',
      ],
    },
    {
      version: '0.1.5',
      date: '2026-02-20',
      fixed: [
        '<strong>Secret-guard fail-closed</strong> -- bloquea cuando no puede determinar la ruta destino.',
        'Instalador idempotente en entorno limpio (<code>mkdir -p</code>).',
        'Detección de versión en <code>/alfred-dev:update</code> más fiable.',
      ],
    },
    {
      version: '0.1.4',
      date: '2026-02-19',
      added: [
        '<strong>6 agentes opcionales</strong> -- data-engineer, ux-reviewer, performance, github, seo, copywriter.',
        '<strong>27 skills nuevos</strong> en 6 dominios. Total: 56 skills en 13 dominios.',
        '<strong>Soporte Windows</strong> -- install.ps1 y uninstall.ps1 nativos.',
        '<strong>Hook spelling-guard.py</strong> -- tildes omitidas en castellano.',
        'Quality gates ampliados: 8 a 18.',
      ],
    },
    {
      version: '0.1.2',
      date: '2026-02-18',
      changed: [
        '<strong>Nueva personalidad</strong> -- compañero cercano con humor, los 8 agentes con voz propia.',
        'Corrección ortográfica completa en 68 ficheros (RAE).',
      ],
      fixed: [
        'Prefijo correcto en comandos, update robusto, registro explícito de los 10 comandos.',
      ],
    },
    {
      version: '0.1.1',
      date: '2026-02-18',
      fixed: [
        '<strong>session-start.sh</strong> -- error de sintaxis que impedía la inyección de contexto.',
        '<strong>secret-guard.sh</strong> -- política fail-closed restaurada.',
        '<strong>stop-hook.py</strong> -- validación de tipos para estado corrupto.',
      ],
    },
    {
      version: '0.1.0',
      date: '2026-02-18',
      added: [
        'Primera release pública.',
        '8 agentes especializados, 5 flujos, 29 skills, 5 hooks.',
        'Quality gates, compliance RGPD/NIS2/CRA, detección de stack.',
      ],
    },
  ],

  // ----------------------------------------------------------------
  // Footer
  // ----------------------------------------------------------------


  footer: {
    version: 'v0.7.0',
    license: 'MIT License',
    githubUrl: 'https://github.com/686f6c61/alfred-dev',
    docsUrl: 'https://github.com/686f6c61/alfred-dev/tree/main/docs',
    tagline: 'Plugin de Claude Code. 10 agentes. 11 skills planas. 10 hooks. 18 comandos /alfred-dev:*. MCP oficial. Memory UI local. Gates con evidencia. Sin alias global /alfred.',
    slogan: 'Ingeniería de software con método para Claude Code.',
    disclaimer: {
      linkText: 'Descargo de responsabilidad',
      title: 'Descargo de responsabilidad',
      closeText: 'Cerrar',
      contentHtml: `
        <p><strong>Alfred Dev</strong> es un proyecto independiente de codigo abierto. No esta afiliado, patrocinado ni respaldado por <strong>Anthropic</strong> ni por el equipo de <strong>Claude Code</strong>.</p>
        <p>El software se proporciona tal cual, sin garantias. El usuario revisa y aprueba las acciones que el plugin propone.</p>
        <p>Los agentes usan modelos de lenguaje que pueden equivocarse. Trata las salidas como sugerencias.</p>
        <p>Uso sujeto a la <a href="https://github.com/686f6c61/alfred-dev/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">licencia MIT</a>.</p>
      `,
    },
  },
};

export default data;
