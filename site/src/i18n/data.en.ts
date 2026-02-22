/**
 * English content data for the Alfred Dev landing page.
 *
 * All values have been translated from the Spanish original (data.es.ts).
 * SVG icon paths, CSS colours, URLs and commands remain identical to
 * the source file. Only user-facing text has been localised.
 *
 * @module i18n/data.en
 */

import type { PageData } from '../types/index';

const data: PageData = {

  // ----------------------------------------------------------------
  // Meta
  // ----------------------------------------------------------------

  meta: {
    title: 'Alfred Dev - Claude Code Plugin with 15 Engineering Agents',
    description: 'Claude Code plugin: 15 specialised agents, 56 skills, persistent memory and quality gates. From idea to production with TDD, security and compliance.',
    canonical: 'https://alfred-dev.com/en/',
    locale: 'en_US',
    og: {
      type: 'website',
      title: 'Alfred Dev - Claude Code Plugin with 15 Engineering Agents',
      description: '15 specialised agents, 56 skills, persistent memory and quality gates. Automated software engineering for Claude Code.',
      url: 'https://alfred-dev.com/en/',
      siteName: 'Alfred Dev',
      locale: 'en_US',
      image: 'https://alfred-dev.com/screenshots/dashboard-estado.webp',
      imageWidth: 1470,
      imageHeight: 759,
      imageType: 'image/webp',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Alfred Dev - Claude Code Plugin with 15 Engineering Agents',
      description: '15 specialised agents, 56 skills, persistent memory and quality gates. From idea to production.',
      image: 'https://alfred-dev.com/screenshots/dashboard-estado.webp',
    },
  },

  // ----------------------------------------------------------------
  // Navigation
  // ----------------------------------------------------------------

  nav: [
    {
      href: '#agentes',
      label: 'Agents',
      svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    },
    {
      href: '#dashboard',
      label: 'Dashboard',
      svgContent: '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><path d="M8 21h8"/><path d="M12 17v4"/>',
    },
    {
      href: '#flujos',
      label: 'Workflows',
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
      label: 'Usage',
      svgContent: '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>',
    },
    {
      href: '#memoria',
      label: 'Memory',
      svgContent: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
    },
    {
      href: '#instalar',
      label: 'Install',
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
    titleHtml: 'Your development<br>teammates in one <em>plugin</em>',
    platformHtml: 'for <span style="color: var(--blue);">Claude Code</span> and <span style="color: var(--gold);">OpenCode</span> <span style="font-size: 13px; opacity: 0.7;">(in development)</span>',
    subtitle: '15 specialised agents with their own personality. 8 core, 7 optional that you activate per project. Persistent memory, quality gates, 56 skills, from idea to production.',
    ctas: [
      {
        label: 'macOS / Linux',
        command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash',
        ariaLabel: 'Copy installation command for macOS and Linux',
      },
      {
        label: 'Windows',
        command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex',
        ariaLabel: 'Copy installation command for Windows',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Stats
  // ----------------------------------------------------------------

  stats: [
    { number: 15, label: 'Agents' },
    { number: 56, label: 'Skills' },
    { number: 5, label: 'Workflows' },
    { number: 10, label: 'Commands' },
    { number: 7, label: 'Templates' },
    { number: 7, label: 'Hooks' },
    { number: 18, label: 'Gates' },
  ],

  // ----------------------------------------------------------------
  // Core agents
  // ----------------------------------------------------------------

  coreAgents: {
    header: {
      label: 'The team',
      title: '8 core agents',
      description: 'Each agent has a defined role, its own personality and signature phrases. They work coordinated by Alfred, the head butler. Always active in every workflow.',
    },
    agents: [
      {
        name: 'Alfred',
        model: 'opus',
        alias: 'Head butler',
        role: 'Team orchestrator. Decides which agents to activate, in what order, and evaluates the quality gates between phases.',
        phrase: '"Very well, sir. Allow me to organise that."',
        color: 'var(--blue)',
      },
      {
        name: 'The Problem Finder',
        model: 'opus',
        alias: 'Product Owner',
        role: 'Obsessed with the user\'s problem. PRDs, user stories, acceptance criteria, competitive analysis.',
        phrase: '"Very nice, but what problem does this solve?"',
        color: 'var(--purple)',
      },
      {
        name: 'The Box Drawer',
        model: 'opus',
        alias: 'Architect',
        role: 'Thinks in systems, not lines of code. Mermaid diagrams, ADRs, decision matrices, dependency evaluation.',
        phrase: '"If it doesn\'t fit in a diagram, it\'s too complex."',
        color: 'var(--green)',
      },
      {
        name: 'The Craftsman',
        model: 'opus',
        alias: 'Senior Dev',
        role: 'Pragmatic, test-first. Strict TDD, refactoring, atomic commits. Chronic allergy to clever code.',
        phrase: '"Test first. Always test first."',
        color: 'var(--orange)',
      },
      {
        name: 'The Paranoid',
        model: 'opus',
        alias: 'Security Officer',
        role: 'Distrustful by default. OWASP Top 10, GDPR/NIS2/CRA compliance, dependency auditing, threat modelling, SBOM.',
        phrase: '"Did you validate that input? No, seriously."',
        color: 'var(--red)',
      },
      {
        name: 'The Breaker',
        model: 'sonnet',
        alias: 'QA Engineer',
        role: 'His mission is to prove the code doesn\'t work. Test plans, code review, exploratory testing, regression.',
        phrase: '"That edge case you didn\'t consider? Found it."',
        color: 'var(--red)',
      },
      {
        name: 'The Plumber',
        model: 'sonnet',
        alias: 'DevOps Engineer',
        role: 'Invisible infrastructure is well-done infrastructure. Docker, CI/CD, deploy, monitoring. All automated.',
        phrase: '"If you deploy it manually, you\'re deploying it wrong."',
        color: 'var(--cyan)',
      },
      {
        name: 'The Translator',
        model: 'sonnet',
        alias: 'Tech Writer',
        role: 'If it\'s not documented, it doesn\'t exist. API docs, user guides, architecture, changelogs, release notes.',
        phrase: '"I\'ve seen graves with more information than this README."',
        color: 'var(--white)',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Optional agents
  // ----------------------------------------------------------------

  optionalAgents: {
    header: {
      label: 'Extensible',
      labelColor: 'var(--gold)',
      title: '7 optional agents',
      description: 'Specialised roles you activate according to your project\'s needs. Alfred analyses your stack and suggests which to enable. Managed with <strong style="color: var(--blue);">/alfred config</strong>.',
    },
    agents: [
      {
        name: 'The Data Plumber',
        model: 'sonnet',
        alias: 'Data Engineer',
        role: 'Schema design, migrations with mandatory rollback, query optimisation. If there\'s a database, there\'s work.',
        phrase: '"A migration without rollback is a one-way ticket."',
        color: 'var(--orange)',
      },
      {
        name: 'The User Advocate',
        model: 'sonnet',
        alias: 'UX Reviewer',
        role: 'WCAG 2.1 AA audit, Nielsen heuristics, flow review. What\'s obvious to you isn\'t obvious to the user.',
        phrase: '"If the user needs a manual, you\'ve failed."',
        color: '#ff69b4',
      },
      {
        name: 'The Stopwatch',
        model: 'sonnet',
        alias: 'Performance Engineer',
        role: 'Profiling, benchmarks with real statistics (p50, p95, p99), bundle analysis. Measure before and after, always.',
        phrase: '"Without numbers there\'s no optimisation, just superstition."',
        color: 'var(--purple)',
      },
      {
        name: 'The Gatekeeper',
        model: 'sonnet',
        alias: 'GitHub Manager',
        role: 'Repository configuration, branch protection, PRs, releases, issue templates. All via gh CLI, no AI mentions.',
        phrase: '"A repo without branch protection is Russian roulette."',
        color: 'var(--text-muted)',
      },
      {
        name: 'The Tracker',
        model: 'sonnet',
        alias: 'SEO Specialist',
        role: 'Meta tags, JSON-LD structured data, Core Web Vitals, Lighthouse. If Google can\'t find it, it doesn\'t exist.',
        phrase: '"A wrong canonical and you\'ve got duplicate content."',
        color: 'var(--green)',
      },
      {
        name: 'The Quill',
        model: 'sonnet',
        alias: 'Copywriter',
        role: 'Text review, effective CTAs, tone guide. Impeccable spelling as absolute priority. No infomercials.',
        phrase: '"If you write \'aplication\' without the double p, don\'t publish."',
        color: 'var(--cyan)',
      },
      {
        name: 'The Librarian',
        model: 'sonnet',
        alias: 'Project memory',
        role: 'Answers historical queries about project decisions, commits and iterations. Always cites sources with verifiable IDs: [D#id], [C#sha], [I#id].',
        phrase: '"According to decision D#42 from February 15th, Redis was discarded due to latency."',
        color: '#c9a96e',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Dashboard
  // ----------------------------------------------------------------

  dashboard: {
    sectionLabel: 'Alpha Phase',
    title: 'Real-time dashboard',
    descriptionHtml: 'The web dashboard shows the full project status without interfering with the terminal. Phases, agents, decisions, commits and timeline updated via WebSocket. Launched with <code style="font-family: var(--font-mono); font-size: 14px; color: var(--cyan);">/alfred gui</code> and works in any browser.',
    heroImage: {
      src: '/screenshots/dashboard-estado.webp',
      alt: 'Project status view in the Alfred Dev dashboard',
      caption: 'Project status',
    },
    gridImages: [
      {
        src: '/screenshots/dashboard-timeline.webp',
        alt: 'Event timeline in the Alfred Dev dashboard',
        caption: 'Event timeline',
      },
      {
        src: '/screenshots/dashboard-decisiones.webp',
        alt: 'Technical decisions in the Alfred Dev dashboard',
        caption: 'Technical decisions',
      },
      {
        src: '/screenshots/dashboard-agentes.webp',
        alt: 'Agent control in the Alfred Dev dashboard',
        caption: 'Agent control',
      },
      {
        src: '/screenshots/dashboard-memoria.webp',
        alt: 'Memory explorer in the Alfred Dev dashboard',
        caption: 'Memory explorer',
      },
      {
        src: '/screenshots/dashboard-commits.webp',
        alt: 'Commit history in the Alfred Dev dashboard',
        caption: 'Commit history',
      },
      {
        src: '/screenshots/dashboard-marcados.webp',
        alt: 'Pinned items in the Alfred Dev dashboard',
        caption: 'Pinned items',
      },
    ],
    features: [
      {
        title: '7 views',
        description: 'Status, timeline, decisions, agents, memory, commits and pinned items.',
      },
      {
        title: 'Real-time',
        description: 'WebSocket with automatic reconnection and exponential backoff.',
      },
      {
        title: 'No dependencies',
        description: 'HTML + vanilla JS, Python asyncio server, no external frameworks.',
      },
      {
        title: 'Fail-open',
        description: 'If the GUI fails, Alfred works exactly the same as without it.',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Workflows
  // ----------------------------------------------------------------

  workflows: {
    header: {
      label: 'Workflows',
      title: '5 workflows, 16 phases',
      description: 'Each workflow has sequential phases with quality gates between them. If a gate fails, the workflow doesn\'t advance. Optional agents integrate automatically into their corresponding phases.',
    },
    flows: [
      {
        command: '/alfred feature',
        subtitle: 'Full or partial cycle',
        description: '6 phases: product, architecture, TDD development, quality + security, documentation, delivery. You can start from any phase.',
        stages: ['Product', 'Architecture', 'Development', 'Quality + Security', 'Documentation', 'Delivery'],
      },
      {
        command: '/alfred fix',
        subtitle: 'Quick fix',
        description: 'Root cause diagnosis, TDD fix (test that reproduces the bug first), QA + security validation.',
        stages: ['Diagnosis', 'TDD Fix', 'Validation'],
      },
      {
        command: '/alfred spike',
        subtitle: 'Investigation',
        description: 'Technical exploration with no commitment: prototypes, benchmarks, evaluation of alternatives. Findings document.',
        stages: ['Investigation', 'Findings'],
      },
      {
        command: '/alfred ship',
        subtitle: 'Deployment',
        description: 'Parallel final audit, release documentation, packaging with semantic versioning, production deployment.',
        stages: ['Audit', 'Documentation', 'Packaging', 'Deployment'],
      },
      {
        command: '/alfred audit',
        subtitle: 'Audit',
        description: '4 agents working in parallel: quality, security, architecture and documentation. Consolidated report with priorities.',
        stages: ['Parallel audit'],
      },
    ],
  },

  // ----------------------------------------------------------------
  // Quality gates
  // ----------------------------------------------------------------

  gates: {
    header: {
      label: 'Quality gates',
      title: 'What Alfred works towards',
      description: 'Alfred doesn\'t give absolute guarantees, but actively works to meet these objectives in every workflow. If it detects something is off, it stops progress and alerts you.',
    },
    coreLabel: 'Core -- always active',
    core: [
      { text: 'Tries to ensure tests are green before advancing to quality' },
      { text: 'Runs QA and security review before proposing deployment' },
      { text: 'Seeks a green CI/CD pipeline as a delivery requirement' },
      { text: 'Asks for user PRD approval before designing' },
      { text: 'The security officer reviews the design before development' },
      { text: 'Reviews OWASP vulnerabilities and alerts on critical or high findings' },
      { text: 'Audits dependencies for known CVEs' },
      { text: 'Checks GDPR, NIS2 and CRA compliance aspects according to context' },
      { text: 'Monitors every file write looking for secrets, API keys or tokens' },
      { text: 'Detects missing accents in Spanish when writing or editing files' },
    ],
    optionalLabel: 'Optional -- when you activate them',
    optional: [
      { text: 'Analyses code with SonarQube (installs Docker if missing, with your permission)', optional: true },
      { text: 'Requires rollback in every database migration before executing it', optional: true },
      { text: 'Verifies WCAG 2.1 AA accessibility before approving the interface', optional: true },
      { text: 'Measures performance with real metrics (p50, p95, p99) before and after', optional: true },
      { text: 'Configures branch protection on main and requires PR with approval', optional: true },
      { text: 'Monitors Core Web Vitals (LCP, INP, CLS) and alerts if out of threshold', optional: true },
      { text: 'Reviews meta tags, structured data and SEO crawlability before publishing', optional: true },
      { text: 'Validates spelling, tone and consistency of interface texts', optional: true },
    ],
  },

  // ----------------------------------------------------------------
  // Skills
  // ----------------------------------------------------------------

  skills: {
    header: {
      label: 'Capabilities',
      title: '56 skills across 13 domains',
      description: 'Each skill is a specific ability that agents execute. The original 7 domains are expanded with 6 new ones for the optional agents.',
    },
    domains: [
      {
        name: 'Product',
        skills: [
          { name: 'write-prd', description: 'Complete PRD with stories and criteria' },
          { name: 'user-stories', description: 'User story decomposition' },
          { name: 'acceptance-criteria', description: 'Given/When/Then criteria' },
          { name: 'competitive-analysis', description: 'Alternatives analysis' },
        ],
      },
      {
        name: 'Architecture',
        skills: [
          { name: 'write-adr', description: 'Architecture Decision Records' },
          { name: 'choose-stack', description: 'Stack decision matrix' },
          { name: 'design-system', description: 'Design with Mermaid diagrams' },
          { name: 'evaluate-dependencies', description: 'Dependency audit' },
        ],
      },
      {
        name: 'Development',
        skills: [
          { name: 'tdd-cycle', description: 'Red-green-refactor cycle' },
          { name: 'explore-codebase', description: 'Code exploration' },
          { name: 'refactor', description: 'Guided refactoring' },
          { name: 'code-review-response', description: 'Code review response' },
        ],
      },
      {
        name: 'Security',
        skills: [
          { name: 'threat-model', description: 'STRIDE modelling' },
          { name: 'dependency-audit', description: 'CVEs, licences, versions' },
          { name: 'security-review', description: 'OWASP Top 10' },
          { name: 'compliance-check', description: 'GDPR, NIS2, CRA' },
          { name: 'sbom-generate', description: 'Software Bill of Materials' },
          { name: 'dependency-update', description: 'Secure dependency updates' },
        ],
      },
      {
        name: 'Quality',
        skills: [
          { name: 'test-plan', description: 'Risk-based test plans' },
          { name: 'code-review', description: 'Quality review' },
          { name: 'exploratory-test', description: 'Exploratory testing' },
          { name: 'regression-check', description: 'Regression analysis' },
          { name: 'sonarqube', description: 'SonarQube + Docker analysis' },
          { name: 'spelling-check', description: 'Spelling verification (accents)' },
        ],
      },
      {
        name: 'DevOps',
        skills: [
          { name: 'dockerize', description: 'Multi-stage Dockerfile' },
          { name: 'ci-cd-pipeline', description: 'GitHub Actions, GitLab CI' },
          { name: 'deploy-config', description: 'Vercel, Railway, Fly, AWS, K8s' },
          { name: 'monitoring-setup', description: 'Logging, alerts, tracking' },
        ],
      },
      {
        name: 'Documentation',
        skills: [
          { name: 'api-docs', description: 'Endpoints, params, examples' },
          { name: 'architecture-docs', description: 'System overview' },
          { name: 'user-guide', description: 'Installation, usage, troubleshooting' },
          { name: 'changelog', description: 'Keep a Changelog' },
          { name: 'project-docs', description: 'Full documentation in docs/' },
          { name: 'glossary', description: 'Project linguistic corpus' },
          { name: 'readme-review', description: 'README audit' },
          { name: 'onboarding-guide', description: 'New developer guide' },
          { name: 'migration-guide', description: 'Version migration' },
        ],
      },
      {
        name: 'Data',
        optional: true,
        skills: [
          { name: 'schema-design', description: 'Normalised schema design' },
          { name: 'migration-plan', description: 'Migrations with rollback' },
          { name: 'query-optimization', description: 'Optimisation with EXPLAIN' },
        ],
      },
      {
        name: 'UX',
        optional: true,
        skills: [
          { name: 'accessibility-audit', description: 'Full WCAG 2.1 AA' },
          { name: 'usability-heuristics', description: 'Nielsen\'s 10 heuristics' },
          { name: 'flow-review', description: 'User flow analysis' },
        ],
      },
      {
        name: 'Performance',
        optional: true,
        skills: [
          { name: 'profiling', description: 'CPU and memory per runtime' },
          { name: 'benchmark', description: 'Benchmarks with p50, p95, p99' },
          { name: 'bundle-size', description: 'Bundle analysis and reduction' },
        ],
      },
      {
        name: 'GitHub',
        optional: true,
        skills: [
          { name: 'repo-setup', description: 'Full repo configuration' },
          { name: 'pr-workflow', description: 'Well-documented PRs' },
          { name: 'release', description: 'Releases with semantic versioning' },
          { name: 'issue-templates', description: 'YAML issue templates' },
        ],
      },
      {
        name: 'SEO',
        optional: true,
        skills: [
          { name: 'meta-tags', description: 'Title, description, Open Graph' },
          { name: 'structured-data', description: 'JSON-LD for schema.org' },
          { name: 'lighthouse-audit', description: 'Core Web Vitals and metrics' },
        ],
      },
      {
        name: 'Marketing',
        optional: true,
        skills: [
          { name: 'copy-review', description: 'Public text review' },
          { name: 'cta-writing', description: 'Effective CTAs without infomercials' },
          { name: 'tone-guide', description: 'Brand tone guide' },
        ],
      },
    ],
  },

  // ----------------------------------------------------------------
  // Infrastructure
  // ----------------------------------------------------------------

  infra: {
    header: {
      label: 'Under the hood',
      title: 'Hooks, templates and core',
      description: 'The infrastructure that powers the team: hooks that watch, templates that standardise and a core that orchestrates.',
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
          { name: 'test-plan.md', label: 'Test plan' },
          { name: 'threat-model.md', label: 'STRIDE modelling' },
          { name: 'sbom.md', label: 'Bill of Materials' },
          { name: 'changelog-entry.md', label: 'Changelog entry' },
          { name: 'release-notes.md', label: 'Release notes' },
        ],
      },
      {
        title: '4 core modules',
        items: [
          { name: 'orchestrator.py', label: 'Workflows, sessions, gates' },
          { name: 'personality.py', label: 'Personality engine' },
          { name: 'config_loader.py', label: 'Config and stack detection' },
          { name: 'memory.py', label: 'SQLite persistent memory' },
        ],
        footnote: '114 passing',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Commands
  // ----------------------------------------------------------------

  commands: {
    header: {
      label: 'Interface',
      title: '10 commands',
      description: 'Everything is controlled from the Claude Code command line. One prefix, one verb, one description.',
    },
    list: [
      {
        command: '/alfred',
        description: 'Contextual assistant: detects the stack and active session, asks what you need and launches the appropriate workflow.',
      },
      {
        command: '/alfred feature',
        description: 'Full 6-phase cycle or from any phase you specify. Alfred asks and adapts: "from development", "documentation only", "full cycle".',
      },
      {
        command: '/alfred fix',
        description: 'Fix a bug with a 3-phase flow: diagnosis, TDD fix, validation.',
      },
      {
        command: '/alfred spike',
        description: 'Exploratory investigation with no commitment: prototypes, benchmarks, conclusions.',
      },
      {
        command: '/alfred ship',
        description: 'Prepare release: final audit, documentation, packaging, deployment.',
      },
      {
        command: '/alfred audit',
        description: 'Full audit with 4 agents in parallel: quality, security, architecture, documentation.',
      },
      {
        command: '/alfred config',
        description: 'Configure autonomy, stack, compliance, personality, <strong style="color: var(--gold);">optional agents</strong> and <strong style="color: var(--gold);">persistent memory</strong>. Includes contextual discovery: Alfred analyses your project and suggests which agents to enable.',
      },
      {
        command: '/alfred status',
        description: 'Active session: current phase, completed phases with duration, pending gate and active agent.',
      },
      {
        command: '/alfred update',
        description: 'Check for a new version, see the release notes and update with one click.',
      },
      {
        command: '/alfred help',
        description: 'Full help for all available commands.',
      },
    ],
    optionalNote: {
      html: '<strong style="color: var(--gold);">Optional agents in workflows:</strong> the 7 optional agents don\'t have their own commands. They are activated with <strong style="color: var(--blue);">/alfred config</strong> and from then on integrate automatically into existing workflows. For example, if you activate the <em>data-engineer</em>, it will participate in the architecture phase of <strong style="color: var(--blue);">/alfred feature</strong>; if you activate the <em>seo-specialist</em>, it will intervene in the quality phase of <strong style="color: var(--blue);">/alfred ship</strong>; if you activate <em>The Librarian</em>, Alfred will consult the decision history before each workflow. Alfred decides when to invoke each agent based on the workflow context.',
    },
  },

  // ----------------------------------------------------------------
  // Stack detection
  // ----------------------------------------------------------------

  stacks: {
    header: {
      label: 'Automatic detection',
      title: 'Adapts to your project',
      description: 'Alfred Dev automatically detects your project\'s technology stack and adapts its artefacts to the actual ecosystem.',
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
  // Use cases
  // ----------------------------------------------------------------

  useCases: {
    header: {
      label: 'In practice',
      labelColor: 'var(--cyan)',
      title: 'How it\'s used',
      description: 'Real usage scenarios step by step. Each case shows the full flow from invocation to result.',
    },
    cases: [
      {
        category: 'Development',
        color: 'var(--blue)',
        background: 'rgba(91,156,245,0.08)',
        title: 'Develop a complete feature',
        command: '/alfred feature push notification system',
        steps: [
          'The product-owner generates the PRD with user stories and acceptance criteria',
          'The architect designs the solution and the security-officer validates the design',
          'The senior-dev implements following strict TDD (red-green-refactor)',
          'QA and security audit in parallel before giving the green light',
          'The tech-writer documents the API and the devops-engineer prepares deployment',
        ],
      },
      {
        category: 'Bug fix',
        color: 'var(--red)',
        background: 'rgba(229,86,79,0.08)',
        title: 'Fix a bug',
        command: '/alfred fix login fails with emails containing accents',
        steps: [
          'The senior-dev reproduces the error and identifies the root cause',
          'Writes a test that fails reproducing the exact bug',
          'Implements the minimal fix that makes the test pass',
          'QA and security validate that no regressions were introduced',
        ],
      },
      {
        category: 'Investigation',
        color: 'var(--purple)',
        background: 'rgba(160,126,232,0.08)',
        title: 'Technical investigation (spike)',
        command: '/alfred spike evaluate migrating from REST to gRPC',
        steps: [
          'The architect and senior-dev explore alternatives with no code commitment',
          'Lightweight proofs of concept are generated to compare performance',
          'An ADR is documented with findings, pros, cons and recommendation',
          'The user decides whether to proceed with implementation or discard it',
        ],
      },
      {
        category: 'Audit',
        color: 'var(--orange)',
        background: 'rgba(232,164,74,0.08)',
        title: 'Audit the project',
        command: '/alfred audit',
        steps: [
          '4 agents work in parallel: QA, security, architecture and documentation',
          'QA looks for logic errors, code smells and test coverage',
          'Security analyses OWASP Top 10, dependencies with CVEs and GDPR/NIS2 compliance',
          'A single report is consolidated with findings prioritised by severity',
        ],
      },
      {
        category: 'Delivery',
        color: 'var(--green)',
        background: 'rgba(78,201,144,0.08)',
        title: 'Prepare a release',
        command: '/alfred ship',
        steps: [
          'Mandatory final audit: QA and security must approve',
          'The tech-writer updates the changelog and generates release notes',
          'The devops-engineer packages, configures the pipeline and verifies the build',
          'Supervised deployment: the user confirms before pushing to production',
        ],
      },
      {
        category: 'Conversational',
        color: 'var(--gold)',
        background: 'rgba(201,169,110,0.08)',
        title: 'Contextual assistant',
        command: '/alfred',
        steps: [
          'Alfred detects the project stack and the active session state',
          'Asks what you need and offers options adapted to the context',
          'Interprets your natural language response and launches the appropriate workflow',
          'You can also say "use the Alfred plugin" at any time',
        ],
      },
      {
        category: 'Quality',
        color: 'var(--red)',
        background: 'rgba(229,86,79,0.08)',
        title: 'SonarQube analysis',
        command: '/alfred audit',
        steps: [
          'QA checks if Docker is installed; if not, installs it itself (with your permission)',
          'Spins up SonarQube with Docker automatically and waits until it\'s ready',
          'Configures the project, runs the scanner and waits for results',
          'Translates findings (bugs, vulnerabilities, code smells) into a report with proposed fixes',
          'Cleans up the container when done: leaves nothing running',
        ],
      },
      {
        category: 'Data',
        color: 'var(--orange)',
        background: 'rgba(232,164,74,0.08)',
        title: 'Design and migrate a database',
        command: '/alfred feature add subscription system with payments',
        steps: [
          'The data-engineer designs the normalised schema with constraints and indices',
          'Generates the migration script with mandatory rollback (forward and back)',
          'The architect validates integration with the ORM and the rest of the stack',
          'The migration is executed, tables are verified and integration tests are run',
        ],
      },
      {
        category: 'GitHub',
        color: 'var(--text-muted)',
        background: 'rgba(110,115,138,0.08)',
        title: 'Configure and publish a repository',
        command: '/alfred ship',
        steps: [
          'The github-manager verifies that gh CLI is installed and authenticated; if not, guides the process',
          'Configures branch protection, labels, issue templates and optimised .gitignore',
          'Creates the PR with structured description, labels and reviewer assignment',
          'Generates the release with semantic versioning, categorised changelog and attached artefacts',
        ],
      },
      {
        category: 'SEO + Copy',
        color: 'var(--green)',
        background: 'rgba(78,201,144,0.08)',
        title: 'Optimise a landing page',
        command: '/alfred audit',
        steps: [
          'The seo-specialist audits meta tags, Open Graph, canonical and JSON-LD structured data',
          'Runs Lighthouse and prioritises improvements by Core Web Vitals impact',
          'The copywriter reviews texts: spelling (accents first), clarity, tone and CTAs',
          'A joint report is generated with fixes ready to apply',
        ],
      },
      {
        category: 'UX',
        color: '#ff69b4',
        background: 'rgba(255,105,180,0.08)',
        title: 'Accessibility and usability audit',
        command: '/alfred audit',
        steps: [
          'The ux-reviewer runs a WCAG 2.1 AA audit across the 4 principles (perceivable, operable, understandable, robust)',
          'Applies Nielsen\'s 10 heuristics to the user\'s main flow',
          'Identifies friction points, edge cases and unnecessary steps in each flow',
          'Generates a report with severity (0-4) and improvement proposal for each finding',
        ],
      },
      {
        category: 'Performance',
        color: 'var(--purple)',
        background: 'rgba(160,126,232,0.08)',
        title: 'Optimise performance',
        command: '/alfred spike the API takes 3 seconds to respond',
        steps: [
          'The performance-engineer runs CPU and memory profiling to locate bottlenecks',
          'Analyses slow queries with EXPLAIN and proposes indices or restructuring',
          'Runs benchmarks before and after with real metrics (p50, p95, p99)',
          'If there\'s a frontend, analyses bundle size and proposes tree-shaking or code splitting',
        ],
      },
      {
        category: 'Automatic',
        color: 'var(--cyan)',
        background: 'rgba(78,201,201,0.08)',
        title: 'Background protection',
        wide: true,
        description: 'Without running any command, Alfred automatically monitors your work session through hooks that trigger on every relevant operation.',
        steps: [
          'Secret guard -- blocks writing API keys, tokens or passwords in code',
          'Quality gate -- verifies tests pass after every significant change',
          'Dependency watch -- detects new libraries and notifies the security auditor',
          'Spelling guard -- detects Spanish words missing accents when writing or editing files',
          'Memory capture -- automatically records workflow events in persistent memory',
          'Commit capture -- detects every git commit and records SHA, author and files in memory',
          'Protected context -- critical decisions survive context compaction',
        ],
      },
    ],
  },

  // ----------------------------------------------------------------
  // Persistent memory
  // ----------------------------------------------------------------

  memory: {
    sectionLabel: 'Since v0.2.0 -- Improved in v0.2.3',
    title: 'Persistent memory',
    descriptionHtml: 'Alfred Dev remembers decisions, commits and iterations between sessions. Memory is stored in a local SQLite database inside each project, with no external dependencies or remote services. Since v0.2.3: tags, status and relationships between decisions, auto-capture of commits, advanced filters and export/import.',
    traceability: {
      title: 'Full traceability',
      descriptionHtml: 'Each decision is linked to the problem that originated it, the commits that implemented it and the validation that confirmed it. Everything referenceable with verifiable IDs.',
      nodes: [
        { label: 'Problem', color: 'var(--purple)', background: 'rgba(160,126,232,0.08)', borderColor: 'rgba(160,126,232,0.15)' },
        { label: 'Decision [D#id]', color: 'var(--gold)', background: 'rgba(201,169,110,0.08)', borderColor: 'rgba(201,169,110,0.15)' },
        { label: 'Commit [C#sha]', color: 'var(--green)', background: 'rgba(78,201,144,0.08)', borderColor: 'rgba(78,201,144,0.15)' },
        { label: 'Validation', color: 'var(--blue)', background: 'rgba(91,156,245,0.08)', borderColor: 'rgba(91,156,245,0.15)' },
      ],
    },
    cards: [
      {
        title: 'Local database',
        descriptionHtml: 'SQLite with WAL mode for concurrent writes. Stores decisions, commits, iterations and events in <code>.claude/alfred-memory.db</code> inside each project. 0600 permissions by default.',
      },
      {
        title: 'Smart search',
        descriptionHtml: 'Full-text search with FTS5 when available, with automatic fallback to LIKE for environments without the FTS extension. Searches decision titles, reasons, discarded alternatives and commit messages.',
      },
      {
        title: 'Automatic capture',
        descriptionHtml: 'Two complementary hooks capture everything automatically: <code>memory-capture.py</code> records workflow events (iterations, phases) and <code>commit-capture.py</code> detects every <code>git commit</code> and records SHA, message, author and affected files.',
      },
      {
        title: 'Integrated MCP server',
        descriptionHtml: '15 tools accessible from any agent via MCP stdio: search, record, query iterations, statistics, iteration management, decision lifecycle, integrity validation, export/import. No external dependencies.',
      },
      {
        title: 'Session context',
        descriptionHtml: 'At the start of each session, relevant decisions are injected: if there\'s an active iteration, those from that iteration; if not, the latest 5 globally. A PreCompact hook protects these decisions during context compaction.',
      },
      {
        title: 'Built-in security',
        descriptionHtml: 'Secret sanitisation with the same patterns as secret-guard.sh: API keys, tokens, JWT, connection strings and private keys are redacted before storage. 0600 permissions on the database file.',
      },
    ],
    librarian: {
      title: 'The Librarian',
      subtitle: 'Optional agent -- project memory',
      descriptionHtml: [
        'The Librarian is the agent that answers historical queries about the project. Unlike other agents that work on current code, this one focuses on the <em>why</em> of past decisions: what was decided, when, what alternatives were discarded and which commits implemented each decision. Since v0.2.3 it also manages the decision lifecycle (status, tags, relationships), validates memory integrity and allows exporting decisions to Markdown or importing from Git and ADRs.',
        'It has an unbreakable rule: <strong>always cite sources</strong>. Every statement includes verifiable references with format <code>[D#42]</code> for decisions, <code>[C#a1b2c3d]</code> for commits and <code>[I#7]</code> for iterations. If it doesn\'t find evidence, it says so instead of making things up.',
      ],
      example: {
        label: 'Example query:',
        question: '> Why did we use SQLite instead of PostgreSQL for memory?',
        answerHtml: 'SQLite was chosen because the requirement was zero external dependencies <span style="color: var(--gold);">[D#12]</span>. The PostgreSQL alternative was discarded because it required an external service running <span style="color: var(--gold);">[D#12, alternatives]</span>. The implementation was done in commit <span style="color: var(--green);">[C#1833e83]</span> within iteration <span style="color: var(--blue);">[I#3]</span>.',
      },
      activationHtml: '<strong>Activation:</strong> enabled from <strong style="color: var(--blue);">/alfred config</strong> in the persistent memory section. Once active, Alfred automatically delegates historical queries that arise during any workflow.',
    },
    faq: [
      {
        question: 'Where is the data stored?',
        answerHtml: 'In the file <code>.claude/alfred-memory.db</code> inside each project root. It\'s a local SQLite file; nothing is sent to external services. Add it to <code>.gitignore</code> if you don\'t want to version it.',
      },
      {
        question: 'Does memory activate automatically?',
        answerHtml: 'No. Activation is explicitly optional. It\'s enabled from <strong>/alfred config</strong> in the memory section. If you don\'t activate it, no database is created and nothing is captured.',
      },
      {
        question: 'What about secrets?',
        answerHtml: 'All content goes through the same sanitisation used by the secret-guard.sh hook before being stored. API keys, tokens, JWT, connection strings and private key headers are automatically redacted. The database file has 0600 permissions (read/write only for the owner).',
      },
      {
        question: 'Can I delete the memory?',
        answerHtml: 'Yes. Simply delete the <code>.claude/alfred-memory.db</code> file. You can also deactivate memory from <strong>/alfred config</strong>: existing data is preserved but stops being queried and no new events are captured.',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Installation
  // ----------------------------------------------------------------

  install: {
    sectionLabel: 'Getting started',
    title: 'Installation',
    description: 'One command in the terminal and you\'re set. Compatible with macOS, Linux and Windows. The installer is idempotent: running it again updates without conflicts.',
    tabs: [
      {
        id: 'macos',
        label: 'macOS',
        command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash',
        requirementsHtml: '<strong>Requirements:</strong> git, Python 3.10+, Claude Code installed.<br>After installation, restart Claude Code and run <strong>/alfred help</strong>.',
      },
      {
        id: 'linux',
        label: 'Linux',
        command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash',
        requirementsHtml: '<strong>Requirements:</strong> git, Python 3.10+, Claude Code installed.<br>After installation, restart Claude Code and run <strong>/alfred help</strong>.',
      },
      {
        id: 'windows',
        label: 'Windows',
        command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex',
        requirementsHtml: '<strong>Requirements:</strong> git, PowerShell 5.1+ (pre-installed on Windows 10/11), Claude Code installed.<br>Python not required. After installation, restart Claude Code and run <strong>/alfred help</strong>.<br>Alternative: you can also use the bash installer with WSL or Git Bash.',
      },
    ],
    uninstall: {
      title: 'Uninstallation',
      description: 'To completely remove Alfred Dev, run the uninstaller for your platform. It cleans up all plugin registries and directories.',
      cards: [
        {
          title: 'macOS / Linux',
          command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash',
          ariaLabel: 'Copy uninstallation command for macOS and Linux',
        },
        {
          title: 'Windows (PowerShell)',
          command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.ps1 | iex',
          ariaLabel: 'Copy uninstallation command for Windows',
        },
      ],
    },
    update: {
      title: 'Update',
      descriptionHtml: 'From Claude Code, run <strong style="color: var(--blue);">/alfred update</strong> to check for a new version. If available, Alfred shows the release notes and asks if you want to update. You can also re-run the installer: it\'s idempotent.',
    },
  },

  // ----------------------------------------------------------------
  // Configuration
  // ----------------------------------------------------------------

  config: {
    sectionLabel: 'Customisation',
    title: 'Per-project configuration',
    descriptionHtml: 'Each project has its own configuration file at <code>.claude/alfred-dev.local.md</code>. Managed with <strong>/alfred config</strong>, which includes contextual discovery of optional agents and persistent memory activation.',
    yamlExample: `---
autonomy:
  product: interactive
  architecture: interactive
  development: semi-autonomous
  security: autonomous
  quality: semi-autonomous
  documentation: autonomous
  devops: semi-autonomous

optional_agents:
  data-engineer: true
  ux-reviewer: false
  github-manager: true
  librarian: true

memory:
  enabled: true
  capture_decisions: true
  capture_commits: true
  retention_days: 365

personality:
  sarcasm_level: 3
  celebrate_victories: true
  call_out_bad_practices: true
---`,
    blocks: [
      {
        title: 'Autonomy per phase',
        descriptionHtml: 'Control how much intervention you need at each workflow phase. <strong>Interactive</strong> asks for approval at every step, <strong>semi-autonomous</strong> proceeds on its own but consults you on key decisions, and <strong>autonomous</strong> executes without interruptions.',
      },
      {
        title: 'Optional agents',
        descriptionHtml: 'Activate only the ones you need. Alfred analyses your project and suggests which to enable based on the detected stack. They can be changed at any time without reinstalling.',
      },
      {
        title: 'Persistent memory',
        descriptionHtml: 'Optional activation. Configure what is captured (decisions, commits), retention in days and the Librarian\'s behaviour.',
      },
      {
        title: 'Personality',
        descriptionHtml: 'Sarcasm level goes from 0 (formal professional) to 5 (sharp with affection). Celebrations and bad-practice warnings are toggled separately.',
      },
    ],
  },

  // ----------------------------------------------------------------
  // FAQ
  // ----------------------------------------------------------------

  faq: {
    header: {
      label: 'Frequently asked questions',
      title: 'FAQ',
    },
    items: [
      {
        svgContent: '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
        question: 'Does it work on Windows?',
        answerHtml: 'Yes. Alfred Dev has a native PowerShell installer for Windows 10/11. You can also use the bash installer through WSL (Windows Subsystem for Linux) or Git Bash. The only dependency on Windows is git; python3 is not required.',
      },
      {
        svgContent: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
        question: 'What dependencies does it need?',
        answerHtml: 'On macOS and Linux: <strong>git</strong> and <strong>python3</strong>. Both are usually pre-installed or easy to install with the system package manager.<br><br>On Windows: just <strong>git</strong>. PowerShell handles JSON natively, so python3 is not needed. PowerShell 5.1+ comes pre-installed on Windows 10/11.',
      },
      {
        svgContent: '<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
        question: 'How do I update the plugin?',
        answerHtml: 'Run <strong>/alfred update</strong> inside Claude Code. The command queries GitHub, compares versions and shows the release notes if a new version is available. You can also re-run the installer: it overwrites the previous version without conflicts.',
      },
      {
        svgContent: '<path d="M19.439 5.56a5.018 5.018 0 0 0-7.09 0L11 6.91l-1.35-1.35a5.013 5.013 0 0 0-7.09 7.09L11 21.09l8.44-8.44a5.013 5.013 0 0 0 0-7.09z"/>',
        question: 'Is it compatible with other Claude Code plugins?',
        answerHtml: 'Yes. Alfred Dev coexists without conflicts with other installed plugins. It uses its own namespace (<code>alfred-dev</code>) and doesn\'t interfere with other plugins\' configuration.',
      },
      {
        svgContent: '<circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6M4.22 4.22l4.24 4.24m7.08 7.08l4.24 4.24M1 12h6m6 0h6M4.22 19.78l4.24-4.24m7.08-7.08l4.24-4.24"/>',
        question: 'What are optional agents?',
        answerHtml: 'They are 7 specialised agents you can activate based on your project\'s needs: <strong>data-engineer</strong> (databases), <strong>ux-reviewer</strong> (accessibility and usability), <strong>performance-engineer</strong> (performance), <strong>github-manager</strong> (repository management), <strong>seo-specialist</strong> (web positioning), <strong>copywriter</strong> (text and spelling) and <strong>The Librarian</strong> (persistent memory: historical queries about project decisions, commits and iterations).<br><br>Alfred analyses your project and suggests which to activate. You can also manage them manually with <strong>/alfred config</strong>. They are activated or deactivated without reinstalling anything.',
      },
      {
        svgContent: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
        question: 'How many skills does it have in total?',
        answerHtml: '56 skills distributed across 13 domains. The original 7 domains (product, architecture, development, security, quality, DevOps, documentation) cover the standard lifecycle. The 6 new ones (data, UX, performance, GitHub, SEO, marketing) correspond to the optional agents. Existing domains have also been expanded: documentation went from 4 to 9 skills, security from 5 to 6, and quality from 4 to 6.',
      },
      {
        svgContent: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
        question: 'What is persistent memory?',
        answerHtml: 'It\'s a local SQLite database that stores each project\'s decisions, commits and iterations. Optionally activated from <strong>/alfred config</strong>. Once active, Alfred automatically records workflow events and the <strong>Librarian</strong> agent can answer historical queries like "why was this architecture chosen" or "what was done in the last iteration", always citing sources. Data stays within the project: everything is kept in <code>.claude/alfred-memory.db</code>.',
      },
      {
        svgContent: '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
        question: 'How much does it cost?',
        answerHtml: 'Nothing. Alfred Dev is free software under the MIT licence. You can use, modify and distribute it without restrictions. The source code is on GitHub (github.com/686f6c61/alfred-dev).',
      },
      {
        svgContent: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        question: 'What language does Alfred respond in?',
        answerHtml: 'Spanish (Spain) by default: both responses and code comments, commits and generated documentation. You can adjust this behaviour with <strong>/alfred config</strong>.',
      },
      {
        svgContent: '<polyline points="20 6 9 17 4 12"/>',
        question: 'What versions of Claude Code does it support?',
        answerHtml: 'Any version of Claude Code that supports the plugin system. If you can install plugins from the command line, Alfred Dev will work. There is no specific minimum version requirement.',
      },
      {
        svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        question: 'Can I contribute to the project?',
        answerHtml: 'Yes. Alfred Dev is free software under the MIT licence. You can report bugs, propose improvements or submit pull requests on the GitHub repository (github.com/686f6c61/alfred-dev/issues). Code, documentation, translation contributions or simply reporting issues are welcome.',
      },
      {
        svgContent: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
        question: 'Do the agents consume additional tokens?',
        answerHtml: 'Yes, like any interaction with Claude. Agents are system instructions that guide responses, so they consume context proportional to their complexity. In practice, the additional cost is moderate: agent system prompts are optimised to take up as little space as possible without losing precision. Optional agents are only loaded if you activate them, so the base context is that of the 8 core agents.',
      },
      {
        svgContent: '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
        question: 'Can I use Alfred in a monorepo?',
        answerHtml: 'Alfred detects the stack of the current working directory, not the repository root. If you run Claude Code from a monorepo root, it will detect all languages present. If you run it from a specific package, it will focus on that package. Persistent memory is per working directory, so each package can have its own decision database if you configure it that way.',
      },
      {
        svgContent: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
        question: 'What happens if a quality gate fails?',
        answerHtml: 'The workflow stops at the current phase and Alfred explains what failed: failing tests, detected vulnerabilities, incomplete documentation or whatever applies. You have three options: fix the issue and retry the gate, ask Alfred to help resolve it (for example, with <strong>/alfred fix</strong> if it\'s a bug), or continue manually accepting the risk. Alfred never advances silently if a gate fails.',
      },
      {
        svgContent: '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
        question: 'Does it work with OpenCode?',
        answerHtml: 'It\'s in development. OpenCode is an open-source terminal-based code editor that shares the plugin architecture with Claude Code. Alfred Dev is being adapted to be compatible with both environments. The OpenCode version will be announced in the repository when it\'s ready for general use.',
      },
    ],
  },

  // ----------------------------------------------------------------
  // Changelog
  // ----------------------------------------------------------------

  changelog: [
    {
      version: '0.3.1',
      date: '2026-02-23',
      fixed: [
        '<strong>Robust WebSocket frame reading</strong> -- rewritten with <code>readexactly()</code> to eliminate disconnections from TCP fragmentation.',
        '<strong>Cross-thread SQLite connection</strong> -- added <code>check_same_thread=False</code> to avoid errors in Python 3.12+.',
        '<strong>get_full_state() consistency</strong> -- all queries use the same polling connection.',
        '<strong>Pinned items polling</strong> -- pinned elements now propagate in real time.',
        '<strong>Timestamp format</strong> -- automatic detection of epoch (s/ms) and ISO strings without timezone.',
        '<strong>GUI action type validation</strong> -- explicit casts to prevent type injection.',
        '<strong>WebSocket handshake buffer</strong> -- expanded to 8192 bytes.',
        '<strong>WebSocket writer cleanup</strong> -- explicit socket close on server stop.',
      ],
      added: [
        '<strong>Mobile support</strong> -- hamburger menu with sliding sidebar for narrow screens.',
        '<strong>HTTP security headers</strong> -- X-Content-Type-Options, Cache-Control and Content-Security-Policy.',
        '<strong>Dynamic injection</strong> -- version and WebSocket port injected from the server, no hardcoded values.',
        '<strong>Pinned SVG icon</strong> -- replaced <code>[*]</code> with pin icon in timeline and decisions.',
        '<strong>SEO audit</strong> -- canonical, og:image, FAQPage schema, hreflang, image dimensions (CLS).',
      ],
    },
    {
      version: '0.3.0',
      date: '2026-02-22',
      added: [
        '<strong>Dashboard GUI</strong> (Alpha Phase) -- real-time web dashboard with 7 views: status, timeline, decisions, agents, memory, commits and pinned items. Launched with <code>/alfred gui</code>.',
        '<strong>Monolithic Python server</strong> -- HTTP + manual WebSocket RFC 6455 + SQLite watcher. No external dependencies.',
        '<strong>Bidirectional WebSocket protocol</strong> -- <code>init</code>, <code>update</code>, <code>action</code> and <code>action_ack</code> messages. Reconnection with exponential backoff.',
        '<strong>Pinning system</strong> -- pinned items survive context compaction.',
        '<strong>New SQLite tables</strong> -- <code>gui_actions</code> and <code>pinned_items</code>. Automatic migration to schema v3.',
        '<strong>Automatic startup</strong> -- GUI server starts with each session and stops on close.',
        'Fail-open principle: if the GUI fails, Alfred works the same. 297 tests.',
      ],
      changed: [
        'README and documentation expanded with dashboard screenshots and WebSocket protocol guide.',
      ],
    },
    {
      version: '0.2.3',
      date: '2026-02-21',
      added: [
        '<strong>Persistent memory v2</strong> -- schema migration, tags, status and relationships between decisions.',
        '<strong>5 new MCP tools</strong> -- total 15: update, link, health, export, import.',
        '<strong>Search filters</strong> -- <code>since</code>, <code>until</code>, <code>tags</code>, <code>status</code> parameters.',
        '<strong>Export/Import</strong> -- decisions to Markdown (ADR), import from Git and ADRs.',
        '<strong>commit-capture.py hook</strong> -- auto-capture of commits in memory.',
        '<strong>memory-compact.py hook</strong> -- protects decisions during compaction.',
        'Context injection by active iteration. ~268 tests.',
      ],
      changed: [
        'The Librarian expanded: decision lifecycle, integrity, export/import.',
      ],
    },
    {
      version: '0.2.2',
      date: '2026-02-21',
      added: [
        '<strong>dangerous-command-guard.py hook</strong> -- blocks <code>rm -rf /</code>, force push, <code>DROP DATABASE</code>, fork bombs and more.',
        '<strong>sensitive-read-guard.py hook</strong> -- warning when reading private keys, <code>.env</code>, credentials.',
        '<strong>4 new MCP tools</strong> -- total 10: stats, iterations, abandon.',
        '<strong>3 new skills</strong> -- incident-response, release-planning, dependency-strategy.',
        '<code>/alfred feature</code> allows selecting start phase.',
        'Version consistency test. 219 total tests.',
      ],
      fixed: [
        '<strong>quality-gate.py</strong> -- position anchor for runners, <code>re.IGNORECASE</code> on failures.',
        'MCP responses with <code>isError: true</code> for errors.',
        '8 technical debt issues: logging, encapsulation, recovery.',
      ],
    },
    {
      version: '0.2.1',
      date: '2026-02-21',
      fixed: [
        '<strong>Windows cache path</strong> -- install.ps1 and uninstall.ps1 aligned with Claude Code convention.',
        '<strong>memory-capture.py</strong> -- diagnostics in silent except blocks.',
        '<strong>session-start.sh</strong> -- specific catches instead of generic Exception.',
      ],
    },
    {
      version: '0.2.0',
      date: '2026-02-20',
      added: [
        '<strong>Persistent memory</strong> -- local SQLite per project with decisions, commits, iterations and events.',
        '<strong>MCP server</strong> -- 6 stdio tools: search, record, query.',
        '<strong>The Librarian</strong> -- optional agent for historical queries.',
        '<strong>memory-capture.py hook</strong> -- automatic workflow event capture.',
        'FTS5 search, secret sanitisation, 0600 permissions.',
        '114 tests (58 new for memory).',
      ],
    },
    {
      version: '0.1.5',
      date: '2026-02-20',
      fixed: [
        '<strong>Secret-guard fail-closed</strong> -- blocks when it cannot determine the target path.',
        'Idempotent installer in clean environment (<code>mkdir -p</code>).',
        'More reliable version detection in <code>/alfred update</code>.',
      ],
    },
    {
      version: '0.1.4',
      date: '2026-02-19',
      added: [
        '<strong>6 optional agents</strong> -- data-engineer, ux-reviewer, performance, github, seo, copywriter.',
        '<strong>27 new skills</strong> across 6 domains. Total: 56 skills in 13 domains.',
        '<strong>Windows support</strong> -- native install.ps1 and uninstall.ps1.',
        '<strong>spelling-guard.py hook</strong> -- missing accents in Spanish.',
        'Quality gates expanded: 8 to 18.',
      ],
    },
    {
      version: '0.1.2',
      date: '2026-02-18',
      changed: [
        '<strong>New personality</strong> -- friendly colleague with humour, all 8 agents with their own voice.',
        'Full spelling correction across 68 files (RAE).',
      ],
      fixed: [
        'Correct command prefix, robust update, explicit registration of all 10 commands.',
      ],
    },
    {
      version: '0.1.1',
      date: '2026-02-18',
      fixed: [
        '<strong>session-start.sh</strong> -- syntax error preventing context injection.',
        '<strong>secret-guard.sh</strong> -- fail-closed policy restored.',
        '<strong>stop-hook.py</strong> -- type validation for corrupt state.',
      ],
    },
    {
      version: '0.1.0',
      date: '2026-02-18',
      added: [
        'First public release.',
        '8 specialised agents, 5 workflows, 29 skills, 5 hooks.',
        'Quality gates, GDPR/NIS2/CRA compliance, stack detection.',
      ],
    },
  ],

  // ----------------------------------------------------------------
  // Footer
  // ----------------------------------------------------------------

  footer: {
    version: 'v0.3.1',
    license: 'MIT License',
    githubUrl: 'https://github.com/686f6c61/alfred-dev',
    docsUrl: 'https://github.com/686f6c61/alfred-dev/tree/main/docs',
    tagline: 'Claude Code plugin. 15 agents. 56 skills. 10 commands. Persistent memory. From idea to production.',
    slogan: 'Automated software engineering for Claude Code.',
  },
};

export default data;
