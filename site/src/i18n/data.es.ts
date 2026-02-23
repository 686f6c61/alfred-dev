/**
 * Datos de contenido de la landing page en castellano de Espana.
 *
 * Todos los valores se han extraido literalmente del HTML original
 * (index.html.bak, 3755 lineas). Las entidades HTML se han convertido
 * a caracteres Unicode, los colores de agentes se han extraido de los
 * atributos style="--agent-color: ..." y los SVG icon paths de los
 * atributos `d` de cada <path> dentro de los iconos del FAQ y la
 * navegacion.
 *
 * @module i18n/data.es
 */

import type { PageData } from '../types/index';

const data: PageData = {

  // ----------------------------------------------------------------
  // Meta
  // ----------------------------------------------------------------

  meta: {
    title: 'Alfred Dev - plugin de Claude Code para equipos de desarrollo',
    description: 'Plugin de Claude Code: 15 agentes especializados, 59 skills, memoria persistente y quality gates. De la idea a producción con TDD, seguridad y compliance.',
    canonical: 'https://alfred-dev.com/',
    locale: 'es_ES',
    og: {
      type: 'website',
      title: 'Alfred Dev - plugin de Claude Code para equipos de desarrollo',
      description: '15 agentes especializados, 59 skills, memoria persistente y quality gates. Ingeniería de software automatizada para Claude Code.',
      url: 'https://alfred-dev.com/',
      siteName: 'Alfred Dev',
      locale: 'es_ES',
      image: 'https://alfred-dev.com/screenshots/dashboard-estado.webp',
      imageWidth: 1470,
      imageHeight: 759,
      imageType: 'image/webp',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Alfred Dev - plugin de Claude Code para equipos de desarrollo',
      description: '15 agentes especializados, 59 skills, memoria persistente y quality gates. De la idea a producción.',
      image: 'https://alfred-dev.com/screenshots/dashboard-estado.webp',
    },
  },

  // ----------------------------------------------------------------
  // Navegacion
  // ----------------------------------------------------------------

  nav: [
    {
      href: '#agentes',
      label: 'Agentes',
      svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    },
    {
      href: '#dashboard',
      label: 'Dashboard',
      svgContent: '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><path d="M8 21h8"/><path d="M12 17v4"/>',
    },
    {
      href: '#flujos',
      label: 'Flujos',
      svgContent: '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>',
    },
    {
      href: '#skills',
      label: 'Skills',
      svgContent: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    },
    {
      href: '#gates',
      label: 'Gates',
      svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    },
    {
      href: '#infra',
      label: 'Infra',
      svgContent: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    },
    {
      href: '#uso',
      label: 'Uso',
      svgContent: '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>',
    },
    {
      href: '#memoria',
      label: 'Memoria',
      svgContent: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
    },
    {
      href: '#instalar',
      label: 'Instalar',
      svgContent: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    },
    {
      href: '#faq',
      label: 'FAQ',
      svgContent: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    },
  ],

  // ----------------------------------------------------------------
  // Hero
  // ----------------------------------------------------------------

  hero: {
    titleHtml: 'Tus compañeros de<br>desarrollo en un <em>plugin</em>',
    platformHtml: 'para <span style="color: var(--blue);">Claude Code</span> y <span style="color: var(--gold);">OpenCode</span> <span style="font-size: 13px; opacity: 0.7;">(en desarrollo)</span>',
    subtitle: '15 agentes especializados con personalidad propia. 8 de núcleo, 7 opcionales que activas según tu proyecto. Memoria persistente, quality gates, 59 skills, de la idea a producción.',
    ctas: [
      {
        label: 'macOS / Linux',
        command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash',
        ariaLabel: 'Copiar comando de instalación para macOS y Linux',
      },
      {
        label: 'Windows',
        command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex',
        ariaLabel: 'Copiar comando de instalación para Windows',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Stats
  // ----------------------------------------------------------------

  stats: [
    { number: 15, label: 'Agentes' },
    { number: 56, label: 'Skills' },
    { number: 5, label: 'Flujos' },
    { number: 10, label: 'Comandos' },
    { number: 7, label: 'Templates' },
    { number: 7, label: 'Hooks' },
    { number: 18, label: 'Gates' },
  ],

  // ----------------------------------------------------------------
  // Agentes de nucleo
  // ----------------------------------------------------------------

  coreAgents: {
    header: {
      label: 'El equipo',
      title: '8 agentes de núcleo',
      description: 'Cada agente tiene un rol definido, una personalidad propia y frases características. Trabajan coordinados por Alfred, el mayordomo jefe. Siempre activos en cada flujo.',
    },
    agents: [
      {
        name: 'Alfred',
        model: 'opus',
        alias: 'Mayordomo jefe',
        role: 'Orquestador del equipo. Decide qué agentes activar, en qué orden, y evalúa las quality gates entre fases.',
        phrase: '"Muy bien, señor. Permítame organizar eso."',
        color: 'var(--blue)',
      },
      {
        name: 'El buscador de problemas',
        model: 'opus',
        alias: 'Product Owner',
        role: 'Obsesionado con el problema del usuario. PRDs, historias de usuario, criterios de aceptación, análisis competitivo.',
        phrase: '"Muy bonito, pero qué problema resuelve esto?"',
        color: 'var(--purple)',
      },
      {
        name: 'El dibujante de cajas',
        model: 'opus',
        alias: 'Arquitecto',
        role: 'Piensa en sistemas, no en líneas de código. Diagramas Mermaid, ADRs, matrices de decisión, evaluación de dependencias.',
        phrase: '"Si no cabe en un diagrama, es demasiado complejo."',
        color: 'var(--green)',
      },
      {
        name: 'El artesano',
        model: 'opus',
        alias: 'Senior Dev',
        role: 'Pragmático, test-first. TDD estricto, refactoring, commits atómicos. Alergia crónica al código clever.',
        phrase: '"Primero el test. Siempre primero el test."',
        color: 'var(--orange)',
      },
      {
        name: 'El paranoico',
        model: 'opus',
        alias: 'Security Officer',
        role: 'Desconfiado por defecto. OWASP Top 10, compliance RGPD/NIS2/CRA, auditoría de dependencias, threat modeling, SBOM.',
        phrase: '"Habéis validado esa entrada? No, en serio."',
        color: 'var(--red)',
      },
      {
        name: 'El rompe-cosas',
        model: 'sonnet',
        alias: 'QA Engineer',
        role: 'Su misión es demostrar que el código no funciona. Test plans, code review, testing exploratorio, regresión.',
        phrase: '"Ese edge case que no contemplaste? Lo encontré."',
        color: 'var(--red)',
      },
      {
        name: 'El fontanero',
        model: 'sonnet',
        alias: 'DevOps Engineer',
        role: 'Infraestructura invisible es infraestructura bien hecha. Docker, CI/CD, deploy, monitoring. Todo automatizado.',
        phrase: '"Si lo despliegas a mano, lo despliegas mal."',
        color: 'var(--cyan)',
      },
      {
        name: 'El traductor',
        model: 'sonnet',
        alias: 'Tech Writer',
        role: 'Si no está documentado, no existe. API docs, guías de usuario, arquitectura, changelogs, release notes.',
        phrase: '"He visto tumbas con más información que este README."',
        color: 'var(--white)',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Agentes opcionales
  // ----------------------------------------------------------------

  optionalAgents: {
    header: {
      label: 'Ampliables',
      labelColor: 'var(--gold)',
      title: '7 agentes opcionales',
      description: 'Roles especializados que activas según lo que necesite tu proyecto. Alfred analiza tu stack y te sugiere cuáles activar. Se gestionan con <strong style="color: var(--blue);">/alfred config</strong>.',
    },
    agents: [
      {
        name: 'El fontanero de datos',
        model: 'sonnet',
        alias: 'Data Engineer',
        role: 'Diseño de esquemas, migraciones con rollback obligatorio, optimización de queries. Si hay base de datos, hay trabajo.',
        phrase: '"Una migración sin rollback es un billete de ida."',
        color: 'var(--orange)',
      },
      {
        name: 'El abogado del usuario',
        model: 'sonnet',
        alias: 'UX Reviewer',
        role: 'Auditoría WCAG 2.1 AA, heurísticas de Nielsen, revisión de flujos. Lo que es obvio para ti no lo es para el usuario.',
        phrase: '"Si el usuario necesita un manual, has fallado."',
        color: '#ff69b4',
      },
      {
        name: 'El cronómetro',
        model: 'sonnet',
        alias: 'Performance Engineer',
        role: 'Profiling, benchmarks con estadísticas reales (p50, p95, p99), análisis de bundles. Medir antes y después, siempre.',
        phrase: '"Sin números no hay optimización, hay superstición."',
        color: 'var(--purple)',
      },
      {
        name: 'El portero',
        model: 'sonnet',
        alias: 'GitHub Manager',
        role: 'Configuración de repositorios, branch protection, PRs, releases, issue templates. Todo vía gh CLI, sin menciones a IA.',
        phrase: '"Un repo sin protección de ramas es una ruleta rusa."',
        color: 'var(--text-muted)',
      },
      {
        name: 'El rastreador',
        model: 'sonnet',
        alias: 'SEO Specialist',
        role: 'Meta tags, datos estructurados JSON-LD, Core Web Vitals, Lighthouse. Si Google no lo encuentra, no existe.',
        phrase: '"Un canonical mal puesto y tienes contenido duplicado."',
        color: 'var(--green)',
      },
      {
        name: 'La pluma',
        model: 'sonnet',
        alias: 'Copywriter',
        role: 'Revisión de textos, CTAs efectivos, guía de tono. Ortografía impecable como prioridad absoluta. Sin teletienda.',
        phrase: '"Si escribes \'aplicacion\' sin tilde, no publiques."',
        color: 'var(--cyan)',
      },
      {
        name: 'El Bibliotecario',
        model: 'sonnet',
        alias: 'Memoria del proyecto',
        role: 'Responde consultas históricas sobre decisiones, commits e iteraciones del proyecto. Siempre cita las fuentes con IDs verificables: [D#id], [C#sha], [I#id].',
        phrase: '"Según la decisión D#42 del 15 de febrero, se descartó Redis por latencia."',
        color: '#c9a96e',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Composicion dinamica de equipo
  // ----------------------------------------------------------------

  composition: {
    header: {
      label: 'Composición dinámica',
      labelColor: 'var(--gold)',
      title: 'El equipo que necesitas, cuando lo necesitas',
      description: 'Alfred analiza tu tarea en tiempo real y sugiere los agentes opcionales más relevantes. Sin configuración manual: describes lo que quieres hacer y el sistema propone el equipo ideal.',
    },
    introHtml: 'Cuando ejecutas <code style="font-family: var(--font-mono); font-size: 14px; color: var(--cyan);">/alfred feature</code> con una descripción de tarea, el motor de composición extrae las keywords relevantes y puntúa cada agente opcional según su afinidad con el trabajo a realizar. Después te presenta un selector para que confirmes o ajustes el equipo antes de arrancar.',
    terminalPrompt: '$ /alfred feature',
    terminalText: 'Necesito migrar la base de datos de SQLite a PostgreSQL, consultar las decisiones anteriores sobre el esquema de datos para no repetir errores, rediseñar completamente la interfaz del checkout con tests de accesibilidad, escribir todo el copy de la landing de lanzamiento y optimizar el rendimiento de carga en dispositivos móviles',
    coreAgentsLabel: 'Equipo base',
    coreAgentsActiveLabel: 'Siempre activo',
    coreAgents: [
      { id: 'alfred', name: 'Alfred', color: '#e8a44a', role: 'Orquestador' },
      { id: 'product-owner', name: 'Product Owner', color: '#5b9cf5', role: 'Producto' },
      { id: 'architect', name: 'Architect', color: '#a07ee8', role: 'Arquitectura' },
      { id: 'senior-dev', name: 'Senior Dev', color: '#4ec990', role: 'Desarrollo' },
      { id: 'security-officer', name: 'Security Officer', color: '#e5564f', role: 'Seguridad' },
      { id: 'qa-engineer', name: 'QA Engineer', color: '#41b9c3', role: 'Calidad' },
      { id: 'tech-writer', name: 'Tech Writer', color: '#e89a4a', role: 'Documentación' },
      { id: 'devops-engineer', name: 'DevOps Engineer', color: '#6ec4e8', role: 'Entrega' },
    ],
    agentsPanelLabel: 'Agentes opcionales',
    suggestedLabel: 'Sugerido',
    notSuggestedLabel: 'No necesario',
    selectorTitle: 'Equipo propuesto',
    confirmLabel: 'Confirmar equipo',
    agents: [
      {
        id: 'data-engineer',
        name: 'Data Engineer',
        color: '#5b9cf5',
        score: 0.85,
        keywords: ['base de datos', 'PostgreSQL'],
      },
      {
        id: 'ux-reviewer',
        name: 'UX Reviewer',
        color: '#a07ee8',
        score: 0.75,
        keywords: ['interfaz', 'redisenar'],
      },
      {
        id: 'performance-engineer',
        name: 'Performance Engineer',
        color: '#4ec990',
        score: 0.80,
        keywords: ['rendimiento', 'optimizar'],
      },
      {
        id: 'copywriter',
        name: 'Copywriter',
        color: '#e8a44a',
        score: 0.70,
        keywords: ['copy', 'landing'],
      },
      {
        id: 'librarian',
        name: 'Bibliotecario',
        color: '#c9a96e',
        score: 0.65,
        keywords: ['decisiones anteriores', 'esquema'],
      },
      {
        id: 'github-manager',
        name: 'GitHub Manager',
        color: '#8b90a8',
        score: 0.0,
        keywords: [],
      },
      {
        id: 'seo-specialist',
        name: 'SEO Specialist',
        color: '#8b90a8',
        score: 0.0,
        keywords: [],
      },
    ],
  },

  // ----------------------------------------------------------------
  // Dashboard
  // ----------------------------------------------------------------

  dashboard: {
    sectionLabel: 'Fase Alpha',
    title: 'Dashboard en tiempo real',
    descriptionHtml: 'El dashboard web muestra el estado completo del proyecto sin intervenir en el terminal. Fases, agentes, decisiones, commits y timeline actualizados por WebSocket. Se lanza con <code style="font-family: var(--font-mono); font-size: 14px; color: var(--cyan);">/alfred gui</code> y funciona en cualquier navegador.',
    heroImage: {
      src: '/screenshots/dashboard-estado.webp',
      alt: 'Vista de estado del proyecto en el dashboard de Alfred Dev',
      caption: 'Estado del proyecto',
    },
    gridImages: [
      {
        src: '/screenshots/dashboard-timeline.webp',
        alt: 'Timeline de eventos en el dashboard de Alfred Dev',
        caption: 'Timeline de eventos',
      },
      {
        src: '/screenshots/dashboard-decisiones.webp',
        alt: 'Decisiones técnicas en el dashboard de Alfred Dev',
        caption: 'Decisiones técnicas',
      },
      {
        src: '/screenshots/dashboard-agentes.webp',
        alt: 'Control de agentes en el dashboard de Alfred Dev',
        caption: 'Control de agentes',
      },
      {
        src: '/screenshots/dashboard-memoria.webp',
        alt: 'Explorador de memoria en el dashboard de Alfred Dev',
        caption: 'Explorador de memoria',
      },
      {
        src: '/screenshots/dashboard-commits.webp',
        alt: 'Historial de commits en el dashboard de Alfred Dev',
        caption: 'Historial de commits',
      },
      {
        src: '/screenshots/dashboard-marcados.webp',
        alt: 'Elementos marcados en el dashboard de Alfred Dev',
        caption: 'Elementos marcados',
      },
    ],
    features: [
      {
        title: '7 vistas',
        description: 'Estado, timeline, decisiones, agentes, memoria, commits y marcados.',
      },
      {
        title: 'Tiempo real',
        description: 'WebSocket con reconexión automática y backoff exponencial.',
      },
      {
        title: 'Sin dependencias',
        description: 'HTML + JS vanilla, servidor Python asyncio, sin frameworks externos.',
      },
      {
        title: 'Fail-open',
        description: 'Si la GUI falla, Alfred funciona exactamente igual que sin ella.',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Flujos de trabajo
  // ----------------------------------------------------------------

  workflows: {
    header: {
      label: 'Flujos de trabajo',
      title: '5 flujos, 16 fases',
      description: 'Cada flujo tiene fases secuenciales con quality gates entre ellas. Si una gate no se supera, el flujo no avanza. Los agentes opcionales se integran automáticamente en las fases que les corresponden.',
    },
    flows: [
      {
        command: '/alfred feature',
        subtitle: 'Ciclo completo o parcial',
        description: '6 fases: producto, arquitectura, desarrollo TDD, calidad + seguridad, documentación, entrega. Puedes arrancar desde cualquier fase.',
        stages: ['Producto', 'Arquitectura', 'Desarrollo', 'Calidad + Seguridad', 'Documentación', 'Entrega'],
      },
      {
        command: '/alfred fix',
        subtitle: 'Corrección rápida',
        description: 'Diagnóstico de causa raíz, corrección con TDD (test que reproduce el bug primero), validación con QA + seguridad.',
        stages: ['Diagnóstico', 'Corrección TDD', 'Validación'],
      },
      {
        command: '/alfred spike',
        subtitle: 'Investigación',
        description: 'Exploración técnica sin compromiso: prototipos, benchmarks, evaluación de alternativas. Documento de hallazgos.',
        stages: ['Investigación', 'Hallazgos'],
      },
      {
        command: '/alfred ship',
        subtitle: 'Despliegue',
        description: 'Auditoría final paralela, documentación de release, empaquetado con versionado semántico, despliegue a producción.',
        stages: ['Auditoría', 'Documentación', 'Empaquetado', 'Despliegue'],
      },
      {
        command: '/alfred audit',
        subtitle: 'Auditoría',
        description: '4 agentes en paralelo: calidad, seguridad, arquitectura y documentación. Informe consolidado con prioridades.',
        stages: ['Auditoría paralela'],
      },
    ],
  },

  // ----------------------------------------------------------------
  // Quality gates
  // ----------------------------------------------------------------

  gates: {
    header: {
      label: 'Quality gates',
      title: 'Hacia dónde trabaja Alfred',
      description: 'Alfred no da garantías absolutas, pero trabaja activamente para que estos objetivos se cumplan en cada flujo. Si detecta que algo no cuadra, detiene el avance y te avisa.',
    },
    coreLabel: 'Núcleo -- siempre activos',
    core: [
      { text: 'Intenta que los tests estén en verde antes de avanzar a calidad' },
      { text: 'Pasa revisión de QA y seguridad antes de proponer el despliegue' },
      { text: 'Busca que el pipeline CI/CD esté verde como requisito de entrega' },
      { text: 'Pide aprobación del PRD al usuario antes de diseñar' },
      { text: 'El security officer revisa el diseño antes de pasar a desarrollo' },
      { text: 'Revisa vulnerabilidades OWASP y alerta si encuentra críticas o altas' },
      { text: 'Audita dependencias en busca de CVEs conocidos' },
      { text: 'Comprueba aspectos de compliance RGPD, NIS2 y CRA según el contexto' },
      { text: 'Vigila cada escritura de fichero buscando secretos, API keys o tokens' },
      { text: 'Detecta tildes omitidas en castellano al escribir o editar ficheros' },
    ],
    optionalLabel: 'Opcionales -- cuando los activas',
    optional: [
      { text: 'Analiza el código con SonarQube (instala Docker si falta, con tu permiso)', optional: true },
      { text: 'Exige rollback en cada migración de base de datos antes de ejecutarla', optional: true },
      { text: 'Verifica accesibilidad WCAG 2.1 AA antes de dar por buena la interfaz', optional: true },
      { text: 'Mide rendimiento con métricas reales (p50, p95, p99) antes y después', optional: true },
      { text: 'Configura branch protection en main y exige PR con aprobación', optional: true },
      { text: 'Monitoriza Core Web Vitals (LCP, INP, CLS) y alerta si están fuera de umbral', optional: true },
      { text: 'Revisa meta tags, structured data y rastreabilidad SEO antes de publicar', optional: true },
      { text: 'Valida ortografía, tono y consistencia de los textos de la interfaz', optional: true },
    ],
  },

  // ----------------------------------------------------------------
  // Skills
  // ----------------------------------------------------------------

  skills: {
    header: {
      label: 'Capacidades',
      title: '59 skills en 13 dominios',
      description: 'Cada skill es una habilidad concreta que los agentes ejecutan. Los 7 dominios originales se amplían con 6 nuevos para los agentes opcionales.',
    },
    domains: [
      {
        name: 'Producto',
        skills: [
          { name: 'write-prd', description: 'PRD completo con historias y criterios' },
          { name: 'user-stories', description: 'Descomposición en historias de usuario' },
          { name: 'acceptance-criteria', description: 'Criterios Given/When/Then' },
          { name: 'competitive-analysis', description: 'Análisis de alternativas' },
        ],
      },
      {
        name: 'Arquitectura',
        skills: [
          { name: 'write-adr', description: 'Architecture Decision Records' },
          { name: 'choose-stack', description: 'Matriz de decisión de stack' },
          { name: 'design-system', description: 'Diseño con diagramas Mermaid' },
          { name: 'evaluate-dependencies', description: 'Auditoría de dependencias' },
        ],
      },
      {
        name: 'Desarrollo',
        skills: [
          { name: 'tdd-cycle', description: 'Ciclo rojo-verde-refactor' },
          { name: 'explore-codebase', description: 'Exploración de código' },
          { name: 'refactor', description: 'Refactoring guiado' },
          { name: 'code-review-response', description: 'Respuesta a code reviews' },
        ],
      },
      {
        name: 'Seguridad',
        skills: [
          { name: 'threat-model', description: 'Modelado STRIDE' },
          { name: 'dependency-audit', description: 'CVEs, licencias, versiones' },
          { name: 'security-review', description: 'OWASP Top 10' },
          { name: 'compliance-check', description: 'RGPD, NIS2, CRA' },
          { name: 'sbom-generate', description: 'Software Bill of Materials' },
          { name: 'dependency-update', description: 'Actualización segura de dependencias' },
        ],
      },
      {
        name: 'Calidad',
        skills: [
          { name: 'test-plan', description: 'Test plans por riesgo' },
          { name: 'code-review', description: 'Review de calidad' },
          { name: 'exploratory-test', description: 'Testing exploratorio' },
          { name: 'regression-check', description: 'Análisis de regresión' },
          { name: 'sonarqube', description: 'Análisis con SonarQube + Docker' },
          { name: 'spelling-check', description: 'Verificación ortográfica (tildes)' },
        ],
      },
      {
        name: 'DevOps',
        skills: [
          { name: 'dockerize', description: 'Dockerfile multi-stage' },
          { name: 'ci-cd-pipeline', description: 'GitHub Actions, GitLab CI' },
          { name: 'deploy-config', description: 'Vercel, Railway, Fly, AWS, K8s' },
          { name: 'monitoring-setup', description: 'Logging, alertas, tracking' },
        ],
      },
      {
        name: 'Documentación',
        skills: [
          { name: 'api-docs', description: 'Endpoints, params, ejemplos' },
          { name: 'architecture-docs', description: 'Visión global del sistema' },
          { name: 'user-guide', description: 'Instalación, uso, troubleshooting' },
          { name: 'changelog', description: 'Keep a Changelog' },
          { name: 'project-docs', description: 'Documentación completa en docs/' },
          { name: 'glossary', description: 'Corpus lingüístico del proyecto' },
          { name: 'readme-review', description: 'Auditoría del README' },
          { name: 'onboarding-guide', description: 'Guía para nuevos developers' },
          { name: 'migration-guide', description: 'Migración entre versiones' },
        ],
      },
      {
        name: 'Datos',
        optional: true,
        skills: [
          { name: 'schema-design', description: 'Diseño de esquemas normalizados' },
          { name: 'migration-plan', description: 'Migraciones con rollback' },
          { name: 'query-optimization', description: 'Optimización con EXPLAIN' },
        ],
      },
      {
        name: 'UX',
        optional: true,
        skills: [
          { name: 'accessibility-audit', description: 'WCAG 2.1 AA completo' },
          { name: 'usability-heuristics', description: '10 heurísticas de Nielsen' },
          { name: 'flow-review', description: 'Análisis de flujos de usuario' },
        ],
      },
      {
        name: 'Rendimiento',
        optional: true,
        skills: [
          { name: 'profiling', description: 'CPU y memoria por runtime' },
          { name: 'benchmark', description: 'Benchmarks con p50, p95, p99' },
          { name: 'bundle-size', description: 'Análisis y reducción de bundles' },
        ],
      },
      {
        name: 'GitHub',
        optional: true,
        skills: [
          { name: 'repo-setup', description: 'Configuración completa de repo' },
          { name: 'pr-workflow', description: 'PRs bien documentadas' },
          { name: 'release', description: 'Releases con versionado semántico' },
          { name: 'issue-templates', description: 'Plantillas de issues YAML' },
        ],
      },
      {
        name: 'SEO',
        optional: true,
        skills: [
          { name: 'meta-tags', description: 'Title, description, Open Graph' },
          { name: 'structured-data', description: 'JSON-LD para schema.org' },
          { name: 'lighthouse-audit', description: 'Core Web Vitals y métricas' },
        ],
      },
      {
        name: 'Marketing',
        optional: true,
        skills: [
          { name: 'copy-review', description: 'Revisión de textos públicos' },
          { name: 'cta-writing', description: 'CTAs efectivos sin teletienda' },
          { name: 'tone-guide', description: 'Guía de tono de marca' },
        ],
      },
    ],
  },

  // ----------------------------------------------------------------
  // Infraestructura
  // ----------------------------------------------------------------

  infra: {
    header: {
      label: 'Bajo el capó',
      title: 'Hooks, templates y core',
      description: 'La infraestructura que hace funcionar al equipo: hooks que vigilan, templates que estandarizan y un core que orquesta.',
    },
    groups: [
      {
        title: '11 hooks',
        items: [
          { name: 'session-start.sh', label: 'SessionStart' },
          { name: 'stop-hook.py', label: 'Stop' },
          { name: 'secret-guard.sh', label: 'PreToolUse' },
          { name: 'dangerous-command-guard.py', label: 'PreToolUse' },
          { name: 'sensitive-read-guard.py', label: 'PreToolUse' },
          { name: 'quality-gate.py', label: 'PostToolUse' },
          { name: 'dependency-watch.py', label: 'PostToolUse' },
          { name: 'spelling-guard.py', label: 'PostToolUse' },
          { name: 'memory-capture.py', label: 'PostToolUse' },
          { name: 'commit-capture.py', label: 'PostToolUse' },
          { name: 'memory-compact.py', label: 'PreCompact' },
        ],
      },
      {
        title: '7 templates',
        items: [
          { name: 'prd.md', label: 'Product Requirements' },
          { name: 'adr.md', label: 'Architecture Decision' },
          { name: 'test-plan.md', label: 'Plan de testing' },
          { name: 'threat-model.md', label: 'Modelado STRIDE' },
          { name: 'sbom.md', label: 'Bill of Materials' },
          { name: 'changelog-entry.md', label: 'Entrada de changelog' },
          { name: 'release-notes.md', label: 'Notas de release' },
        ],
      },
      {
        title: '4 módulos core',
        items: [
          { name: 'orchestrator.py', label: 'Flujos, sesiones, gates' },
          { name: 'personality.py', label: 'Motor de personalidad' },
          { name: 'config_loader.py', label: 'Config y detección de stack' },
          { name: 'memory.py', label: 'Memoria persistente SQLite' },
        ],
        footnote: '114 passing',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Comandos
  // ----------------------------------------------------------------

  commands: {
    header: {
      label: 'Interfaz',
      title: '11 comandos',
      description: 'Todo se controla desde la línea de comandos de Claude Code. Un prefijo, un verbo, una descripción.',
    },
    list: [
      {
        command: '/alfred',
        description: 'Asistente contextual: detecta el stack y la sesión activa, pregunta qué necesitas y lanza el flujo adecuado.',
      },
      {
        command: '/alfred feature',
        description: 'Ciclo completo de 6 fases o desde la que indiques. Alfred pregunta y se adapta: "desde desarrollo", "solo documentación", "ciclo completo".',
      },
      {
        command: '/alfred fix',
        description: 'Corregir un bug con flujo de 3 fases: diagnóstico, corrección TDD, validación.',
      },
      {
        command: '/alfred spike',
        description: 'Investigación exploratoria sin compromiso: prototipos, benchmarks, conclusiones.',
      },
      {
        command: '/alfred ship',
        description: 'Preparar release: auditoría final, documentación, empaquetado, despliegue.',
      },
      {
        command: '/alfred audit',
        description: 'Auditoría completa con 4 agentes en paralelo: calidad, seguridad, arquitectura, documentación.',
      },
      {
        command: '/alfred config',
        description: 'Configurar autonomía, stack, compliance, personalidad, <strong style="color: var(--gold);">agentes opcionales</strong> y <strong style="color: var(--gold);">memoria persistente</strong>. Incluye descubrimiento contextual: Alfred analiza tu proyecto y sugiere qué agentes activar.',
      },
      {
        command: '/alfred status',
        description: 'Sesión activa: fase actual, fases completadas con duración, gate pendiente y agente activo.',
      },
      {
        command: '/alfred update',
        description: 'Comprobar si hay versión nueva, ver las notas de release y actualizar con un clic.',
      },
      {
        command: '/alfred help',
        description: 'Ayuda completa de todos los comandos disponibles.',
      },
    ],
    optionalNote: '<strong style="color: var(--gold);">Agentes opcionales en los flujos:</strong> los 7 agentes opcionales no tienen comandos propios. Se activan con <strong style="color: var(--blue);">/alfred config</strong> y a partir de ahí se integran automáticamente en los flujos existentes. Por ejemplo, si activas el <em>data-engineer</em>, participará en la fase de arquitectura de <strong style="color: var(--blue);">/alfred feature</strong>; si activas el <em>seo-specialist</em>, intervendrá en la fase de calidad de <strong style="color: var(--blue);">/alfred ship</strong>; si activas <em>El Bibliotecario</em>, Alfred consultará el historial de decisiones antes de cada flujo. Alfred decide cuándo invocar a cada agente según el contexto del flujo.',
  },

  // ----------------------------------------------------------------
  // Deteccion de stack
  // ----------------------------------------------------------------

  stacks: {
    header: {
      label: 'Detección automática',
      title: 'Se adapta a tu proyecto',
      description: 'Alfred Dev detecta automáticamente el stack tecnológico de tu proyecto y adapta sus artefactos al ecosistema real.',
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

  // ----------------------------------------------------------------
  // Casos de uso
  // ----------------------------------------------------------------

  useCases: {
    header: {
      label: 'En la práctica',
      labelColor: 'var(--cyan)',
      title: 'Cómo se usa',
      description: 'Escenarios reales de uso paso a paso. Cada caso muestra el flujo completo desde la invocación hasta el resultado.',
    },
    cases: [
      {
        category: 'Desarrollo',
        color: 'var(--blue)',
        background: 'rgba(91,156,245,0.08)',
        title: 'Desarrollar una feature completa',
        command: '/alfred feature sistema de notificaciones push',
        steps: [
          'El product-owner genera el PRD con historias de usuario y criterios de aceptación',
          'El architect diseña la solución y el security-officer valida el diseño',
          'El senior-dev implementa siguiendo TDD estricto (rojo-verde-refactor)',
          'QA y seguridad auditan en paralelo antes de dar el visto bueno',
          'El tech-writer documenta la API y el devops-engineer prepara el despliegue',
        ],
      },
      {
        category: 'Corrección',
        color: 'var(--red)',
        background: 'rgba(229,86,79,0.08)',
        title: 'Corregir un bug',
        command: '/alfred fix el login falla con emails que tienen tildes',
        steps: [
          'El senior-dev reproduce el error e identifica la causa raíz',
          'Escribe un test que falla reproduciendo el bug exacto',
          'Implementa la corrección mínima que hace pasar el test',
          'QA y seguridad validan que no se hayan introducido regresiones',
        ],
      },
      {
        category: 'Investigación',
        color: 'var(--purple)',
        background: 'rgba(160,126,232,0.08)',
        title: 'Investigación técnica (spike)',
        command: '/alfred spike evaluar si migrar de REST a gRPC',
        steps: [
          'El architect y el senior-dev exploran las alternativas sin compromiso de código',
          'Se generan pruebas de concepto ligeras para comparar rendimiento',
          'Se documenta un ADR con los hallazgos, pros, contras y recomendación',
          'El usuario decide si proceder a implementación o descartarlo',
        ],
      },
      {
        category: 'Auditoría',
        color: 'var(--orange)',
        background: 'rgba(232,164,74,0.08)',
        title: 'Auditar el proyecto',
        command: '/alfred audit',
        steps: [
          '4 agentes trabajan en paralelo: QA, seguridad, arquitectura y documentación',
          'QA busca errores lógicos, code smells y cobertura de tests',
          'Seguridad analiza OWASP Top 10, dependencias con CVEs y compliance RGPD/NIS2',
          'Se consolida un informe único con hallazgos priorizados por severidad',
        ],
      },
      {
        category: 'Entrega',
        color: 'var(--green)',
        background: 'rgba(78,201,144,0.08)',
        title: 'Preparar una entrega',
        command: '/alfred ship',
        steps: [
          'Auditoría final obligatoria: QA y seguridad deben aprobar',
          'El tech-writer actualiza el changelog y genera las notas de release',
          'El devops-engineer empaqueta, configura el pipeline y verifica el build',
          'Despliegue supervisado: el usuario confirma antes de subir a producción',
        ],
      },
      {
        category: 'Conversacional',
        color: 'var(--gold)',
        background: 'rgba(201,169,110,0.08)',
        title: 'Asistente contextual',
        command: '/alfred',
        steps: [
          'Alfred detecta el stack del proyecto y el estado de la sesión activa',
          'Pregunta qué necesitas y ofrece opciones adaptadas al contexto',
          'Interpreta tu respuesta en lenguaje natural y lanza el flujo adecuado',
          'También puedes decir "usa el plugin de Alfred" en cualquier momento',
        ],
      },
      {
        category: 'Calidad',
        color: 'var(--red)',
        background: 'rgba(229,86,79,0.08)',
        title: 'Análisis con SonarQube',
        command: '/alfred audit',
        steps: [
          'El QA comprueba si Docker está instalado; si no, lo instala él mismo (con tu permiso)',
          'Levanta SonarQube con Docker automáticamente y espera a que esté listo',
          'Configura el proyecto, ejecuta el scanner y espera los resultados',
          'Traduce los hallazgos (bugs, vulnerabilidades, code smells) en un informe con correcciones propuestas',
          'Limpia el contenedor al terminar: no deja nada corriendo',
        ],
      },
      {
        category: 'Datos',
        color: 'var(--orange)',
        background: 'rgba(232,164,74,0.08)',
        title: 'Diseñar y migrar una base de datos',
        command: '/alfred feature añadir sistema de suscripciones con pagos',
        steps: [
          'El data-engineer diseña el esquema normalizado con constraints e índices',
          'Genera el script de migración con rollback obligatorio (ida y vuelta)',
          'El architect valida la integración con el ORM y el resto del stack',
          'Se ejecuta la migración, se verifican las tablas y se pasan los tests de integración',
        ],
      },
      {
        category: 'GitHub',
        color: 'var(--text-muted)',
        background: 'rgba(110,115,138,0.08)',
        title: 'Configurar y publicar un repositorio',
        command: '/alfred ship',
        steps: [
          'El github-manager verifica que gh CLI está instalado y autenticado; si no, guía el proceso',
          'Configura branch protection, labels, issue templates y .gitignore optimizado',
          'Crea la PR con descripción estructurada, labels y asignación de reviewers',
          'Genera la release con versionado semántico, changelog categorizado y artefactos adjuntos',
        ],
      },
      {
        category: 'SEO + Copy',
        color: 'var(--green)',
        background: 'rgba(78,201,144,0.08)',
        title: 'Optimizar una landing page',
        command: '/alfred audit',
        steps: [
          'El seo-specialist audita meta tags, Open Graph, canonical y datos estructurados JSON-LD',
          'Ejecuta Lighthouse y prioriza las mejoras por impacto en Core Web Vitals',
          'El copywriter revisa los textos: ortografía (tildes primero), claridad, tono y CTAs',
          'Se genera un informe conjunto con correcciones listas para aplicar',
        ],
      },
      {
        category: 'UX',
        color: '#ff69b4',
        background: 'rgba(255,105,180,0.08)',
        title: 'Auditoría de accesibilidad y usabilidad',
        command: '/alfred audit',
        steps: [
          'El ux-reviewer ejecuta una auditoría WCAG 2.1 AA por los 4 principios (perceptible, operable, comprensible, robusto)',
          'Aplica las 10 heurísticas de Nielsen al flujo principal del usuario',
          'Identifica puntos de fricción, edge cases y pasos innecesarios en cada flujo',
          'Genera un informe con severidad (0-4) y propuesta de mejora para cada hallazgo',
        ],
      },
      {
        category: 'Rendimiento',
        color: 'var(--purple)',
        background: 'rgba(160,126,232,0.08)',
        title: 'Optimizar el rendimiento',
        command: '/alfred spike la API tarda 3 segundos en responder',
        steps: [
          'El performance-engineer ejecuta profiling de CPU y memoria para localizar cuellos de botella',
          'Analiza queries lentas con EXPLAIN y propone índices o reestructuración',
          'Ejecuta benchmarks antes y después con métricas reales (p50, p95, p99)',
          'Si hay frontend, analiza el bundle size y propone tree-shaking o code splitting',
        ],
      },
      {
        category: 'Automático',
        color: 'var(--cyan)',
        background: 'rgba(78,201,201,0.08)',
        title: 'Protección en segundo plano',
        wide: true,
        description: 'Sin necesidad de ejecutar ningún comando, Alfred vigila automáticamente tu sesión de trabajo mediante hooks que se activan en cada operación relevante.',
        steps: [
          'Guardia de secretos -- bloquea la escritura de API keys, tokens o contraseñas en el código',
          'Quality gate -- verifica que los tests pasen después de cada cambio significativo',
          'Vigilancia de dependencias -- detecta nuevas librerías y notifica al auditor de seguridad',
          'Guardia ortográfico -- detecta palabras castellanas sin tilde al escribir o editar ficheros',
          'Captura de memoria -- registra automáticamente eventos del flujo de trabajo en la memoria persistente',
          'Captura de commits -- detecta cada git commit y registra SHA, autor y ficheros en la memoria',
          'Contexto protegido -- las decisiones críticas sobreviven a la compactación de contexto',
        ],
      },
    ],
  },

  // ----------------------------------------------------------------
  // Memoria persistente
  // ----------------------------------------------------------------

  memory: {
    sectionLabel: 'Desde v0.2.0 · Mejorada en v0.2.3',
    title: 'Memoria persistente',
    descriptionHtml: 'Alfred Dev recuerda decisiones, commits e iteraciones entre sesiones. La memoria se almacena en una base de datos SQLite local dentro de cada proyecto, sin dependencias externas ni servicios remotos. Desde v0.2.3: etiquetas, estado y relaciones entre decisiones, auto-captura de commits, filtros avanzados y export/import.',
    traceability: {
      title: 'Trazabilidad completa',
      descriptionHtml: 'Cada decisión queda enlazada con el problema que la originó, los commits que la implementaron y la validación que la confirmó. Todo referenciable con IDs verificables.',
      nodes: [
        { label: 'Problema', color: 'var(--purple)', background: 'rgba(160,126,232,0.08)', borderColor: 'rgba(160,126,232,0.15)' },
        { label: 'Decisión [D#id]', color: 'var(--gold)', background: 'rgba(201,169,110,0.08)', borderColor: 'rgba(201,169,110,0.15)' },
        { label: 'Commit [C#sha]', color: 'var(--green)', background: 'rgba(78,201,144,0.08)', borderColor: 'rgba(78,201,144,0.15)' },
        { label: 'Validación', color: 'var(--blue)', background: 'rgba(91,156,245,0.08)', borderColor: 'rgba(91,156,245,0.15)' },
      ],
    },
    cards: [
      {
        title: 'Base de datos local',
        descriptionHtml: 'SQLite con modo WAL para escrituras concurrentes. Almacena decisiones, commits, iteraciones y eventos en <code>.claude/alfred-memory.db</code> dentro de cada proyecto. Permisos 0600 por defecto.',
      },
      {
        title: 'Búsqueda inteligente',
        descriptionHtml: 'Texto completo con FTS5 cuando está disponible, con fallback automático a LIKE para entornos sin extensión FTS. Busca en títulos de decisiones, razones, alternativas descartadas y mensajes de commit.',
      },
      {
        title: 'Captura automática',
        descriptionHtml: 'Dos hooks complementarios capturan todo automáticamente: <code>memory-capture.py</code> registra eventos del flujo (iteraciones, fases) y <code>commit-capture.py</code> detecta cada <code>git commit</code> y registra SHA, mensaje, autor y ficheros afectados.',
      },
      {
        title: 'Servidor MCP integrado',
        descriptionHtml: '15 herramientas accesibles desde cualquier agente vía MCP stdio: buscar, registrar, consultar iteraciones, estadísticas, gestión de iteraciones, ciclo de vida de decisiones, validación de integridad, export/import. Sin dependencias externas.',
      },
      {
        title: 'Contexto de sesión',
        descriptionHtml: 'Al iniciar cada sesión, se inyectan las decisiones relevantes: si hay iteración activa, las de esa iteración; si no, las 5 últimas globales. Un hook PreCompact protege estas decisiones durante la compactación de contexto.',
      },
      {
        title: 'Seguridad integrada',
        descriptionHtml: 'Sanitización de secretos con los mismos patrones que secret-guard.sh: API keys, tokens, JWT, cadenas de conexión y claves privadas se redactan antes de almacenarse. Permisos 0600 en el fichero de base de datos.',
      },
    ],
    librarian: {
      title: 'El Bibliotecario',
      subtitle: 'Agente opcional -- memoria del proyecto',
      descriptionHtml: [
        'El Bibliotecario es el agente que responde consultas históricas sobre el proyecto. A diferencia de otros agentes que trabajan sobre el código actual, este se centra en el <em>por qué</em> de las decisiones pasadas: qué se decidió, cuándo, qué alternativas se descartaron y qué commits implementaron cada decisión. Desde v0.2.3 también gestiona el ciclo de vida de las decisiones (estado, etiquetas, relaciones), valida la integridad de la memoria y permite exportar decisiones a Markdown o importar desde Git y ADRs.',
        'Tiene una regla infranqueable: <strong>siempre cita las fuentes</strong>. Cada afirmación incluye referencias verificables con formato <code>[D#42]</code> para decisiones, <code>[C#a1b2c3d]</code> para commits y <code>[I#7]</code> para iteraciones. Si no encuentra evidencia, lo dice en lugar de inventar.',
      ],
      example: {
        label: 'Ejemplo de consulta:',
        question: '> Por qué usamos SQLite en lugar de PostgreSQL para la memoria?',
        answerHtml: 'Se eligió SQLite porque el requisito era cero dependencias externas <span style="color: var(--gold);">[D#12]</span>. La alternativa de PostgreSQL se descartó por requerir un servicio externo corriendo <span style="color: var(--gold);">[D#12, alternativas]</span>. La implementación se hizo en el commit <span style="color: var(--green);">[C#1833e83]</span> dentro de la iteración <span style="color: var(--blue);">[I#3]</span>.',
      },
      activationHtml: '<strong>Activación:</strong> se habilita desde <strong style="color: var(--blue);">/alfred config</strong> en la sección de memoria persistente. Una vez activo, Alfred le delega automáticamente las consultas históricas que surjan durante cualquier flujo.',
    },
    faq: [
      {
        question: 'Dónde se almacenan los datos?',
        answerHtml: 'En el fichero <code>.claude/alfred-memory.db</code> dentro de la raíz de cada proyecto. Es un fichero SQLite local, no se envía nada a servicios externos. Añádelo a <code>.gitignore</code> si no quieres versionarlo.',
      },
      {
        question: 'La memoria se activa sola?',
        answerHtml: 'No. La activación es explícitamente opcional. Se habilita desde <strong>/alfred config</strong> en la sección de memoria. Si no la activas, no se crea la base de datos ni se captura nada.',
      },
      {
        question: 'Qué pasa con los secretos?',
        answerHtml: 'Todo el contenido pasa por la misma sanitización que usa el hook secret-guard.sh antes de almacenarse. Claves de API, tokens, JWT, cadenas de conexión y cabeceras de clave privada se redactan automáticamente. El fichero de base de datos tiene permisos 0600 (solo lectura/escritura para el propietario).',
      },
      {
        question: 'Puedo borrar la memoria?',
        answerHtml: 'Sí. Basta con eliminar el fichero <code>.claude/alfred-memory.db</code>. También puedes desactivar la memoria desde <strong>/alfred config</strong>: los datos existentes se conservan pero dejan de consultarse y no se capturan nuevos eventos.',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Instalacion
  // ----------------------------------------------------------------

  install: {
    sectionLabel: 'Primeros pasos',
    title: 'Instalación',
    description: 'Un comando en la terminal y listo. Compatible con macOS, Linux y Windows. El instalador es idempotente: ejecutarlo de nuevo actualiza sin conflictos.',
    tabs: [
      {
        id: 'macos',
        label: 'macOS',
        command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash',
        requirementsHtml: '<strong>Requisitos:</strong> git, Python 3.10+, Claude Code instalado.<br>Tras la instalación, reinicia Claude Code y ejecuta <strong>/alfred help</strong>.',
      },
      {
        id: 'linux',
        label: 'Linux',
        command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash',
        requirementsHtml: '<strong>Requisitos:</strong> git, Python 3.10+, Claude Code instalado.<br>Tras la instalación, reinicia Claude Code y ejecuta <strong>/alfred help</strong>.',
      },
      {
        id: 'windows',
        label: 'Windows',
        command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex',
        requirementsHtml: '<strong>Requisitos:</strong> git, PowerShell 5.1+ (preinstalado en Windows 10/11), Claude Code instalado.<br>No necesita Python. Tras la instalación, reinicia Claude Code y ejecuta <strong>/alfred help</strong>.<br>Alternativa: también puedes usar el instalador bash con WSL o Git Bash.',
      },
    ],
    uninstall: {
      title: 'Desinstalación',
      description: 'Para eliminar Alfred Dev completamente, ejecuta el desinstalador de tu plataforma. Limpia todos los registros y directorios del plugin.',
      cards: [
        {
          title: 'macOS / Linux',
          command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash',
          ariaLabel: 'Copiar comando de desinstalación para macOS y Linux',
        },
        {
          title: 'Windows (PowerShell)',
          command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.ps1 | iex',
          ariaLabel: 'Copiar comando de desinstalación para Windows',
        },
      ],
    },
    update: {
      title: 'Actualización',
      descriptionHtml: 'Desde Claude Code, ejecuta <strong style="color: var(--blue);">/alfred update</strong> para comprobar si hay una versión nueva. Si la hay, Alfred te muestra las notas de la release y te pregunta si quieres actualizar. También puedes volver a ejecutar el instalador: es idempotente.',
    },
  },

  // ----------------------------------------------------------------
  // Configuracion
  // ----------------------------------------------------------------

  config: {
    sectionLabel: 'Personalización',
    title: 'Configuración por proyecto',
    descriptionHtml: 'Cada proyecto tiene su propio fichero de configuración en <code>.claude/alfred-dev.local.md</code>. Se gestiona con <strong>/alfred config</strong>, que incluye descubrimiento contextual de agentes opcionales y activación de memoria persistente.',
    yamlExample: `---
autonomia:
  producto: interactivo
  arquitectura: interactivo
  desarrollo: semi-autonomo
  seguridad: autonomo
  calidad: semi-autonomo
  documentacion: autonomo
  devops: semi-autonomo

agentes_opcionales:
  data-engineer: true
  ux-reviewer: false
  github-manager: true
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
---`,
    blocks: [
      {
        title: 'Autonomía por fase',
        descriptionHtml: 'Controla cuánta intervención necesitas en cada fase del flujo. <strong>Interactivo</strong> pide aprobación en cada paso, <strong>semi-autónomo</strong> avanza solo pero te consulta las decisiones clave, y <strong>autónomo</strong> ejecuta sin interrupciones.',
      },
      {
        title: 'Agentes opcionales',
        descriptionHtml: 'Activa solo los que necesites. Alfred analiza tu proyecto y te sugiere cuáles habilitar según el stack detectado. Se pueden cambiar en cualquier momento sin reinstalar.',
      },
      {
        title: 'Memoria persistente',
        descriptionHtml: 'Activación opcional. Configura qué se captura (decisiones, commits), la retención en días y el comportamiento del Bibliotecario.',
      },
      {
        title: 'Personalidad',
        descriptionHtml: 'El nivel de sarcasmo va de 0 (profesional formal) a 5 (ácido con cariño). Las celebraciones y los avisos por malas prácticas se activan por separado.',
      },
    ],
  },

  // ----------------------------------------------------------------
  // FAQ
  // ----------------------------------------------------------------

  faq: {
    header: {
      label: 'Preguntas frecuentes',
      title: 'FAQ',
    },
    items: [
      {
        svgContent: '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
        question: 'Funciona en Windows?',
        answerHtml: 'Sí. Alfred Dev tiene un instalador nativo en PowerShell para Windows 10/11. También puedes usar el instalador bash a través de WSL (Windows Subsystem for Linux) o Git Bash. La única dependencia en Windows es git; no necesita python3.',
      },
      {
        svgContent: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
        question: 'Qué dependencias necesita?',
        answerHtml: 'En macOS y Linux: <strong>git</strong> y <strong>python3</strong>. Ambas suelen estar preinstaladas o son fáciles de instalar con el gestor de paquetes del sistema.<br><br>En Windows: solo <strong>git</strong>. PowerShell maneja el JSON de forma nativa, así que python3 no es necesario. PowerShell 5.1+ viene preinstalado en Windows 10/11.',
      },
      {
        svgContent: '<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
        question: 'Cómo actualizo el plugin?',
        answerHtml: 'Ejecuta <strong>/alfred update</strong> dentro de Claude Code. El comando consulta GitHub, compara versiones y te muestra las notas de la release si hay versión nueva. También puedes volver a ejecutar el instalador: sobreescribe la versión anterior sin conflictos.',
      },
      {
        svgContent: '<path d="M19.439 5.56a5.018 5.018 0 0 0-7.09 0L11 6.91l-1.35-1.35a5.013 5.013 0 0 0-7.09 7.09L11 21.09l8.44-8.44a5.013 5.013 0 0 0 0-7.09z"/>',
        question: 'Es compatible con otros plugins de Claude Code?',
        answerHtml: 'Sí. Alfred Dev convive sin conflictos con otros plugins instalados. Usa su propio namespace (<code>alfred-dev</code>) y no interfiere con la configuración de otros plugins.',
      },
      {
        svgContent: '<circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6M4.22 4.22l4.24 4.24m7.08 7.08l4.24 4.24M1 12h6m6 0h6M4.22 19.78l4.24-4.24m7.08-7.08l4.24-4.24"/>',
        question: 'Qué son los agentes opcionales?',
        answerHtml: 'Son 7 agentes especializados que puedes activar según las necesidades de tu proyecto: <strong>data-engineer</strong> (bases de datos), <strong>ux-reviewer</strong> (accesibilidad y usabilidad), <strong>performance-engineer</strong> (rendimiento), <strong>github-manager</strong> (gestión de repositorios), <strong>seo-specialist</strong> (posicionamiento web), <strong>copywriter</strong> (textos y ortografía) y <strong>El Bibliotecario</strong> (memoria persistente: consultas históricas sobre decisiones, commits e iteraciones del proyecto).<br><br>Alfred analiza tu proyecto y te sugiere cuáles activar. También puedes gestionarlos manualmente con <strong>/alfred config</strong>. Se activan o desactivan sin reinstalar nada.',
      },
      {
        svgContent: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
        question: 'Cuántos skills tiene en total?',
        answerHtml: '59 skills distribuidos en 13 dominios. Los 7 dominios originales (producto, arquitectura, desarrollo, seguridad, calidad, DevOps, documentación) cubren el ciclo de vida estándar. Los 6 nuevos (datos, UX, rendimiento, GitHub, SEO, marketing) corresponden a los agentes opcionales. Los dominios existentes también se han ampliado: documentación pasó de 4 a 9 skills, seguridad de 5 a 6, y calidad de 4 a 6.',
      },
      {
        svgContent: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
        question: 'Qué es la memoria persistente?',
        answerHtml: 'Es una base de datos SQLite local que almacena las decisiones, commits e iteraciones de cada proyecto. Se activa opcionalmente desde <strong>/alfred config</strong>. Una vez activa, Alfred registra automáticamente los eventos del flujo de trabajo y el agente <strong>El Bibliotecario</strong> puede responder consultas históricas como "por qué se eligió esta arquitectura" o "qué se hizo en la última iteración", citando siempre las fuentes. Los datos no salen del proyecto: todo queda en <code>.claude/alfred-memory.db</code>.',
      },
      {
        svgContent: '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
        question: 'Cuánto cuesta?',
        answerHtml: 'Nada. Alfred Dev es software libre bajo licencia MIT. Puedes usarlo, modificarlo y distribuirlo sin restricciones. El código fuente está en GitHub (github.com/686f6c61/alfred-dev).',
      },
      {
        svgContent: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        question: 'En qué idioma responde Alfred?',
        answerHtml: 'Castellano de España por defecto: tanto las respuestas como los comentarios de código, commits y documentación generada. Puedes ajustar este comportamiento con <strong>/alfred config</strong>.',
      },
      {
        svgContent: '<polyline points="20 6 9 17 4 12"/>',
        question: 'Qué versiones de Claude Code soporta?',
        answerHtml: 'Cualquier versión de Claude Code que soporte el sistema de plugins. Si puedes instalar plugins desde la línea de comandos, Alfred Dev funcionará. No hay requisito de versión mínima específica.',
      },
      {
        svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        question: 'Puedo contribuir al proyecto?',
        answerHtml: 'Sí. Alfred Dev es software libre bajo licencia MIT. Puedes reportar bugs, proponer mejoras o enviar pull requests en el repositorio de GitHub (github.com/686f6c61/alfred-dev/issues). Las contribuciones de código, documentación, traducciones o simplemente reportar problemas son bienvenidas.',
      },
      {
        svgContent: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
        question: 'Los agentes consumen tokens adicionales?',
        answerHtml: 'Sí, como cualquier interacción con Claude. Los agentes son instrucciones de sistema que guían las respuestas, así que consumen contexto proporcional a su complejidad. En la práctica, el coste adicional es moderado: los system prompts de los agentes están optimizados para ocupar el mínimo posible sin perder precisión. Los agentes opcionales solo se cargan si los activas, así que el contexto base es el de los 8 de núcleo.',
      },
      {
        svgContent: '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
        question: 'Puedo usar Alfred en un monorepo?',
        answerHtml: 'Alfred detecta el stack del directorio de trabajo actual, no del repositorio raíz. Si ejecutas Claude Code desde la raíz de un monorepo, detectará todos los lenguajes presentes. Si lo ejecutas desde un paquete concreto, se centrará en ese paquete. La memoria persistente es por directorio de trabajo, así que cada paquete puede tener su propia base de datos de decisiones si lo configuras así.',
      },
      {
        svgContent: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
        question: 'Qué pasa si una quality gate falla?',
        answerHtml: 'El flujo se detiene en la fase actual y Alfred te explica qué no se cumple: tests que fallan, vulnerabilidades detectadas, documentación incompleta o lo que corresponda. Tienes tres opciones: corregir el problema y reintentar la gate, pedir a Alfred que te ayude a resolverlo (por ejemplo, con <strong>/alfred fix</strong> si es un bug), o continuar manualmente asumiendo el riesgo. Alfred nunca avanza en silencio si una gate no se supera.',
      },
      {
        svgContent: '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
        question: 'Funciona con OpenCode?',
        answerHtml: 'Está en desarrollo. OpenCode es un editor de código basado en terminal, de código abierto, que comparte la arquitectura de plugins con Claude Code. Alfred Dev está adaptándose para ser compatible con ambos entornos. La versión para OpenCode se anunciará en el repositorio cuando esté lista para uso general.',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Changelog
  // ----------------------------------------------------------------

  changelog: [
    {
      version: '0.3.2',
      date: '2026-02-23',
      added: [
        '<strong>Composición dinámica de equipo</strong> -- sistema de 4 capas (heurística, razonamiento, presentación, ejecución) que sugiere agentes opcionales según la descripción de la tarea. La selección es efímera y no modifica la configuración persistente.',
        '<strong>Función run_flow()</strong> -- punto de entrada para flujos con equipo de sesión efímero. Valida la estructura, inyecta el equipo y registra diagnósticos de error.',
        '<strong>Tabla TASK_KEYWORDS</strong> -- mapa de 7 agentes opcionales con keywords contextuales y pesos base para la composición dinámica.',
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
        '<strong>Dashboard GUI</strong> (Fase Alpha) -- dashboard web en tiempo real con 7 vistas: estado, timeline, decisiones, agentes, memoria, commits y marcados. Se lanza con <code>/alfred gui</code>.',
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
        '<strong>Hook commit-capture.py</strong> -- auto-captura de commits en la memoria.',
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
        '<code>/alfred feature</code> permite seleccionar fase de inicio.',
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
        '<strong>memory-capture.py</strong> -- diagnóstico en bloques except silenciosos.',
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
        '<strong>Hook memory-capture.py</strong> -- captura automática de eventos del flujo.',
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
        'Detección de versión en <code>/alfred update</code> más fiable.',
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
    version: 'v0.3.2',
    license: 'MIT License',
    githubUrl: 'https://github.com/686f6c61/alfred-dev',
    docsUrl: 'https://github.com/686f6c61/alfred-dev/tree/main/docs',
    tagline: 'Plugin de Claude Code. 15 agentes. 59 skills. 11 comandos. Memoria persistente. De la idea a producción.',
    slogan: 'Ingeniería de software automatizada para Claude Code.',
  },
};

export default data;
