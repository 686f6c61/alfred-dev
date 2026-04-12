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
    description: 'Plugin de Claude Code con 19 agentes especializados, un catalogo publicado de 61 skills y memoria persistente por proyecto. TDD estricto, seguridad transversal y quality gates automáticas en cada fase.',
    canonical: 'https://alfred-dev.com/',
    locale: 'es_ES',
    og: {
      type: 'website',
      title: 'Alfred Dev - plugin de Claude Code para equipos de desarrollo',
      description: 'Un equipo de 19 agentes especializados para Claude Code. Cada rol tiene herramientas restringidas, personalidad propia y quality gates que el flujo no puede saltarse.',
      url: 'https://alfred-dev.com/',
      siteName: 'Alfred Dev',
      locale: 'es_ES',
      image: 'https://alfred-dev.com/screenshots/alfred-dev-share-es.png',
      imageWidth: 2400,
      imageHeight: 1260,
      imageType: 'image/png',
      imageAlt: 'Captura de la landing de Alfred Dev con el titular Un sistema de trabajo para Claude Code',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Alfred Dev - plugin de Claude Code para equipos de desarrollo',
      description: 'Plugin de Claude Code: 10 agentes de núcleo + 9 opcionales, memoria SQLite por proyecto, 26 comandos y quality gates automáticas en cada fase del desarrollo.',
      image: 'https://alfred-dev.com/screenshots/alfred-dev-share-es.png',
      imageAlt: 'Captura de la landing de Alfred Dev con el titular Un sistema de trabajo para Claude Code',
      site: '@686f6c61',
      creator: '@686f6c61',
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
    subtitle: '19 agentes especializados con personalidad propia. 10 de núcleo, 9 opcionales. Hasta 7 fases, 26 comandos, memoria persistente y quality gates automáticas en cada transición.',
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
    features: {
      label: 'Capacidades destacadas',
      items: [
        {
          title: 'Lucius — segunda opinión técnica',
          description: 'Cuando Alfred termina, invoca a Codex CLI para una perspectiva externa. Diagnóstico y prescripción por ítem: seguridad, arquitectura, tests o rendimiento. Sin tocar nada. Tú decides qué implementar y con quién.',
          svgContent: '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
          tag: { text: 'Nuevo', href: '#uso' },
        },
        {
          title: 'Selina — flujo guiado de dirección visual',
          description: 'Selina deja fijar sistema de diseño base, pairing tipográfico y gama cromática antes de bajar a tres propuestas comparables. La implementación arranca con una familia visual cerrada, no con intuiciones sueltas.',
          svgContent: '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>',
          tag: { text: 'Nuevo', href: '#uso' },
        },
        {
          title: 'Continuidad operativa real',
          description: 'Alfred ya sabe decir qué toca ahora, pausar una sesión, retomarla y mostrar el estado del proyecto sin reabrir medio repo.',
          svgContent: '<path d="M9 12l2 2 4-4"/><path d="M12 3c7.2 0 9 1.8 9 9s-1.8 9-9 9-9-1.8-9-9 1.8-9 9-9z"/>',
        },
        {
          title: 'Brownfield sin empezar a ciegas',
          description: 'Repos existentes arrancan por map-codebase y discuss: Alfred deja un mapa persistente del codebase antes de abrir flujos de implementación.',
          svgContent: '<path d="M12 16v5"/><path d="M16 14l-4 2-4-2"/><path d="M12 3l9 4.5v5L12 17l-9-4.5v-5L12 3z"/>',
        },
        {
          title: 'Quick mode con garantías',
          description: 'Los cambios pequeños ya tienen su propio flujo ligero: menos ceremonia, pero con tests, regresión local y revisión de seguridad.',
          svgContent: '<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
        },
        {
          title: 'UAT explícita y trazable',
          description: 'verify separa los tests automáticos de la validación humana y progress expone kanban, bloqueos, trazabilidad y estado de UAT.',
          svgContent: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
        },
        {
          title: 'SonIA usable desde CLI',
          description: 'standup, blocked, in-progress, validate y search convierten el kanban local en una interfaz diaria útil, no solo en documentación oculta.',
          svgContent: '<path d="M4 19h16"/><path d="M4 5h16"/><path d="M9 9h11"/><path d="M9 15h7"/><circle cx="6" cy="9" r="1"/><circle cx="6" cy="15" r="1"/>',
        },
        {
          title: 'GitHub como espejo opcional',
          description: 'SonIA Sync publica backlog, bloqueos y progreso en GitHub Issues con gh, sin perder la fuente de verdad local en docs/project y SQLite.',
          svgContent: '<path d="M9 19c-5 1.5-5-2.5-7-3"/><path d="M15 22v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 19 4.77 5.07 5.07 0 0 0 18.91 1S17.73.65 15 2.48a13.38 13.38 0 0 0-6 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77 5.44 5.44 0 0 0 3.5 8.53c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>',
        },
        {
          title: 'Memory UI en navegador',
          description: 'La memoria SQLite del proyecto ya se puede abrir como UI local viva: overview, timeline, decisiones, commits, búsqueda, salud y señales operativas.',
          svgContent: '<path d="M3 4h18a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z"/><path d="M8 20h8"/><path d="M12 16v4"/><path d="M6 8h5"/><path d="M6 12h10"/><path d="M16 8h2"/>',
        },
      ],
    },
  },

  // ----------------------------------------------------------------
  // Stats
  // ----------------------------------------------------------------

  stats: [
    { number: 19, label: 'Agentes' },
    { number: 61, label: 'Skills' },
    { number: 6, label: 'Flujos' },
    { number: 26, label: 'Comandos' },
    { number: 7, label: 'Templates' },
    { number: 13, label: 'Hooks' },
    { number: 23, label: 'Gates' },
  ],

  // ----------------------------------------------------------------
  // Agentes de nucleo
  // ----------------------------------------------------------------

  coreAgents: {
    header: {
      label: 'El equipo',
      title: '10 agentes de núcleo',
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
        name: 'SonIA',
        model: 'sonnet',
        alias: 'Project Manager',
        role: 'Si no está en el kanban, no existe. Descompone el PRD en tareas, traza cada criterio de aceptación hasta su test y documentación, y detecta desvíos de alcance.',
        phrase: '"El criterio CA-05 no tiene test asociado. Quién se encarga?"',
        color: 'var(--magenta)',
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
        color: 'var(--gold)',
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
        name: 'El escriba',
        model: 'sonnet',
        alias: 'Tech Writer',
        role: 'Document first. Comenta el código inline (cabeceras, docstrings) y genera la documentación de proyecto: API docs, arquitectura con diagramas Mermaid, guías y changelogs.',
        phrase: '"Ese fichero no tiene cabecera. Nadie sabe para qué sirve."',
        color: 'var(--white)',
      },
      {
        name: 'Selina',
        model: 'opus',
        alias: 'Sistema de diseño',
        role: 'Dirección de sistema de diseño. Parte de 10 familias base y deja cerradas tipografía, paleta y densidad antes de que el architect diseñe el primer componente. Solo activa en proyectos con interfaz de usuario.',
        phrase: '"El estilo no es decoración: es comunicación."',
        color: 'var(--purple)',
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
      title: '9 agentes opcionales',
      description: 'Roles especializados que activas según lo que necesite tu proyecto. Alfred analiza tu stack y te sugiere cuáles activar. Se gestionan con <strong style="color: var(--blue);">/alfred-dev:config</strong>.',
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
      {
        name: 'La Intérprete',
        model: 'sonnet',
        alias: 'i18n Specialist',
        role: 'Auditoría de claves i18n, detección de cadenas hardcodeadas, validación de formatos por locale. Si el idioma base tiene N claves, todos los demás deben tener N.',
        phrase: '"El idioma base tiene 847 claves. El francés tiene 831. Faltan 16."',
        color: 'var(--cyan)',
      },
      {
        name: 'Lucius',
        model: 'opus',
        alias: 'Director técnico externo',
        role: 'Segunda opinión técnica vía Codex CLI con GPT-5.4. Audita el proyecto completo y devuelve diagnóstico y prescripción por ítem. Requiere suscripción activa de OpenAI. Sin modificaciones: solo analiza.',
        phrase: '"Desde fuera, esto tiene un punto débil que probablemente no veis porque estáis dentro."',
        color: '#d97706',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Composicion dinamica de equipo
  // ----------------------------------------------------------------

  composition: {
    header: {
      label: 'Composicion dinamica',
      labelColor: 'var(--gold)',
      title: 'El equipo que necesitas, cuando lo necesitas',
    description: 'Cuando Alfred detecta que toca abrir un flujo multiagente, analiza tu tarea en tiempo real y sugiere los agentes opcionales mas relevantes. Si antes toca mapear, retomar, verificar o mostrar progreso, resuelve eso primero.',
    },
    introHtml: 'Cuando <code style="font-family: var(--font-mono); font-size: 14px; color: var(--cyan);">/alfred-dev:alfred</code> o un comando explicito deciden que la ruta correcta es un flujo multiagente, Alfred razona sobre que especialistas encajan con el trabajo, te presenta la seleccion de agentes y arranca la fase adecuada. Asi se ve cuando la ruta elegida es <code style="font-family: var(--font-mono); font-size: 14px; color: var(--cyan);">/alfred-dev:feature</code>:',
    terminalPrompt: '$ /alfred-dev:feature',
    terminalText: 'Migrar la base de datos de SQLite a PostgreSQL y rediseñar la interfaz del checkout con tests de accesibilidad',
    coreTeamText: 'Equipo de nucleo (siempre activos): Alfred, Product Owner, Arquitecto, Senior Dev, Security Officer, QA Engineer, Tech Writer, DevOps, SonIA, Selina.',
    techQuestion: 'Que agentes tecnicos quieres activar?',
    techOptions: [
      { label: 'Data Engineer', desc: 'Migracion de BD detectada (Recomendado)', selected: true },
      { label: 'Performance Engineer', desc: 'Profiling y optimizacion', selected: false },
      { label: 'GitHub Manager', desc: 'Remote git configurado (Recomendado)', selected: true },
      { label: 'Librarian', desc: 'Memoria persistente', selected: false },
    ],
    contentQuestion: 'Que agentes de contenido y UX quieres activar?',
    contentOptions: [
      { label: 'UX Reviewer', desc: 'Rediseño de checkout (Recomendado)', selected: true },
      { label: 'SEO Specialist', desc: 'Posicionamiento web', selected: false },
      { label: 'Copywriter', desc: 'Textos publicos', selected: false },
      { label: 'i18n Specialist', desc: 'Internacionalizacion', selected: false },
    ],
    confirmText: 'Equipo confirmado: 10 de nucleo + 3 opcionales',
    productQuestion: 'Quien es el usuario principal de esta funcionalidad?',
    productOptions: [
      { label: 'Administrador de tienda', desc: '', selected: true },
      { label: 'Cliente final', desc: '', selected: false },
      { label: 'Equipo de soporte', desc: '', selected: false },
      { label: 'Desarrollador externo', desc: '', selected: false },
    ],
  },

  // ----------------------------------------------------------------
  // Flujos de trabajo
  // ----------------------------------------------------------------

  workflows: {
    header: {
      label: 'Flujos de trabajo',
      title: '6 flujos de ejecución, 18 fases',
      description: 'Cada flujo se ejecuta por fases. Entre fase y fase hay una quality gate (la sección de abajo las detalla todas). Fuera de los flujos, comandos como <code>next</code>, <code>pause</code>, <code>resume</code> y <code>progress</code> permiten pausar, retomar o consultar el estado sin perder el hilo.',
    },
    flows: [
      {
        command: '/alfred-dev:feature',
        subtitle: 'Ciclo completo o parcial',
        description: 'Hasta 7 fases: producto, sistema de diseño (Selina, condicional), arquitectura, desarrollo TDD, calidad + seguridad, documentación, entrega. Puedes arrancar desde cualquier fase.',
        stages: ['Producto', 'Estilo visual', 'Arquitectura', 'Desarrollo', 'Calidad + Seguridad', 'Documentación', 'Entrega'],
      },
      {
        command: '/alfred-dev:quick',
        subtitle: 'Cambio pequeño',
        description: '2 fases: ejecución acotada y validación rápida. Menos ceremonia que feature, pero con tests y revisión de seguridad.',
        stages: ['Ejecución acotada', 'Validación rápida'],
      },
      {
        command: '/alfred-dev:fix',
        subtitle: 'Corrección rápida',
        description: 'Diagnóstico de causa raíz, corrección con TDD (test que reproduce el bug primero), validación con QA + seguridad.',
        stages: ['Diagnóstico', 'Corrección TDD', 'Validación'],
      },
      {
        command: '/alfred-dev:spike',
        subtitle: 'Investigación',
        description: 'Exploración técnica sin compromiso: prototipos, benchmarks, evaluación de alternativas. Documento de hallazgos.',
        stages: ['Investigación', 'Hallazgos'],
      },
      {
        command: '/alfred-dev:ship',
        subtitle: 'Despliegue',
        description: 'Auditoría final paralela, documentación de release, empaquetado con versionado semántico, despliegue a producción.',
        stages: ['Auditoría', 'Documentación', 'Empaquetado', 'Despliegue'],
      },
      {
        command: '/alfred-dev:audit',
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
      title: 'Cobertura de calidad en todo el ciclo',
      description: 'Cada fase del desarrollo tiene sus propias quality gates. Los 10 agentes de núcleo cubren desde la validación del producto hasta la entrega, y los opcionales amplían el control a dominios especializados. Si una gate no se supera, el flujo se detiene.',
    },
    coreLabel: 'Núcleo -- de la idea a producción',
    core: [
      { text: 'Valida el PRD con el usuario antes de pasar a diseño' },
      { text: 'Revisa coherencia arquitectónica y acoplamiento entre módulos antes de codificar' },
      { text: 'Analiza el diseño en busca de vectores de ataque con modelo de amenazas' },
      { text: 'Aplica TDD estricto: test que falla, implementación mínima, refactor' },
      { text: 'Ejecuta tests unitarios, de integración y E2E antes de avanzar a calidad' },
      { text: 'Audita OWASP Top 10, CVEs en dependencias y compliance RGPD, NIS2 y CRA' },
      { text: 'Documenta código en línea durante el desarrollo y genera documentación de proyecto al cierre' },
      { text: 'Exige pipeline CI/CD en verde como requisito de entrega' },
      { text: 'Rastrea progreso entre fases y mantiene la trazabilidad de cada decisión' },
      { text: 'Consulta la memoria persistente del proyecto para contextualizar con el histórico' },
      { text: 'Vigila cada escritura de fichero buscando secretos, API keys o tokens' },
      { text: 'Detecta tildes omitidas en castellano al escribir o editar ficheros' },
      { text: 'Verifica que los tests se ejecutaron realmente antes de aceptar que pasan (evidencia verificable)' },
      { text: 'Itera dentro de cada fase hasta 5 veces si la gate no se supera, habilitando ciclos TDD naturales' },
    ],
    optionalLabel: 'Opcionales -- amplían el control',
    optional: [
      { text: 'Analiza el código con SonarQube (instala Docker si falta, con tu permiso)', optional: true },
      { text: 'Exige rollback en cada migración de base de datos antes de ejecutarla', optional: true },
      { text: 'Verifica accesibilidad WCAG 2.1 AA antes de dar por buena la interfaz', optional: true },
      { text: 'Mide rendimiento con métricas reales (p50, p95, p99) antes y después', optional: true },
      { text: 'Configura branch protection en main y exige PR con aprobación', optional: true },
      { text: 'Monitoriza Core Web Vitals (LCP, INP, CLS) y alerta si están fuera de umbral', optional: true },
      { text: 'Revisa meta tags, structured data y rastreabilidad SEO antes de publicar', optional: true },
      { text: 'Valida ortografía, tono y consistencia de los textos de la interfaz', optional: true },
      { text: 'Comprueba que todas las claves i18n del idioma base existan en todos los idiomas destino', optional: true },
    ],
  },

  // ----------------------------------------------------------------
  // Skills
  // ----------------------------------------------------------------

  skills: {
    header: {
      label: 'Capacidades',
      title: '61 skills en 14 dominios',
      description: 'Catalogo publicado del plugin: cada skill es una capacidad concreta que los agentes pueden invocar. Los 7 dominios originales se amplían con 6 nuevos para los agentes opcionales y un dominio adicional de sistema de diseño para Selina. Desde la v0.5.2, el manifiesto público de Claude Code expone los 14 dominios completos; los skills más pesados o con side effects claros siguen disponibles, pero marcados como manuales.',
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
          { name: 'dependency-strategy', description: 'Estrategia de dependencias a medio plazo' },
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
          { name: 'e2e-testing', description: 'Pruebas end-to-end de recorridos críticos' },
          { name: 'exploratory-testing', description: 'Testing exploratorio' },
          { name: 'incident-response', description: 'Triaje, mitigación y postmortem' },
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
          { name: 'release-planning', description: 'Versionado, changelog y release notes' },
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
        name: 'Estilo',
        skills: [
          { name: 'style-direction', description: 'Companion visual y cierre de dirección de estilo' },
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
      description: 'La infraestructura que hace funcionar al equipo: hooks que arrancan la sesión, templates que estandarizan artefactos y un core que orquesta tanto los flujos de ejecución como la continuidad operativa.',
    },
    groups: [
      {
        title: '13 hooks',
        items: [
          { name: 'session-bootstrap.sh', label: 'SessionStart' },
          { name: 'session-start.sh', label: 'SessionStart' },
          { name: 'stop-hook.py', label: 'Stop' },
          { name: 'secret-guard.sh', label: 'PreToolUse' },
          { name: 'dangerous-command-guard.py', label: 'PreToolUse' },
          { name: 'sensitive-read-guard.py', label: 'PreToolUse' },
          { name: 'prefetch-finish-guard.py', label: 'PreToolUse' },
          { name: 'quality-gate.py', label: 'PostToolUse' },
          { name: 'evidence-guard.py', label: 'PostToolUse' },
          { name: 'dependency-watch.py', label: 'PostToolUse' },
          { name: 'spelling-guard.py', label: 'PostToolUse' },
          { name: 'activity-capture.py', label: 'PostToolUse' },
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
        title: '6 módulos core',
        items: [
          { name: 'orchestrator.py', label: 'Flujos, sesiones, gates, loop iterativo y autopilot' },
          { name: 'continuity.py', label: 'Continuidad, PM operativo, búsqueda y sync GitHub' },
          { name: 'personality.py', label: 'Motor de personalidad' },
          { name: 'config_loader.py', label: 'Config y detección de stack' },
          { name: 'memory.py', label: 'Memoria persistente SQLite' },
          { name: 'session_report.py', label: 'Informes de sesión en markdown' },
        ],
      },
    ],
  },

  // ----------------------------------------------------------------
  // Comandos
  // ----------------------------------------------------------------

  commands: {
    header: {
      label: 'Interfaz',
      title: '26 comandos',
      description: 'Todo se controla desde la línea de comandos de Claude Code.',
    },
    groups: [
      {
        label: 'Flujos',
        color: 'var(--blue)',
        commands: [
          { command: '/alfred-dev:feature', description: 'Ciclo completo: hasta 7 fases o desde la que indiques. Selina se activa automáticamente en proyectos con UI para cerrar el sistema de diseño.' },
          { command: '/alfred-dev:quick',   description: 'Cambio pequeño con dos fases ligeras: ejecución acotada y validación rápida con QA + seguridad.' },
          { command: '/alfred-dev:fix',     description: 'Bug con 3 fases: diagnóstico, corrección TDD, validación.' },
          { command: '/alfred-dev:spike',   description: 'Investigación exploratoria sin compromiso: prototipos, benchmarks, conclusiones.' },
          { command: '/alfred-dev:ship',    description: 'Preparar release: auditoría final, documentación, empaquetado, despliegue.' },
          { command: '/alfred-dev:audit',   description: 'Auditoría con 4 agentes en paralelo: calidad, seguridad, arquitectura, documentación.' },
        ],
      },
      {
        label: 'Contexto',
        color: 'var(--green)',
        commands: [
          { command: '/alfred-dev:alfred',       description: 'Asistente contextual: detecta el estado del proyecto y decide si toca mapear, retomar, refinar o abrir un flujo.' },
          { command: '/alfred-dev:map-codebase', description: 'Analiza un repo existente y crea <code>codebase-map.md</code> y <code>current.md</code> antes de tocar código.' },
          { command: '/alfred-dev:discuss',      description: 'Refina una idea antes de abrir implementación. Deja <code>discovery.md</code> y el siguiente comando recomendado.' },
          { command: '/alfred-dev:lucius',       description: 'Segunda opinión externa vía Codex CLI (GPT-5.4). Diagnóstico y prescripción por ítem. Requiere suscripción OpenAI.' },
        ],
      },
      {
        label: 'Continuidad',
        color: 'var(--cyan)',
        commands: [
          { command: '/alfred-dev:next',   description: 'Responde “qué toca ahora” y ejecuta si la ruta es inequívoca: retomar, verificar, mapear o abrir flujo.' },
          { command: '/alfred-dev:pause',  description: 'Pausa el trabajo y deja un handoff explícito en <code>.claude/alfred-handoff.json</code>.' },
          { command: '/alfred-dev:resume', description: 'Retoma una sesión activa o handoff pendiente sin abrir una iteración nueva a ciegas.' },
          { command: '/alfred-dev:verify', description: 'Registra la validación manual/UAT del entregable, separando la aceptación humana de los tests automáticos.' },
        ],
      },
      {
        label: 'PM operativo',
        color: 'var(--magenta)',
        commands: [
          { command: '/alfred-dev:progress',    description: 'Progreso, kanban, bloqueos, trazabilidad y estado de UAT en una vista compacta.' },
          { command: '/alfred-dev:standup',     description: 'Standup diario accionable: foco actual, trabajo en curso, bloqueos y siguiente paso.' },
          { command: '/alfred-dev:blocked',     description: 'Tareas bloqueadas con dependencia, nota operativa y responsable.' },
          { command: '/alfred-dev:in-progress', description: 'Trabajo en curso sin releer todo el tablero.' },
          { command: '/alfred-dev:validate',    description: 'Salud del tablero: IDs duplicados, trazabilidad incompleta, UAT pendiente, drift de sync.' },
          { command: '/alfred-dev:search',      description: 'Busca en artefactos y memoria SQLite a la vez para responder dudas históricas u operativas.' },
          { command: '/alfred-dev:sync-github', description: 'SonIA Sync: refleja el tablero local en GitHub Issues con <code>gh</code>.' },
        ],
      },
      {
        label: 'Herramientas',
        color: 'var(--gold)',
        commands: [
          { command: '/alfred-dev:memory-ui', description: 'UI local en navegador sobre la SQLite del proyecto: overview, timeline, decisiones, commits, búsqueda.' },
          { command: '/alfred-dev:config',    description: 'Autonomía, stack, compliance, personalidad, agentes opcionales y memoria. Bootstrappeable en la primera sesión.' },
          { command: '/alfred-dev:status',    description: 'Sesión activa: fase actual, fases completadas, gate pendiente y foco inmediato.' },
          { command: '/alfred-dev:update',    description: 'Ver si hay versión nueva, leer las notas de release y actualizar con un clic.' },
          { command: '/alfred-dev:help',      description: 'Ayuda completa de todos los comandos disponibles.' },
        ],
      },
    ],
    optionalNote: 'Los 9 agentes opcionales se activan con <strong style=”color: var(--blue);”>/alfred-dev:config</strong> y Alfred los integra automáticamente en <em>feature</em>, <em>quick</em>, <em>fix</em>, <em>spike</em>, <em>audit</em> y <em>ship</em>.',
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
        command: '/alfred-dev:feature sistema de notificaciones push',
        steps: [
          'El product-owner genera el PRD con historias de usuario y criterios de aceptación',
          'El architect diseña la solución y el security-officer valida el diseño',
          'El senior-dev implementa siguiendo TDD estricto (rojo-verde-refactor)',
          'QA y seguridad auditan en paralelo antes de dar el visto bueno',
          'El escriba documenta el código inline y genera los docs de API; el devops-engineer prepara el despliegue',
        ],
      },
      {
        category: 'Corrección',
        color: 'var(--red)',
        background: 'rgba(229,86,79,0.08)',
        title: 'Corregir un bug',
        command: '/alfred-dev:fix el login falla con emails que tienen tildes',
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
        command: '/alfred-dev:spike evaluar si migrar de REST a gRPC',
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
        command: '/alfred-dev:audit',
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
        command: '/alfred-dev:ship',
        steps: [
          'Auditoría final obligatoria: QA y seguridad deben aprobar',
          'El escriba actualiza el changelog y genera las notas de release',
          'El devops-engineer empaqueta, configura el pipeline y verifica el build',
          'Despliegue supervisado: el usuario confirma antes de subir a producción',
        ],
      },
      {
        category: 'Conversacional',
        color: 'var(--gold)',
        background: 'rgba(201,169,110,0.08)',
        title: 'Asistente contextual',
        command: '/alfred-dev:alfred',
        steps: [
          'Alfred detecta el stack del proyecto, la sesión activa, el handoff pendiente y si falta mapa brownfield',
          'Decide si toca next, map-codebase, discuss, quick, feature, fix, spike, audit, verify o progress',
          'Si la ruta correcta es operativa, la resuelve antes de abrir un equipo multiagente',
          'Solo compone agentes cuando de verdad toca un flujo de ejecución',
        ],
      },
      {
        category: 'Brownfield',
        color: 'var(--cyan)',
        background: 'rgba(78,201,201,0.08)',
        title: 'Entrar en un repo existente',
        command: '/alfred-dev:map-codebase checkout',
        steps: [
          'Alfred analiza README, manifiestos, estructura principal y zonas sensibles sin tocar código de producto',
          'Genera docs/project/codebase-map.md con dominios, entrypoints, hotspots, pruebas, despliegue y riesgos',
          'Deja docs/project/current.md con lectura operativa y siguiente comando recomendado',
          'A partir de ahí feature, fix, spike y audit ya no arrancan a ciegas',
        ],
      },
      {
        category: 'Refinado',
        color: 'var(--gold)',
        background: 'rgba(201,169,110,0.08)',
        title: 'Aterrizar una idea antes de construir',
        command: '/alfred-dev:discuss nuevo onboarding para equipos',
        steps: [
          'Alfred clarifica problema real, actor principal, alcance y supuestos antes de hablar de implementación',
          'Persiste el refinado en docs/project/discovery.md y actualiza docs/project/current.md',
          'Si la idea ya está madura, recomienda feature o quick; si faltan datos técnicos, spike',
          'Evita abrir PRD, arquitectura o desarrollo antes de tiempo',
        ],
      },
      {
        category: 'Cambio pequeño',
        color: 'var(--blue)',
        background: 'rgba(91,156,245,0.08)',
        title: 'Resolver algo pequeño sin abrir toda la maquinaria',
        command: '/alfred-dev:quick corregir copy del checkout y su test',
        steps: [
          'Quick abre una sesión ligera con dos fases: ejecución acotada y validación rápida',
          'El senior-dev cambia solo la superficie tocada y actualiza los tests necesarios',
          'QA y seguridad revisan regresión local y riesgos obvios sin convertirlo en una auditoría global',
          'El siguiente paso esperado queda explícito: /alfred-dev:verify',
        ],
      },
      {
        category: 'Continuidad',
        color: 'var(--green)',
        background: 'rgba(78,201,144,0.08)',
        title: 'Saber qué toca ahora',
        command: '/alfred-dev:next',
        steps: [
          'Prioriza sesión activa, handoff pendiente, UAT pendiente o brownfield sin mapear',
          'Si la salida es inequívoca, ejecuta la ruta correcta sin ofrecer un menú genérico',
          'Si hay trabajo a retomar, muestra flujo, fase actual, gate pendiente y siguiente acción concreta',
          'Si no hay nada vivo, sugiere el siguiente flujo razonable para el estado real del proyecto',
        ],
      },
      {
        category: 'Continuidad',
        color: 'var(--purple)',
        background: 'rgba(160,126,232,0.08)',
        title: 'Pausar y retomar sin perder el hilo',
        command: '/alfred-dev:pause',
        steps: [
          'Pause guarda handoff en .claude/alfred-handoff.json y docs/project/handoff.md',
          'Resume reutiliza estado e handoff para volver exactamente al punto en que se dejó el trabajo',
          'No abre una iteración nueva ni empuja gates por su cuenta: primero deja claro qué toca',
          'Sirve igual para sesiones largas de feature que para quick o trabajo interrumpido',
        ],
      },
      {
        category: 'Verificación',
        color: 'var(--red)',
        background: 'rgba(229,86,79,0.08)',
        title: 'Cerrar la aceptación manual',
        command: '/alfred-dev:verify aprobado smoke manual correcto',
        steps: [
          'Verify prepara o actualiza la UAT del entregable actual en .claude/alfred-uat.json y docs/project/uat.md',
          'Separa claramente los tests automáticos de la validación humana final',
          'Registra si la UAT queda pendiente, aprobada o rechazada, junto con la nota principal',
          'Si la validación falla, el siguiente paso operativo vuelve a quedar visible en current/uat',
        ],
      },
      {
        category: 'Project management',
        color: 'var(--magenta)',
        background: 'rgba(214,106,214,0.08)',
        title: 'Ver el estado real del proyecto',
        command: '/alfred-dev:progress',
        steps: [
          'Progress expone la capa operativa de SonIA: progreso general, kanban, bloqueos y trazabilidad',
          'Resume el flujo activo o el handoff pendiente sin reabrir el trabajo en curso',
          'Muestra huecos de trazabilidad y el estado de la UAT si existe',
          'Cierra con el siguiente comando recomendado para seguir avanzando',
        ],
      },
      {
        category: 'Project management',
        color: 'var(--magenta)',
        background: 'rgba(214,106,214,0.08)',
        title: 'Tener un standup diario sin abrir GitHub ni releer docs',
        command: '/alfred-dev:standup',
        steps: [
          'Standup resume foco actual, tareas en curso, bloqueos, evidencia reciente y recomendación operativa',
          'Lee el kanban de SonIA, el estado de continuidad y la UAT pendiente o aprobada',
          'Sirve como briefing rápido antes de seguir trabajando o delegar una tarea',
          'No modifica el tablero: solo hace visible lo importante',
        ],
      },
      {
        category: 'Project management',
        color: 'var(--magenta)',
        background: 'rgba(214,106,214,0.08)',
        title: 'Validar la salud operativa antes de seguir',
        command: '/alfred-dev:validate',
        steps: [
          'Validate revisa backlog, in-progress, blocked y done buscando IDs duplicados o tareas sin metadatos básicos',
          'Contrasta trazabilidad, evidencia, UAT y artefactos clave como progress.md o traceability.md',
          'Si existe sync local con GitHub, también detecta desalineaciones entre tareas e issues',
          'Devuelve un checklist accionable para corregir el tablero antes de seguir avanzando',
        ],
      },
      {
        category: 'Project management',
        color: 'var(--text-muted)',
        background: 'rgba(110,115,138,0.08)',
        title: 'Ejecutar SonIA Sync con GitHub',
        command: '/alfred-dev:sync-github owner/repo',
        wide: true,
        image: {
          src: '/screenshots/sonia-sync-github.png',
          alt: 'Vista de SonIA Sync en GitHub Issues con el issue paraguas y las tareas sincronizadas',
          caption: 'SonIA Sync reflejando backlog, trabajo en curso, bloqueos y el issue paraguas en GitHub Issues.',
        },
        steps: [
          'Lee el tablero local y crea o actualiza issues para backlog, trabajo en curso, bloqueos y tareas terminadas',
          'Asegura labels de Alfred y un issue paraguas de SonIA Sync con el resumen global',
          'Guarda el mapping local en .claude/alfred-github-sync.json y un resumen humano en docs/project/github-sync.md',
          'GitHub actúa como espejo colaborativo: la verdad sigue estando en docs/project y SQLite',
        ],
      },
      {
        category: 'Contexto',
        color: 'var(--gold)',
        background: 'rgba(201,169,110,0.08)',
        title: 'Buscar contexto sin explorar medio repo',
        command: '/alfred-dev:search login social',
        steps: [
          'Search cruza discovery, current, handoff, UAT, kanban y memoria persistente en una sola consulta',
          'Devuelve coincidencias de artefactos operativos y decisiones históricas con su origen visible',
          'Es especialmente útil para saber por qué se tomó una decisión o dónde quedó apuntado un bloqueo',
          'Evita abrir manualmente varios Markdown o consultar SQLite por separado',
        ],
      },
      {
        category: 'Memoria',
        color: 'var(--blue)',
        background: 'rgba(84,196,255,0.08)',
        title: 'Abrir la memoria viva del proyecto',
        command: '/alfred-dev:memory-ui',
        wide: true,
        steps: [
          'Levanta una UI local en el navegador sobre la SQLite real del proyecto, sin duplicar la fuente de verdad',
          'Muestra overview, timeline, decisiones, commits, búsqueda y salud del almacén en una sola pantalla',
          'Mezcla memoria persistente con señales operativas de current, progress, traceability y kanban cuando existen',
          'Se refresca sola mientras Alfred sigue trabajando, así que sirve como panel vivo del proyecto',
        ],
      },
      {
        category: 'Sistema de diseño',
        color: 'var(--purple)',
        background: 'rgba(160,126,232,0.08)',
        title: 'Cerrar el sistema de diseño antes de construir',
        command: '/alfred-dev:feature nueva app de finanzas personales',
        wide: true,
        image: {
          src: '/screenshots/selina-style-direction.svg',
          alt: 'Selina enseñando una galería de sistemas de diseño y tres propuestas finalistas en el navegador',
          caption: 'Selina parte de 10 sistemas de diseño base, reduce la decisión a tres finalistas comparables y cierra la gate con docs/style-direction.md antes de que el architect diseñe un solo componente.',
        },
        steps: [
          'Selina lee el PRD aprobado, detecta el stack (framework, componentes, contexto del producto) y decide qué familias del catálogo de 10 sistemas merecen entrar en la ronda final',
          'Puede enseñar primero la galería base y después genera tres propuestas HTML en pantalla completa: cada una con tipografía, paleta, densidad y personalidad claramente distinta',
          'El usuario elige en el navegador; Selina registra la elección y genera docs/style-direction.md con el sistema de diseño ya aterrizado',
          'Architect, senior-dev, ux-reviewer, copywriter y seo-specialist leen ese artefacto como referencia de diseño para el resto del flujo',
          'La fase se salta automáticamente en proyectos sin interfaz de usuario',
        ],
      },
      {
        category: 'Calidad',
        color: 'var(--red)',
        background: 'rgba(229,86,79,0.08)',
        title: 'Análisis con SonarQube',
        command: '/alfred-dev:audit',
        steps: [
          'El security-officer comprueba si Docker está instalado; si no, pide permiso al usuario para instalarlo',
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
        command: '/alfred-dev:feature añadir sistema de suscripciones con pagos',
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
        command: '/alfred-dev:ship',
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
        command: '/alfred-dev:audit',
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
        command: '/alfred-dev:audit',
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
        command: '/alfred-dev:spike la API tarda 3 segundos en responder',
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
          'Verificación de evidencia -- registra cada ejecución de tests como evidencia verificable, impidiendo afirmaciones sin pruebas',
          'Vigilancia de dependencias -- detecta nuevas librerías y notifica al auditor de seguridad',
          'Guardia ortográfico -- detecta palabras castellanas sin tilde al escribir o editar ficheros',
          'Captura de memoria -- registra automáticamente eventos del flujo de trabajo en la memoria persistente',
          'Captura de commits -- detecta cada git commit y registra SHA, autor y ficheros en la memoria',
          'Contexto protegido -- las decisiones críticas sobreviven a la compactación de contexto',
          'Informe de sesión -- al cerrar una sesión completada se genera un resumen en docs/alfred-reports/ con fases, evidencia y artefactos',
        ],
      },
      {
        category: 'Autonomía',
        color: 'var(--green)',
        background: 'rgba(78,201,126,0.08)',
        title: 'Modo autopilot',
        command: '/alfred-dev:feature --autopilot',
        steps: [
          'El flujo completo se ejecuta sin intervención: las gates de usuario se aprueban automáticamente',
          'Las gates automáticas (tests) y de seguridad se siguen evaluando normalmente',
          'Si una gate automática falla, el loop iterativo reintenta hasta 5 veces antes de escalar',
        ],
      },
    ],
  },

  // ----------------------------------------------------------------
  // Memoria persistente
  // ----------------------------------------------------------------

  memory: {
    sectionLabel: 'Memoria persistente por proyecto',
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
        descriptionHtml: 'Texto completo con FTS5 cuando está disponible, con fallback automático a LIKE para entornos sin extensión FTS. Busca en títulos de decisiones, razones, alternativas descartadas, mensajes de commit y eventos con contenido.',
      },
      {
        title: 'Captura automática',
        descriptionHtml: 'Un único hook unificado (<code>activity-capture.py</code>) captura todo automáticamente: eventos del flujo (iteraciones, fases), commits de Git (SHA, mensaje, autor, ficheros) y actividad de herramientas. Dispatch interno según el tipo de evento.',
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
      activationHtml: '<strong>Activación:</strong> se habilita desde <strong style="color: var(--blue);">/alfred-dev:config</strong> en la sección de memoria persistente. Una vez activo, Alfred le delega automáticamente las consultas históricas que surjan durante cualquier flujo.',
    },
    faq: [
      {
        question: 'Dónde se almacenan los datos?',
        answerHtml: 'En el fichero <code>.claude/alfred-memory.db</code> dentro de la raíz de cada proyecto. Es un fichero SQLite local, no se envía nada a servicios externos. Añádelo a <code>.gitignore</code> si no quieres versionarlo.',
      },
      {
        question: 'La memoria se activa sola?',
        answerHtml: 'No. La activación es explícitamente opcional. Se habilita desde <strong>/alfred-dev:config</strong> en la sección de memoria. Si no la activas, no se crea la base de datos ni se captura nada.',
      },
      {
        question: 'Qué pasa con los secretos?',
        answerHtml: 'Todo el contenido pasa por la misma sanitización que usa el hook secret-guard.sh antes de almacenarse. Claves de API, tokens, JWT, cadenas de conexión y cabeceras de clave privada se redactan automáticamente. El fichero de base de datos tiene permisos 0600 (solo lectura/escritura para el propietario).',
      },
      {
        question: 'Puedo borrar la memoria?',
        answerHtml: 'Sí. Basta con eliminar el fichero <code>.claude/alfred-memory.db</code>. También puedes desactivar la memoria desde <strong>/alfred-dev:config</strong>: los datos existentes se conservan pero dejan de consultarse y no se capturan nuevos eventos.',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Instalacion
  // ----------------------------------------------------------------

  install: {
    sectionLabel: 'Primeros pasos',
    title: 'Instalación',
    description: 'Un comando en la terminal y listo. Compatible con macOS, Linux y Windows. El instalador es idempotente: ejecutarlo de nuevo actualiza sin conflictos. En la primera sesión Alfred puede bootstrappear tu configuración local y sugerirte el siguiente paso.',
    tabs: [
      {
        id: 'macos',
        label: 'macOS',
        command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash',
        requirementsHtml: '<strong>Requisitos:</strong> Python 3.10+, Claude Code instalado.<br>Tras la instalación, reinicia Claude Code y ejecuta <strong>/alfred-dev:alfred</strong> o <strong>/alfred-dev:help</strong>.',
      },
      {
        id: 'linux',
        label: 'Linux',
        command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash',
        requirementsHtml: '<strong>Requisitos:</strong> Python 3.10+, Claude Code instalado.<br>Tras la instalación, reinicia Claude Code y ejecuta <strong>/alfred-dev:alfred</strong> o <strong>/alfred-dev:help</strong>.',
      },
      {
        id: 'windows',
        label: 'Windows',
        command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex',
        requirementsHtml: '<strong>Requisitos:</strong> PowerShell 5.1+ (preinstalado en Windows 10/11), Python 3.10+, Claude Code instalado.<br>Tras la instalación, reinicia Claude Code y ejecuta <strong>/alfred-dev:alfred</strong> o <strong>/alfred-dev:help</strong>.<br>Alternativa: también puedes usar el instalador bash con WSL o Git Bash.',
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
      descriptionHtml: 'Desde Claude Code, ejecuta <strong style="color: var(--blue);">/alfred-dev:update</strong> para comprobar si hay una versión nueva. Si la hay, Alfred te muestra las notas de la release y te pregunta si quieres actualizar. También puedes volver a ejecutar el instalador: es idempotente.',
    },
  },

  // ----------------------------------------------------------------
  // Configuracion
  // ----------------------------------------------------------------

  config: {
    sectionLabel: 'Personalización',
    title: 'Configuración por proyecto',
    descriptionHtml: 'Cada proyecto tiene su propio fichero de configuración en <code>.claude/alfred-dev.local.md</code>. La primera sesión puede generarlo automáticamente con una configuración usable para CLI; después <strong>/alfred-dev:config</strong> te deja revisarlo y ampliarlo con autonomía, agentes opcionales y memoria persistente.',
    yamlExample: `---
autonomia:
  producto: autonomo
  arquitectura: autonomo
  desarrollo: autonomo
  calidad: autonomo
  documentacion: autonomo
  entrega: autonomo

agentes_opcionales:
  data-engineer: false
  ux-reviewer: false
  performance-engineer: false
  github-manager: false
  seo-specialist: false
  copywriter: false
  librarian: false
  i18n-specialist: false

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
      {
        title: 'Bootstrap automático',
        descriptionHtml: 'Si un proyecto no tiene configuración local, Alfred puede generar <code>.claude/alfred-dev.local.md</code> automáticamente en la primera sesión para que el plugin sea usable desde CLI sin preparación manual.',
      },
      {
        title: 'Autonomía operativa',
        descriptionHtml: 'Controla cuánta intervención necesitas en cada fase o tramo del flujo. En modo autónomo Alfred reduce entrevistas innecesarias y prioriza continuidad, brownfield y siguiente paso antes de abrir un equipo completo.',
      },
      {
        title: 'Agentes opcionales',
        descriptionHtml: 'Activa solo los que necesites. Alfred analiza tu proyecto y te sugiere cuáles habilitar según el stack detectado. Se pueden cambiar en cualquier momento sin reinstalar.',
      },
      {
        title: 'Memoria y contexto',
        descriptionHtml: 'La memoria persistente y los artefactos de continuidad conviven: decisiones en SQLite por proyecto, handoff, UAT y documentos operativos en <code>docs/project/</code> para retomar trabajo sin perder el hilo.',
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
        answerHtml: 'Ejecuta <strong>/alfred-dev:update</strong> dentro de Claude Code. El comando consulta GitHub, compara versiones y te muestra las notas de la release si hay versión nueva. También puedes volver a ejecutar el instalador: sobreescribe la versión anterior sin conflictos.',
      },
      {
        svgContent: '<path d="M3 12h18"/><path d="M12 3v18"/><path d="M5 5l14 14"/>',
        question: 'Qué hace Alfred en un repo ya existente?',
        answerHtml: 'Si el proyecto ya tiene código pero todavía no tiene mapa persistente, Alfred prioriza <strong>/alfred-dev:map-codebase</strong>. Analiza la estructura, detecta stack, entrypoints, riesgos y convenciones, y deja el contexto en <code>docs/project/codebase-map.md</code> y <code>docs/project/current.md</code> antes de abrir <strong>feature</strong>, <strong>fix</strong>, <strong>spike</strong> o <strong>audit</strong>.',
      },
      {
        svgContent: '<path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/>',
        question: 'Cuándo uso quick y cuándo feature?',
        answerHtml: '<strong>/alfred-dev:quick</strong> es para cambios pequeños, locales y acotados: dos fases ligeras, tests de la zona tocada y revisión rápida de seguridad. <strong>/alfred-dev:feature</strong> es para funcionalidad nueva o cambios que cruzan varios dominios, necesitan PRD, decisiones de arquitectura o un ciclo completo de producto a entrega.',
      },
      {
        svgContent: '<path d="M12 2v4"/><path d="M12 18v4"/><path d="M4.93 4.93l2.83 2.83"/><path d="M16.24 16.24l2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="M4.93 19.07l2.83-2.83"/><path d="M16.24 7.76l2.83-2.83"/>',
        question: 'Puedo pausar y retomar una sesión?',
        answerHtml: 'Sí. <strong>/alfred-dev:pause</strong> guarda el estado actual en <code>.claude/alfred-handoff.json</code> y <code>docs/project/handoff.md</code>. Después puedes volver con <strong>/alfred-dev:resume</strong> o pedir simplemente <strong>/alfred-dev:next</strong>. Alfred recupera el flujo, la fase actual, la gate pendiente y el siguiente paso concreto.',
      },
      {
        svgContent: '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
        question: 'Qué es verify y por qué existe si ya hay tests?',
        answerHtml: '<strong>/alfred-dev:verify</strong> cierra la validación humana del entregable. Los tests automáticos dicen si el sistema funciona técnicamente; verify registra si cumple la expectativa del usuario en UAT. El estado queda trazado como <em>pendiente</em>, <em>aprobado</em> o <em>rechazado</em> en <code>.claude/alfred-uat.json</code> y <code>docs/project/uat.md</code>.',
      },
      {
        svgContent: '<path d="M3 3v18h18"/><path d="M7 14l3-3 3 2 4-5"/>',
        question: 'Qué muestra progress?',
        answerHtml: '<strong>/alfred-dev:progress</strong> hace visible el estado operativo del proyecto: flujo activo o handoff, progreso general, kanban, bloqueos, trazabilidad y estado de UAT. No abre trabajo nuevo ni fuerza una gate; sirve para decidir qué toca ahora con contexto real.',
      },
      {
        svgContent: '<path d="M4 19h16"/><path d="M4 5h16"/><path d="M9 9h11"/><path d="M9 15h7"/><circle cx="6" cy="9" r="1"/><circle cx="6" cy="15" r="1"/>',
        question: 'Qué añade SonIA en 0.4.5?',
        answerHtml: 'Ahora SonIA no solo mantiene el tablero por debajo. <strong>/alfred-dev:standup</strong>, <strong>/alfred-dev:blocked</strong>, <strong>/alfred-dev:in-progress</strong>, <strong>/alfred-dev:validate</strong> y <strong>/alfred-dev:search</strong> convierten ese estado en una interfaz operativa diaria desde CLI.',
      },
      {
        svgContent: '<path d="M9 19c-5 1.5-5-2.5-7-3"/><path d="M15 22v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 19 4.77 5.07 5.07 0 0 0 18.91 1S17.73.65 15 2.48a13.38 13.38 0 0 0-6 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77 5.44 5.44 0 0 0 3.5 8.53c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>',
        question: 'GitHub pasa a ser la fuente de verdad del proyecto?',
        answerHtml: 'No. <strong>/alfred-dev:sync-github</strong> ejecuta SonIA Sync como espejo colaborativo para issues. La fuente de verdad sigue siendo local: <code>docs/project/</code>, <code>.claude/</code> y la memoria SQLite del proyecto.',
      },
      {
        svgContent: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8"/><path d="M12 16v4"/><path d="M7 9h10"/><path d="M7 12h6"/>',
        question: 'Qué es Memory UI y cuándo debería usarla?',
        answerHtml: '<strong>/alfred-dev:memory-ui</strong> abre una vista local en navegador sobre la SQLite real del proyecto. Úsala cuando quieras entender rápido qué ha pasado, qué decisiones hay registradas, qué commits se han capturado, cómo va la continuidad o si la memoria está sana, sin leer la base de datos a mano.',
      },
      {
        svgContent: '<path d="M12 2l4 4-4 4-4-4 4-4z"/><path d="M4 12l4 4-4 4-4-4 4-4z"/><path d="M20 12l4 4-4 4-4-4 4-4z"/><path d="M12 10v4"/><path d="M10 12h4"/>',
        question: 'Tengo que configurar Alfred a mano la primera vez?',
        answerHtml: 'No necesariamente. En la primera sesión Alfred puede bootstrappear <code>.claude/alfred-dev.local.md</code> con una configuración base usable para CLI. Después puedes afinar autonomía, agentes opcionales, memoria o personalidad con <strong>/alfred-dev:config</strong>.',
      },
      {
        svgContent: '<path d="M19.439 5.56a5.018 5.018 0 0 0-7.09 0L11 6.91l-1.35-1.35a5.013 5.013 0 0 0-7.09 7.09L11 21.09l8.44-8.44a5.013 5.013 0 0 0 0-7.09z"/>',
        question: 'Es compatible con otros plugins de Claude Code?',
        answerHtml: 'Sí. Alfred Dev convive sin conflictos con otros plugins instalados. Usa su propio namespace (<code>alfred-dev</code>) y no interfiere con la configuración de otros plugins.',
      },
      {
        svgContent: '<circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6M4.22 4.22l4.24 4.24m7.08 7.08l4.24 4.24M1 12h6m6 0h6M4.22 19.78l4.24-4.24m7.08-7.08l4.24-4.24"/>',
        question: 'Qué son los agentes opcionales?',
        answerHtml: 'Son 9 agentes especializados que puedes activar según las necesidades de tu proyecto: <strong>data-engineer</strong> (bases de datos), <strong>ux-reviewer</strong> (accesibilidad y usabilidad), <strong>performance-engineer</strong> (rendimiento), <strong>github-manager</strong> (gestión de repositorios), <strong>seo-specialist</strong> (posicionamiento web), <strong>copywriter</strong> (textos y ortografía), <strong>El Bibliotecario</strong> (memoria persistente: consultas históricas sobre decisiones, commits e iteraciones del proyecto), <strong>La Intérprete</strong> (internacionalización: auditoría de claves i18n, detección de cadenas hardcodeadas, validación de formatos por locale) y <strong>Lucius</strong> (segunda opinión técnica externa con Codex CLI).<br><br>Alfred analiza tu proyecto y te sugiere cuáles activar. También puedes gestionarlos manualmente con <strong>/alfred-dev:config</strong>. Se activan o desactivan sin reinstalar nada.',
      },
      {
        svgContent: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
        question: 'Cuántos skills tiene en total?',
        answerHtml: 'Alfred mantiene 61 skills distribuidos en 14 dominios. Los 7 dominios originales (producto, arquitectura, desarrollo, seguridad, calidad, DevOps, documentación) cubren el ciclo de vida estándar. Los 6 dominios de agentes opcionales (datos, UX, rendimiento, GitHub, SEO, marketing) amplían el alcance del plugin y Selina añade un dominio específico de sistema de diseño. Desde la v0.5.2, el manifiesto público de Claude Code publica el catálogo completo por dominios; los skills más delicados siguen visibles, pero forzados a activación manual explícita.',
      },
      {
        svgContent: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
        question: 'Qué es la memoria persistente?',
        answerHtml: 'Es una base de datos SQLite local que almacena las decisiones, commits e iteraciones de cada proyecto. Se activa opcionalmente desde <strong>/alfred-dev:config</strong>. Una vez activa, Alfred registra automáticamente los eventos del flujo de trabajo y el agente <strong>El Bibliotecario</strong> puede responder consultas históricas como "por qué se eligió esta arquitectura" o "qué se hizo en la última iteración", citando siempre las fuentes. Los datos no salen del proyecto: todo queda en <code>.claude/alfred-memory.db</code>.',
      },
      {
        svgContent: '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
        question: 'Cuánto cuesta?',
        answerHtml: 'Nada. Alfred Dev es software libre bajo licencia MIT. Puedes usarlo, modificarlo y distribuirlo sin restricciones. El código fuente está en GitHub (github.com/686f6c61/alfred-dev).',
      },
      {
        svgContent: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        question: 'En qué idioma responde Alfred?',
        answerHtml: 'Castellano de España por defecto: tanto las respuestas como los comentarios de código, commits y documentación generada. Puedes ajustar este comportamiento con <strong>/alfred-dev:config</strong>.',
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
        answerHtml: 'Sí, como cualquier interacción con Claude. Los agentes son instrucciones de sistema que guían las respuestas, así que consumen contexto proporcional a su complejidad. En la práctica, el coste adicional es moderado: los system prompts de los agentes están optimizados para ocupar el mínimo posible sin perder precisión. Los agentes opcionales solo se cargan si los activas, así que el contexto base es el de los 10 de núcleo.',
      },
      {
        svgContent: '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
        question: 'Puedo usar Alfred en un monorepo?',
        answerHtml: 'Alfred detecta el stack del directorio de trabajo actual, no del repositorio raíz. Si ejecutas Claude Code desde la raíz de un monorepo, detectará todos los lenguajes presentes. Si lo ejecutas desde un paquete concreto, se centrará en ese paquete. La memoria persistente es por directorio de trabajo, así que cada paquete puede tener su propia base de datos de decisiones si lo configuras así.',
      },
      {
        svgContent: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
        question: 'Qué pasa si una quality gate falla?',
        answerHtml: 'El flujo se detiene en la fase actual y Alfred te explica qué no se cumple: tests que fallan, vulnerabilidades detectadas, documentación incompleta o lo que corresponda. Tienes tres opciones: corregir el problema y reintentar la gate, pedir a Alfred que te ayude a resolverlo (por ejemplo, con <strong>/alfred-dev:fix</strong> si es un bug), o continuar manualmente asumiendo el riesgo. Alfred nunca avanza en silencio si una gate no se supera.',
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
      version: '0.5.2',
      date: '2026-04-11',
      added: [
        '<strong>Catálogo completo de skills publicado</strong>: <code>plugin.json</code> deja de enumerar una muestra parcial y pasa a exponer los 14 dominios completos de <code>skills/</code>.',
        '<strong>Contratos de superficie pública más estrictos</strong>: la suite valida catálogo publicado, frontmatters canónicos, skills manuales y ausencia de colisiones con comandos.',
        '<strong>Selina con flujo guiado real</strong>: primero sistema base, luego tipografía y paleta, y solo después tres propuestas finales comparables dentro de esa misma familia.',
      ],
      changed: [
        'Los skills más pesados o con side effects claros quedan publicados, pero forzados a activación manual con <code>disable-model-invocation: true</code>.',
        'La ayuda y la documentación pública agrupan ahora los comandos por valor real: core, operativos avanzados y vistas/aliases.',
        'Las propuestas finales de Selina ya respetan el sistema visual elegido y dejan de recolorear la misma maqueta genérica.',
        'La landing deja de presentar el catálogo como una muestra interna/parcial y refleja ya las 61 skills publicadas de la release.',
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
        '<strong>Lucius — El Director Técnico</strong>: nuevo agente opcional que actúa como segunda opinión técnica externa. Invoca <code>codex review</code> con GPT-5.4 en modo de solo lectura y entrega diagnóstico + prescripción por ítem.',
        '<strong>Comando <code>/alfred-dev:lucius</code></strong>: punto de entrada para invocar la auditoría. Acepta directorio objetivo y scope opcionales (<code>all</code>, <code>security</code>, <code>tests</code>, <code>architecture</code>, <code>performance</code>).',
        '<strong>Informe estructurado por ítem</strong>: Lucius devuelve diagnóstico + prescripción + esfuerzo (S/M/L) + sugerencia de con quién implementar (Alfred o Codex) en cuatro secciones: Crítico, Relevante, Oportunidades y Lo que está bien.',
        '<strong>Preflight de prerequisitos</strong>: verifica que <code>codex</code> está en el PATH y autenticado. Si falta algún requisito, para con instrucciones claras de instalación.',
        '<strong>HARD-GATE sin modificaciones</strong>: el subcomando <code>codex review</code> activa <code>sandbox: read-only</code> y <code>approval: never</code> de forma nativa, garantizando que ningún fichero se toca.',
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
        'Permisos de Docker en subagentes: entradas <code>Bash(docker ...)</code> en <code>~/.claude/settings.json</code> permiten que <code>security-officer</code> arranque SonarQube sin pedir confirmación al usuario.',
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
        '/alfred-dev:alfred pasa a ser un router contextual: decide si toca continuidad, brownfield, refinado o flujo multiagente.',
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
        '<strong>SonarQube movido al security-officer</strong> -- el análisis de SonarQube lo ejecuta ahora el security-officer en lugar del qa-engineer durante <code>/alfred-dev:audit</code>. Levanta Docker, ejecuta el scanner end-to-end e integra los hallazgos en su informe de seguridad.',
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
        '<strong>SonarQube integrado en audit</strong> -- el security-officer ejecuta el skill de SonarQube como paso por defecto. Verificado end-to-end con Docker.',
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
    version: 'v0.5.2',
    license: 'MIT License',
    githubUrl: 'https://github.com/686f6c61/alfred-dev',
    docsUrl: 'https://github.com/686f6c61/alfred-dev/tree/main/docs',
    tagline: 'Plugin de Claude Code. 19 agentes. Catalogo publicado de 61 skills. 13 hooks. 26 comandos. 10 sistemas de diseño con Selina. Memory UI local. Memoria persistente. Continuidad operativa. PM operacional. De la idea a producción.',
    slogan: 'Ingeniería de software automatizada para Claude Code.',
    disclaimer: {
      linkText: 'Descargo de responsabilidad',
      title: 'Descargo de responsabilidad',
      closeText: 'Cerrar',
      contentHtml: `
        <p><strong>Alfred Dev</strong> es un proyecto independiente de codigo abierto. No esta afiliado, patrocinado ni respaldado por <strong>Anthropic</strong> ni por el equipo de <strong>Claude Code</strong>.</p>
        <p>El software se proporciona «tal cual» (<em>as is</em>), sin garantias de ningun tipo, expresas o implicitas, incluyendo, entre otras, las garantias de comerciabilidad, adecuacion a un proposito particular y no infraccion. En ningun caso los autores o titulares de los derechos de autor seran responsables de reclamaciones, danos u otras responsabilidades derivadas del uso del software.</p>
        <p>Alfred Dev ejecuta agentes que pueden crear, modificar y eliminar ficheros, ejecutar comandos en terminal e interactuar con servicios externos (GitHub, Docker, etc.). El usuario es responsable de revisar y aprobar las acciones que el plugin propone antes de su ejecucion.</p>
        <p>Los agentes utilizan modelos de lenguaje de gran tamano (LLM) que pueden generar contenido incorrecto, incompleto o inadecuado. Las salidas del plugin deben tratarse como sugerencias que requieren revision humana, no como resultados definitivos.</p>
        <p>El uso de este plugin esta sujeto a la <a href="https://github.com/686f6c61/alfred-dev/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">licencia MIT</a> del proyecto.</p>
      `,
    },
  },
};

export default data;
