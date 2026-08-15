/**
 * English content for the Alfred Dev landing page.
 *
 * Public claims must match plugin.json 0.7.0, README.md and docs/release.md.
 *
 * @module i18n/data.en
 */

import type { PageData } from '../types/index';

const data: PageData = {
  meta: {
    title: 'Alfred Dev - Claude Code plugin aligned with the SDK',
    description: 'Claude Code plugin with 10 agents, 11 flat skills, 18 commands, and local memory. Evidence-backed quality gates, official MCP, no global /alfred alias.',
    canonical: 'https://alfred-dev.com/en/',
    locale: 'en_US',
    og: {
      type: 'website',
      title: 'Alfred Dev - Claude Code plugin aligned with the SDK',
      description: 'A short team for Claude Code: 8 core agents, Selina when there is a frontend, Lucius on demand. Speak plainly. Gates require evidence.',
      url: 'https://alfred-dev.com/en/',
      siteName: 'Alfred Dev',
      locale: 'en_US',
      image: 'https://alfred-dev.com/screenshots/alfred-dev-share-en.png',
      imageWidth: 2400,
      imageHeight: 1260,
      imageType: 'image/png',
      imageAlt: 'Alfred Dev landing: a work system for Claude Code',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Alfred Dev - Claude Code plugin aligned with the SDK',
      description: '10 agents, 11 skills, 18 /alfred-dev:* commands. Official MCP, secret-guard, verifiable gates.',
      image: 'https://alfred-dev.com/screenshots/alfred-dev-share-en.png',
      imageAlt: 'Alfred Dev landing: a work system for Claude Code',
      site: '@686f6c61',
      creator: '@686f6c61',
    },
  },

  nav: [
    { href: '#agentes', label: 'Agents', svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>' },
    { href: '#flujos', label: 'Flows', svgContent: '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>' },
    { href: '#skills', label: 'Skills', svgContent: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>' },
    { href: '#gates', label: 'Gates', svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>' },
    { href: '#infra', label: 'Infra', svgContent: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>' },
    { href: '#uso', label: 'Use', svgContent: '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>' },
    { href: '#memoria', label: 'Memory', svgContent: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>' },
    { href: '#instalar', label: 'Install', svgContent: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>' },
    { href: '#faq', label: 'FAQ', svgContent: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>' },
  ],

  hero: {
    titleHtml: 'Your development<br>teammates in a <em>plugin</em>',
    platformHtml: 'for <span style="color: var(--blue);">Claude Code</span>',
    subtitle: '10 agents (8 core, Selina when there is a frontend, Lucius on demand). 11 flat skills, 18 /alfred-dev:* commands. Speak plainly. Evidence-backed gates and official MCP.',
    ctas: [
      { label: 'macOS / Linux', command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash', ariaLabel: 'Copy install command for macOS and Linux' },
      { label: 'Windows', command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex', ariaLabel: 'Copy install command for Windows' },
    ],
    features: {
      label: 'Why people keep it installed',
      items: [
        { title: 'Aligned with the Anthropic SDK', description: 'commands/, flat skills, exec-form hooks, official MCP. It does not rewrite settings.json or invent a global /alfred alias.', svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>', tag: { text: '0.7.0', href: '#infra' } },
        { title: 'Speak, do not recite slashes', description: 'Write “login is broken” or “pick up where we left off”. prompt-route suggests fix, quick, or retomar.', svgContent: '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>', tag: { text: 'New', href: '#uso' } },
        { title: 'A short core', description: 'Ten real roles. The runtime writes the kanban. Lucius is the only optional agent.', svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>' },
        { title: 'Gates that do not believe “tests OK”', description: 'Autopilot only resolves configured user gates. Tests, security, evidence, and human deploy stay.', svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>' },
        { title: 'Selina when there is UI', description: 'Three browser proposals and docs/style-direction.md before architecture. Skipped on APIs.', svgContent: '<circle cx="12" cy="12" r="10"/>' },
        { title: 'Lucius, second opinion', description: 'Read-only Codex CLI. Diagnosis and prescription. Enable it in /alfred-dev:ajustes.', svgContent: '<circle cx="11" cy="11" r="8"/>' },
        { title: 'Local memory and Memory UI', description: 'Per-project SQLite, 15 MCP tools, localhost GET viewer. No git-log import.', svgContent: '<rect x="3" y="4" width="18" height="12" rx="1"/>' },
        { title: 'Living docs', description: 'Architecture, compliance, threat model, and ADRs in your repo. Hygiene can block ship if they stay as scaffolds.', svgContent: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>' },
        { title: 'Secret-guard that blocks', description: 'Write, Edit, Bash, and MCP write tools. Fail-closed.', svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>' },
      ],
    },
  },

  stats: [
    { number: 10, label: 'Agents' },
    { number: 11, label: 'Skills' },
    { number: 6, label: 'Flows' },
    { number: 18, label: 'Commands' },
    { number: 8, label: 'Templates' },
    { number: 10, label: 'Hooks' },
    { number: 5, label: 'Gate types' },
  ],

  coreAgents: {
    header: {
      label: 'The team',
      title: '8 core + Selina',
      description: 'Each role is bounded. Alfred coordinates. The runtime writes the kanban — there is no project-manager agent.',
    },
    agents: [
      { name: 'Alfred', model: 'inherit', alias: 'Chief of staff', role: 'Orchestrates flows, chooses who enters, evaluates gates.', phrase: '"I took the liberty of preparing a plan."', color: 'var(--blue)' },
      { name: 'The problem hunter', model: 'inherit', alias: 'Product Owner', role: 'PRDs, stories, acceptance criteria.', phrase: '"Before we design anything, the real problem."', color: 'var(--purple)' },
      { name: 'The box drawer', model: 'inherit', alias: 'Architect', role: 'Systems, ADRs, diagrams, threat model with security.', phrase: '"If it is not in the diagram, it is debt."', color: 'var(--green)' },
      { name: 'The craftsman', model: 'inherit', alias: 'Senior Dev', role: 'TDD, atomic commits, maintainable implementation.', phrase: '"The tests are already waiting."', color: 'var(--orange)' },
      { name: 'The paranoid', model: 'inherit', alias: 'Security Officer', role: 'OWASP, STRIDE, SBOM, GDPR/NIS2/CRA. Cross-cutting.', phrase: '"That does not get hardcoded."', color: 'var(--red)' },
      { name: 'The breaker', model: 'inherit', alias: 'QA Engineer', role: 'Test plans, review, exploration, regression.', phrase: '"That edge case you skipped? I found it."', color: 'var(--gold)' },
      { name: 'The plumber', model: 'inherit', alias: 'DevOps Engineer', role: 'Docker, CI/CD, packaging, deploy. Deploy stays human.', phrase: '"If you deploy it by hand, you deploy it badly."', color: 'var(--cyan)' },
      { name: 'The translator', model: 'inherit', alias: 'Tech Writer', role: 'Code docs and project docs. Syncs docs/project and ADRs.', phrase: '"If it is not written down, it does not exist."', color: 'var(--white)' },
      { name: 'Selina', model: 'inherit', alias: 'Visual direction', role: 'Three browser proposals and docs/style-direction.md. Frontend only.', phrase: '"Style is communication, not decoration."', color: 'var(--purple)' },
    ],
  },

  optionalAgents: {
    header: {
      label: 'On demand',
      labelColor: 'var(--gold)',
      title: '1 optional: Lucius',
      description: 'Second opinion via Codex CLI. Enable with <strong style="color: var(--blue);">/alfred-dev:ajustes</strong>.',
    },
    agents: [
      { name: 'Lucius', model: 'inherit', alias: 'External technical director', role: 'Read-only Codex CLI audit. Does not replace the flow sign-off.', phrase: '"From the outside you can see a weak spot."', color: '#d97706' },
    ],
  },

  composition: {
    header: {
      label: 'Composition',
      labelColor: 'var(--gold)',
      title: 'Core always. Lucius if you ask.',
    description: 'No 9-specialist menus. Lucius is the only optional. Selina enters when there is a frontend.',
    },
    introHtml: 'When <code>/alfred-dev:alfred</code> opens work, the core team is ready. If you want an external second opinion, Alfred asks about Lucius:',
    terminalPrompt: '$ /alfred-dev:feature',
    terminalText: 'Email and password login, TDD and threat model',
    coreTeamText: 'Core team: Alfred, Product Owner, Architect, Senior Dev, Security, QA, Tech Writer, DevOps. Selina if there is UI.',
    techQuestion: 'Enable Lucius as an external second opinion?',
    techOptions: [
      { label: 'Lucius', desc: 'Codex CLI, read-only', selected: false },
    ],
    contentQuestion: 'Done with this group',
    contentOptions: [
      { label: 'Continue without enabling more', desc: 'Keep the core only', selected: true },
    ],
    confirmText: 'Team: core + optional Lucius',
    productQuestion: 'Who is the primary user?',
    productOptions: [
      { label: 'End user', desc: '', selected: true },
      { label: 'Admin', desc: '', selected: false },
      { label: 'Internal team', desc: '', selected: false },
    ],
  },

  workflows: {
    header: {
      label: 'Workflows',
      title: '6 flows, gates between phases',
      description: 'feature up to 7 phases. Outside flows: <code>progress</code>, <code>pause</code>, <code>retomar</code>.',
    },
    flows: [
      { command: '/alfred-dev:feature', subtitle: 'Full or partial cycle', description: 'Up to 7 phases. Selina only with a frontend.', stages: ['Product', 'Visual style', 'Architecture', 'Development', 'Quality', 'Docs', 'Delivery'] },
      { command: '/alfred-dev:quick', subtitle: 'Small change', description: 'Two light phases with tests and security.', stages: ['Bounded execution', 'Quick validation'] },
      { command: '/alfred-dev:fix', subtitle: 'Bug', description: 'Root cause, failing test, minimal fix, validation.', stages: ['Diagnosis', 'TDD fix', 'Validation'] },
      { command: '/alfred-dev:spike', subtitle: 'Research', description: 'No implementation commitment.', stages: ['Research', 'Findings'] },
      { command: '/alfred-dev:ship', subtitle: 'Release', description: 'Hygiene can block if UAT is open or living docs are still scaffolds.', stages: ['Audit', 'Docs', 'Package', 'Deploy'] },
      { command: '/alfred-dev:audit', subtitle: 'Audit', description: 'Quality, security, architecture, docs in parallel.', stages: ['Parallel audit'] },
    ],
  },

  gates: {
    header: {
      label: 'Quality gates',
      title: 'Evidence before claims',
      description: 'Autopilot only resolves configured user gates. It does not skip tests, security, evidence, or human deploy.',
    },
    coreLabel: 'Core',
    core: [
      { text: 'Product: the user approves the PRD' },
      { text: 'Selina: the user picks a visual direction when there is UI' },
      { text: 'Architecture: design + threat model' },
      { text: 'Development: green tests' },
      { text: 'Quality: tests + security' },
      { text: 'Docs: free gate with a checklist' },
      { text: 'Delivery: user + security. Deploy is never silent' },
      { text: 'evidence-guard records real runners' },
      { text: 'secret-guard blocks secrets on Write, Edit, Bash, and MCP' },
      { text: 'Hygiene blocks ship when UAT is open or docs/project is still a scaffold' },
    ],
    optionalLabel: 'Lucius',
    optional: [
      { text: 'External second opinion does not replace the flow sign-off', optional: true },
    ],
  },

  skills: {
    header: {
      label: 'Capabilities',
      title: '11 flat skills',
      description: 'Each skill lives at skills/&lt;name&gt;/SKILL.md. Side-effect skills require explicit invocation.',
    },
    domains: [
      { name: 'Process', skills: [
        { name: 'write-adr', description: 'ADRs in docs/adr/' },
        { name: 'evaluate-dependency', description: 'Verdict on new packages' },
        { name: 'sync-project-docs', description: 'Index and sync docs/project/' },
        { name: 'memory', description: 'SQLite read/write policy' },
      ] },
      { name: 'Security and compliance', skills: [
        { name: 'threat-model', description: 'STRIDE' },
        { name: 'compliance-check', description: 'GDPR, NIS2, CRA' },
        { name: 'sbom-generate', description: 'Software Bill of Materials' },
      ] },
      { name: 'Quality and delivery', skills: [
        { name: 'sonarqube', description: 'Preflight and analysis (manual)' },
        { name: 'incident-response', description: 'Incident response (manual)' },
        { name: 'pr-workflow', description: 'Pull request (manual)' },
      ] },
      { name: 'Visual', skills: [
        { name: 'style-direction', description: 'Selina visual direction (manual)' },
      ] },
    ],
  },

  infra: {
    header: {
      label: 'Under the hood',
      title: '10 hooks, 8 templates, Python core',
      description: 'What Claude Code actually runs. No Ralph stop-hook, no PreCompact, no spelling or dependency watchers.',
    },
    groups: [
      { title: '10 hooks', items: [
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
      ] },
      { title: '8 templates', items: [
        { name: 'prd.md', label: 'Product Requirements' },
        { name: 'adr.md', label: 'Architecture Decision' },
        { name: 'test-plan.md', label: 'Test plan' },
        { name: 'threat-model.md', label: 'STRIDE' },
        { name: 'sbom.md', label: 'Bill of Materials' },
        { name: 'compliance.md', label: 'Compliance checklist' },
        { name: 'changelog-entry.md', label: 'Changelog entry' },
        { name: 'release-notes.md', label: 'Release notes' },
      ] },
      { title: 'Python core', items: [
        { name: 'orchestrator.py', label: 'Flows, phases, gates, autopilot' },
        { name: 'continuity.py', label: 'Kanban, handoff, UAT, GitHub sync' },
        { name: 'prompt_route.py', label: 'Route without a slash' },
        { name: 'session_brief.py', label: 'Session briefing' },
        { name: 'project_docs.py', label: 'Living docs and ADRs' },
        { name: 'memory*.py', label: 'SQLite, MCP, and Memory UI' },
      ] },
    ],
  },

  commands: {
    header: {
      label: 'Interface',
      title: '18 /alfred-dev:* commands',
      description: 'Entry is /alfred-dev:alfred. No global /alfred. next and search stay internal helpers.',
    },
    groups: [
      { label: 'Entry', color: 'var(--blue)', commands: [
        { command: '/alfred-dev:alfred', description: 'Decide whether to map, resume, open a flow, or answer shortly.' },
        { command: '/alfred-dev:ajustes', description: 'Autonomy, Lucius, memory, personality. Formerly /alfred-dev:config.' },
        { command: '/alfred-dev:update', description: 'Real semver and a two-option menu.' },
      ] },
      { label: 'Flows', color: 'var(--green)', commands: [
        { command: '/alfred-dev:feature', description: 'Up to 7 phases. Selina if there is UI.' },
        { command: '/alfred-dev:quick', description: 'Small change, 2 phases.' },
        { command: '/alfred-dev:fix', description: 'Bug with TDD.' },
        { command: '/alfred-dev:spike', description: 'Research without a commitment.' },
        { command: '/alfred-dev:ship', description: 'Release. Hygiene may block.' },
        { command: '/alfred-dev:audit', description: 'Four axes in parallel.' },
      ] },
      { label: 'Continuity', color: 'var(--cyan)', commands: [
        { command: '/alfred-dev:progress', description: 'Kanban, blockers, UAT, traceability.' },
        { command: '/alfred-dev:pause', description: 'Handoff in JSON and Markdown.' },
        { command: '/alfred-dev:retomar', description: 'Resume the handoff. Formerly /alfred-dev:resume.' },
        { command: '/alfred-dev:map-codebase', description: 'Persistent brownfield map.' },
        { command: '/alfred-dev:discuss', description: 'Refine before feature.' },
      ] },
      { label: 'Operations', color: 'var(--gold)', commands: [
        { command: '/alfred-dev:uat', description: 'Human validation. Formerly /alfred-dev:verify.' },
        { command: '/alfred-dev:memory-ui', description: 'Local GET viewer over SQLite.' },
        { command: '/alfred-dev:sync-github', description: 'Mirror the local board to Issues.' },
        { command: '/alfred-dev:lucius', description: 'Codex CLI second opinion.' },
      ] },
    ],
    optionalNote: 'The only optional agent is <strong>Lucius</strong>, via <strong>/alfred-dev:ajustes</strong>. Selina enters when there is a frontend.',
  },

  stacks: {
    header: {
      label: 'Automatic detection',
      title: 'It adapts to your project',
      description: 'Detects the stack and adapts artifacts. It does not invent the 0.6 specialist catalog.',
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
      label: 'In practice',
      labelColor: 'var(--cyan)',
      title: 'How you use it',
      description: 'Speak plainly or use /alfred-dev:*. These are real 0.7.0 paths.',
    },
    cases: [
      { category: 'Conversational', color: 'var(--gold)', background: 'rgba(201,169,110,0.08)', title: 'No slash memorization', command: 'login breaks on tildes', steps: ['prompt-route classifies it as fix', 'Alfred starts TDD diagnosis'] },
      { category: 'Development', color: 'var(--blue)', background: 'rgba(91,156,245,0.08)', title: 'Full feature', command: '/alfred-dev:feature push notifications', steps: ['PRD', 'Selina only with UI', 'Architecture, TDD, QA, docs, delivery'] },
      { category: 'Fix', color: 'var(--red)', background: 'rgba(229,86,79,0.08)', title: 'Bug', command: '/alfred-dev:fix login fails on tildes', steps: ['Reproduce', 'Failing test', 'Minimal fix'] },
      { category: 'Research', color: 'var(--purple)', background: 'rgba(160,126,232,0.08)', title: 'Spike', command: '/alfred-dev:spike REST vs gRPC', steps: ['Explore without committing'] },
      { category: 'Audit', color: 'var(--orange)', background: 'rgba(232,164,74,0.08)', title: 'Audit', command: '/alfred-dev:audit', steps: ['Four axes', 'SonarQube only with a human decision'] },
      { category: 'Ship', color: 'var(--green)', background: 'rgba(78,201,144,0.08)', title: 'Release', command: '/alfred-dev:ship', steps: ['Hygiene', 'Changelog', 'Human deploy'] },
      { category: 'Brownfield', color: 'var(--cyan)', background: 'rgba(78,201,201,0.08)', title: 'Existing repo', command: '/alfred-dev:map-codebase', steps: ['Persistent map in docs/project/'] },
      { category: 'Continuity', color: 'var(--green)', background: 'rgba(78,201,144,0.08)', title: 'Pause and resume', command: '/alfred-dev:pause', steps: ['Handoff JSON + Markdown', '/alfred-dev:retomar'] },
      { category: 'State', color: 'var(--magenta)', background: 'rgba(214,106,214,0.08)', title: 'What is in flight', command: '/alfred-dev:progress', steps: ['Kanban, blockers, UAT'] },
      { category: 'UAT', color: 'var(--red)', background: 'rgba(229,86,79,0.08)', title: 'Human acceptance', command: '/alfred-dev:uat', steps: ['pending / approved / rejected'] },
      { category: 'Memory', color: 'var(--blue)', background: 'rgba(84,196,255,0.08)', title: 'Memory UI', command: '/alfred-dev:memory-ui', wide: true, steps: ['Localhost GET viewer', 'No git-log import'] },
      { category: 'Visual', color: 'var(--purple)', background: 'rgba(160,126,232,0.08)', title: 'Selina', command: '/alfred-dev:feature app with UI', wide: true, image: { src: '/screenshots/selina-style-direction.svg', alt: 'Selina visual proposals', caption: 'Three finalists and docs/style-direction.md.' }, steps: ['Three proposals', 'User chooses'] },
      { category: 'GitHub', color: 'var(--text-muted)', background: 'rgba(110,115,138,0.08)', title: 'Board mirror', command: '/alfred-dev:sync-github owner/repo', wide: true, image: { src: '/screenshots/sonia-sync-github.png', alt: 'Local board mirrored to GitHub Issues', caption: 'GitHub is a mirror. Truth stays in docs/project and SQLite.' }, steps: ['Projects the local board with gh'] },
      { category: 'Automatic', color: 'var(--cyan)', background: 'rgba(78,201,201,0.08)', title: 'What runs on its own', wide: true, description: 'Registered hooks only.', steps: ['secret-guard', 'dangerous-command-guard', 'quality-gate + evidence-guard', 'prompt-route', 'activity-capture', 'session-end'] },
      { category: 'Autonomy', color: 'var(--green)', background: 'rgba(78,201,126,0.08)', title: 'Honest autopilot', command: '/alfred-dev:ajustes', steps: ['Only user gates auto-pass'] },
    ],
  },

  memory: {
    sectionLabel: 'Per-project persistent memory',
    title: 'Local memory, official MCP, GET UI',
    descriptionHtml: 'SQLite at <code>.claude/alfred-memory.db</code>. FastMCP when the <code>mcp</code> package is installed. Memory UI does not import Git history.',
    traceability: {
      title: 'Traceability',
      descriptionHtml: 'Problem, decision, commit, and validation with citable IDs.',
      nodes: [
        { label: 'Problem', color: 'var(--purple)', background: 'rgba(160,126,232,0.08)', borderColor: 'rgba(160,126,232,0.15)' },
        { label: 'Decision [D#id]', color: 'var(--gold)', background: 'rgba(201,169,110,0.08)', borderColor: 'rgba(201,169,110,0.15)' },
        { label: 'Commit [C#sha]', color: 'var(--green)', background: 'rgba(78,201,144,0.08)', borderColor: 'rgba(78,201,144,0.15)' },
        { label: 'Validation', color: 'var(--blue)', background: 'rgba(91,156,245,0.08)', borderColor: 'rgba(91,156,245,0.15)' },
      ],
    },
    cards: [
      { title: 'Local SQLite', descriptionHtml: 'WAL, FTS5, 0600. Nothing leaves the project.' },
      { title: 'Official MCP', descriptionHtml: '15 tools. FastMCP when <code>mcp</code> is installed.' },
      { title: 'Bounded capture', descriptionHtml: '<code>activity-capture.py</code> on UserPromptSubmit and PostToolUse (Write/Edit/Bash).' },
      { title: 'Session briefing', descriptionHtml: 'SessionStart injects state, last decision, and accepted ADRs.' },
      { title: 'Close', descriptionHtml: 'SessionEnd writes <code>.claude/alfred-last-cierre.md</code>.' },
      { title: 'Secrets', descriptionHtml: 'Same sanitizer as <code>secret-guard.py</code>.' },
    ],
    librarian: {
      title: 'Lookup: MCP and Memory UI',
      subtitle: 'There is no Librarian agent',
      descriptionHtml: [
        'Queries go through MCP tools or <code>/alfred-dev:memory-ui</code>. Citations use <code>[D#id]</code>, <code>[C#sha]</code>, <code>[I#id]</code>.',
        'Memory UI is a localhost GET viewer. Empty memory stays empty.',
      ],
      example: {
        label: 'Example:',
        question: '> Why SQLite instead of PostgreSQL?',
        answerHtml: 'Zero external services was the requirement <span style="color: var(--gold);">[D#12]</span>. Implemented in <span style="color: var(--green);">[C#1833e83]</span>.',
      },
      activationHtml: '<strong>Enable:</strong> <code>/alfred-dev:ajustes</code>, memory section.',
    },
    faq: [
      { question: 'Where is data stored?', answerHtml: 'In <code>.claude/alfred-memory.db</code> inside the project.' },
      { question: 'Does it turn on by itself?', answerHtml: 'First SessionStart may seed <code>memoria.enabled: true</code>. After that, <code>/alfred-dev:ajustes</code> wins.' },
      { question: 'What about secrets?', answerHtml: 'They go through <code>core/secrets.py</code>. The db file is 0600.' },
      { question: 'Can I delete memory?', answerHtml: 'Yes. Delete the <code>.db</code> or set <code>enabled: false</code>.' },
    ],
  },

  install: {
    sectionLabel: 'First steps',
    title: 'Install',
    description: 'One command. User scope. The 0.7.0 script does not overwrite ~/.claude/skills or create /alfred. GitHub main may still serve another version.',
    tabs: [
      { id: 'macos', label: 'macOS', command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash', requirementsHtml: '<strong>Requirements:</strong> Python 3.10+, Claude Code with plugins/skills/hooks/MCP.<br>Then <strong>/reload-plugins</strong> and <strong>/alfred-dev:alfred</strong>.' },
      { id: 'linux', label: 'Linux', command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash', requirementsHtml: '<strong>Requirements:</strong> Python 3.10+, Claude Code with plugins/skills/hooks/MCP.<br>Then <strong>/reload-plugins</strong> and <strong>/alfred-dev:alfred</strong>.' },
      { id: 'windows', label: 'Windows', command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex', requirementsHtml: '<strong>Requirements:</strong> PowerShell 5.1+, Python 3.10+, recent Claude Code.<br>Then <strong>/reload-plugins</strong> and <strong>/alfred-dev:alfred</strong>.' },
    ],
    uninstall: {
      title: 'Uninstall',
      description: 'Removes plugin, marketplace, and cache. Leaves project .claude/ alone.',
      cards: [
        { title: 'macOS / Linux', command: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash', ariaLabel: 'Copy uninstall command for macOS/Linux' },
        { title: 'Windows (PowerShell)', command: 'irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.ps1 | iex', ariaLabel: 'Copy uninstall command for Windows' },
      ],
    },
    update: {
      title: 'Update',
      descriptionHtml: '<strong>/alfred-dev:update</strong> compares semver and offers one menu. Normalizes to <code>--scope user</code>. It does not recreate /alfred.',
    },
  },

  config: {
    sectionLabel: 'Customization',
    title: 'Per-project configuration',
    descriptionHtml: '<code>.claude/alfred-dev.local.md</code>. First session seeds it. Then <strong>/alfred-dev:ajustes</strong>.',
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
---`,
    blocks: [
      { title: 'Bootstrap', descriptionHtml: 'SessionStart creates the file if missing. It does not rewrite settings.json.' },
      { title: 'Autonomy', descriptionHtml: 'Per phase. Autopilot only auto-approves user gates.' },
      { title: 'Lucius', descriptionHtml: 'The only optional. Codex CLI, read-only.' },
      { title: 'Memory and docs', descriptionHtml: 'SQLite plus docs/project and docs/adr.' },
      { title: 'Personality', descriptionHtml: 'Sarcasm 1-5. Celebrations are separate.' },
    ],
  },

  faq: {
    header: { label: 'FAQ', title: 'FAQ' },
    items: [
      {
        svgContent: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/>',
        question: 'How do I install it?',
        answerHtml: '<p>macOS and Linux:</p><pre>curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash</pre><p>Windows:</p><pre>irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex</pre><p>You need Claude CLI on PATH, Python 3.10+, and <code>~/.claude</code>. The script installs <code>alfred-dev@alfred-dev</code> with <code>--scope user</code>. Then <code>/reload-plugins</code> and <code>/alfred-dev:alfred</code>.</p>',
      },
      {
        svgContent: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>',
        question: 'Does that curl already install 0.7.0?',
        answerHtml: '<p>Not necessarily. The command reads the GitHub <code>main</code> branch, not this landing.</p><p>When this page was built, <code>main</code> published <strong>{{GITHUB_MAIN_VERSION}}</strong> ({{GITHUB_MAIN_COMMANDS}} commands). This page describes <strong>{{LANDING_VERSION}}</strong>.</p><p>If they differ, the one-liner installs whatever is on <code>main</code>. 0.6.1 creates the <code>/alfred</code> alias. 0.7.0 does not, and it does not overwrite <code>~/.claude/skills</code>.</p>',
      },
      {
        svgContent: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>',
        question: 'What does it need?',
        answerHtml: '<p>A recent Claude Code with plugins, skills, hooks, and MCP. Python 3.10 or newer. The installer looks for <code>python3.13</code> … <code>python3.10</code> if <code>python3</code> is old.</p><p>The Python <code>mcp</code> package enables FastMCP; without it, the memory server still has a fallback. On Windows: PowerShell 5.1+ or bash on WSL.</p>',
      },
      {
        svgContent: '<rect x="2" y="3" width="20" height="14" rx="2"/>',
        question: 'Does it work on Windows?',
        answerHtml: '<p>Yes. Use <code>install.ps1</code>, or <code>install.sh</code> inside WSL.</p><p>Then <code>/reload-plugins</code> and <code>/alfred-dev:alfred</code>. If the inventory does not load, restart Claude Code.</p>',
      },
      {
        svgContent: '<polyline points="23 4 23 10 17 10"/>',
        question: 'How do I update or uninstall?',
        answerHtml: '<p>Update: <code>/alfred-dev:update</code> compares semver with GitHub Releases and, if you accept, reruns the <code>main</code> installer with <code>--scope user</code>. 0.7.0 does not recreate <code>/alfred</code>.</p><p>Uninstall:</p><pre>curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash</pre><pre>irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.ps1 | iex</pre><p>That removes the plugin, marketplace, cache, and a leftover 0.6.1 <code>/alfred</code> alias. It does not delete the project <code>.claude/</code>.</p>',
      },
      {
        svgContent: '<path d="M3 12h18"/>',
        question: 'Is there a /alfred alias?',
        answerHtml: '<p>Not in 0.7.0. The entry is <code>/alfred-dev:alfred</code>. The 0.7.0 installer does not write into <code>~/.claude/skills</code>.</p><p>If you come from 0.6.1, the uninstaller deletes that alias only when the file is marked «Alfred Dev global alias».</p>',
      },
      {
        svgContent: '<polyline points="4 17 10 11 4 5"/>',
        question: 'Do I need to learn all 18 commands?',
        answerHtml: '<p>No. Write in plain language. <code>prompt-route</code> suggests the route (fix, quick, retomar, ship…).</p><p>SessionStart injects the briefing. If you want a slash, start with <code>/alfred-dev:alfred</code>.</p>',
      },
      {
        svgContent: '<path d="M8 6h13"/>',
        question: 'When quick and when feature?',
        answerHtml: '<p><code>quick</code> is a bounded change: two phases, tests and security, less ceremony.</p><p><code>feature</code> if it crosses product, architecture, or several phases (up to 7, with Selina only when there is a frontend).</p>',
      },
      {
        svgContent: '<path d="M12 2v4"/>',
        question: 'How do I pick up a session?',
        answerHtml: '<p><code>/alfred-dev:retomar</code> or “pick up where we left off”. It reads <code>.claude/alfred-handoff.json</code>.</p><p>Before you stop: <code>/alfred-dev:pause</code>. Board state is in <code>/alfred-dev:progress</code>.</p>',
      },
      {
        svgContent: '<path d="M3 3v18h18"/>',
        question: 'What are progress and uat?',
        answerHtml: '<p><code>progress</code> summarizes kanban, blockers, UAT, and traceability. It replaced standup, blocked, in-progress, and validate as public slashes.</p><p><code>uat</code> records human acceptance: <code>pending</code>, <code>approved</code>, or <code>rejected</code>. Automated tests do not close UAT.</p>',
      },
      {
        svgContent: '<rect x="3" y="4" width="18" height="12" rx="2"/>',
        question: 'Where is memory stored?',
        answerHtml: '<p>In <code>.claude/alfred-memory.db</code> inside the project (SQLite, WAL, FTS5, 0600). There are 15 MCP tools.</p><p><code>/alfred-dev:memory-ui</code> opens a localhost GET viewer. It does not import git log. <code>/alfred-dev:memory-ui stop</code> or SessionEnd close it. Empty memory stays empty.</p>',
      },
      {
        svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>',
        question: 'How many agents and skills are there?',
        answerHtml: '<p>10 agents: 8 core, Selina when there is a frontend, and Lucius on demand (<code>/alfred-dev:ajustes</code>).</p><p>11 flat skills. Side-effect ones (SonarQube, style, incident, PR) need an explicit invocation. 18 published <code>/alfred-dev:*</code> commands.</p>',
      },
      {
        svgContent: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        question: 'Is it aligned with the Anthropic SDK?',
        answerHtml: '<p>Yes. <code>plugin.json</code> lists the 18 commands, skills are auto-discovered, hooks use <code>command</code> + <code>args</code>, and MCP is official.</p><p>There is no global <code>/alfred</code> alias, no Ralph-style Stop hook, and no <code>settings.json</code> rewrite to install.</p>',
      },
      {
        svgContent: '<line x1="12" y1="1" x2="12" y2="23"/>',
        question: 'What does it cost, and what language does it use?',
        answerHtml: '<p>The plugin is MIT. You pay for your Claude Code session.</p><p>It answers in Spanish from Spain by default. Change that in <code>/alfred-dev:ajustes</code>.</p>',
      },
      {
        svgContent: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>',
        question: 'What if a gate fails?',
        answerHtml: '<p>The flow stops and explains why.</p><p>Autopilot only auto-approves configured user gates. It does not skip tests, security, evidence, or the human deploy confirmation.</p>',
      },
      {
        svgContent: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>',
        question: 'Can I contribute?',
        answerHtml: '<p>Yes. MIT. Issues and PRs at <a href="https://github.com/686f6c61/alfred-dev" target="_blank" rel="noopener noreferrer">github.com/686f6c61/alfred-dev</a>.</p>',
      },
    ],
  },

  changelog: [
    {
      version: '0.7.0',
      date: '2026-08-15',
      added: [
        '<strong>Aligned with the Claude Code SDK</strong>: commands, flat skills, exec-form hooks, and official MCP (FastMCP) when the <code>mcp</code> package is installed.',
        '<strong>Speak without slashes</strong>: SessionStart injects the protocol and <code>prompt-route.py</code> suggests fix, quick, or retomar when you write in plain language.',
        '<strong>Living project docs</strong>: index, architecture, compliance, threat model, and ADRs in the user repo, synced by phase.',
        '<strong>Session close</strong>: SessionEnd writes <code>.claude/alfred-last-cierre.md</code> and stops Memory UI.',
      ],
      changed: [
        'Public surface cut to 10 agents, 11 flat skills, 18 commands. Entry is <code>/alfred-dev:alfred</code>.',
        'Public continuity: <code>alfred</code>, <code>progress</code>, and <code>retomar</code>. <code>config</code> becomes <code>ajustes</code>, <code>verify</code> becomes <code>uat</code>.',
        'No Ralph stop-hook and no rewriting <code>settings.json</code>. Secret-guard covers Write, Edit, Bash, and MCP write tools.',
        'Agent Teams only if the user already enabled it. Memory UI does not import Git history.',
      ],
      removed: [
        'Global <code>/alfred</code> alias and the 0.6 optional catalog (data-engineer, github-manager, librarian, and the rest).',
        'Public commands <code>next</code>, <code>search</code>, <code>standup</code>, <code>validate</code>, <code>help</code>, and <code>status</code>.',
      ],
    },
    {
      version: '0.6.1',
      date: '2026-06-22',
      changed: [
        '<strong>More resilient installers</strong>: Bash and PowerShell clear stale local Claude Code marketplace checkouts before reinstalling.',
        '<strong>Normalized global updates</strong>: the flow re-registers the GitHub source, refreshes the <code>alfred-dev</code> marketplace, and keeps the plugin installed at <code>user</code> scope.',
      ],
      fixed: [
        'Fixes the case where Claude Code reported <code>Successfully installed plugin: alfred-dev@alfred-dev</code> while the installed cache still resolved to an older version such as <code>0.5.2</code>.',
        'The <code>/alfred</code> alias is materialized again from the correct plugin root after updating from old versions or inherited local caches.',
      ],
    },
    {
      version: '0.6.0',
      date: '2026-06-19',
      changed: [
        '<strong>Agents loaded from the root</strong>: the 9 optional agents move into <code>agents/</code> so Claude Code can discover all 19 plugin agents.',
        '<strong>MCP compatible with the current CLI</strong>: <code>alfred-memory</code> is declared in <code>.mcp.json</code> with a portable launcher that uses <code>CLAUDE_PLUGIN_ROOT</code> when installed and <code>cwd</code> during local development.',
        '<strong>Updated terminology</strong>: commands, agents, and operational docs replace obsolete <code>Task</code> references with <code>Agent</code>.',
        '<strong>Human UI name</strong>: <code>plugin.json</code> and <code>marketplace.json</code> declare <code>displayName: "Alfred Dev"</code> so Claude Code shows <code>Alfred Dev (alfred-dev)</code> without changing the technical namespace.',
        '0.6.0 stabilization release: <code>plugin.json</code> is the canonical version source and the marketplace does not duplicate <code>version</code>.',
        'The memory MCP server speaks modern JSONL stdio and still reads legacy <code>Content-Length</code> framing.',
      ],
      fixed: [
        'Claude Code can now show the 19 agents in the plugin inventory.',
        'Claude Code counts <code>alfred-memory</code> in the plugin inventory again.',
        '<code>claude mcp get plugin:alfred-dev:alfred-memory</code> now connects to the real server.',
      ],
    },
    {
      version: '0.5.2',
      date: '2026-04-11',
      added: [
        '<strong>Full skills catalog published</strong>: <code>plugin.json</code> stops enumerating a partial sample and now exposes all 15 domains under <code>skills/</code>.',
        '<strong>Stricter public surface contracts</strong>: the suite now validates the published catalog, canonical frontmatter, manual-only skills, and the absence of collisions with commands.',
        '<strong>Selina gets a real guided flow</strong>: base system first, then typography and palette, and only then three comparable final proposals inside that family.',
      ],
      changed: [
        'Heavier skills or those with clear side effects remain published, but are forced to manual activation with <code>disable-model-invocation: true</code>.',
        'Help and public docs now group commands by actual value: core, advanced operations, and views/aliases.',
        'Selina’s final proposals now respect the selected visual system instead of recolouring the same generic layout shell.',
        'The landing no longer frames the catalog as an internal/partial sample and now reflects the 62 published skills in the release.',
        'Version alignment to 0.5.2 across plugin, marketplace, installers, packages, docs, changelog, and landing.',
      ],
      fixed: [
        '<code>style-direction</code> now declares canonical frontmatter instead of relying on implicit inference.',
        'The public skill surface no longer depends on partial lists that drift from the real repository.',
        'Selina’s visual companion still records the user choice when the local WebSocket handshake fails and the HTTP fallback has to take over.',
      ],
    },
    {
      version: '0.5.1',
      date: '2026-04-10',
      added: [
        '<strong>Canonical Selina catalog with 10 base design systems</strong>: <code>core/selina_style_catalog.py</code> gathers the free/contextual mode plus nine trend-led families so the visual phase starts from an explicit vocabulary.',
        '<strong>Visual demo gallery</strong>: <code>core/selina_style_demo.py</code> and <code>visual/scripts/write-style-demo-gallery.py</code> generate a browsable catalog before the three final proposals are locked.',
        '<strong>Palettes and type pairings per family</strong>: each design system declares colour modes, typography pairings and links to references or Google Fonts.',
      ],
      changed: [
        'Selina is no longer framed as “three isolated styles”: it now works from 10 base design systems and narrows them down to three comparable proposals based on the PRD, audience, and stack.',
        'Version aligned to 0.5.1 across plugin, marketplace, installers, packages, Memory MCP, session report, README, changelog, docs and landing.',
        'The landing explains more faithfully how Selina enters the flow and what it really means to close a design system before touching frontend code.',
      ],
      fixed: [
        'Update surface without drift: internal fallback points that still returned an older release now reflect the current version.',
        'Release tests are less brittle: the suite no longer depends on thin Astro wrappers or hardcoded version paths when the manifest is the real source of truth.',
      ],
    },
    {
      version: '0.5.0',
      date: '2026-03-31',
      added: [
        '<strong>Lucius — The Technical Director</strong>: new optional agent that acts as an external technical second opinion. It invokes <code>codex exec</code> with an explicit read-only sandbox, uses the configured Codex CLI model and returns diagnosis + prescription per item.',
        '<strong><code>/alfred-dev:lucius</code> command</strong>: entry point for the audit. It accepts an optional target directory and scope (<code>all</code>, <code>security</code>, <code>tests</code>, <code>architecture</code>, <code>performance</code>).',
        '<strong>Structured report per item</strong>: Lucius returns diagnosis + prescription + effort (S/M/L) + suggested implementer (Alfred or Codex) in four sections: Critical, Relevant, Opportunities and What\'s working well.',
        '<strong>Prerequisite preflight</strong>: checks that <code>codex</code> is on the PATH and authenticated. If something is missing, it stops with clear install instructions.',
        '<strong>Hard gate with no modifications</strong>: Lucius compares Git status before and after running Codex CLI in <code>--sandbox read-only</code>; if it detects differences, it reports them instead of hiding the problem.',
        '<strong>Selina — The Stylist</strong>: new core agent (10th) that occupies phase 1b of the <code>feature</code> workflow and presents three style directions before component design starts.',
        '<strong>Local visual server</strong>: zero-dependency HTTP + WebSocket server in <code>visual/scripts/server.cjs</code> with hot reload, per-project sessions and graceful shutdown.',
        '<strong>Visual style skill</strong>: <code>skills/estilo/style-direction/SKILL.md</code> guides Selina to start the server, propose options, capture the selection and generate <code>docs/style-direction.md</code>.',
        '<strong>Conditional <code>visual_style</code> phase</strong>: the orchestrator only enables it when <code>config_loader.has_frontend(stack)</code> detects a public UI.',
        '<strong><code>_advance_skipping_phases</code> helper</strong>: extracted orchestrator function that skips phases whose condition is not met and reduces cognitive complexity.',
      ],
      changed: [
        '19 agents total: the plugin moves from 18 to 19 agents (10 core + 9 optional) with Lucius included.',
        '26 commands: <code>/alfred-dev:lucius</code> joins the manifest and the public surface of the plugin.',
        'Version aligned to 0.5.0 across plugin, marketplace, installers, packages, README, changelog, docs and landing.',
        'Landing updated: Lucius card appears before Selina with a “New” badge, optional-agent use cases and counters updated to 19 agents and 26 commands.',
      ],
      fixed: [
        'Native module imports in <code>server.cjs</code>: mandatory <code>node:</code> prefix (<code>node:http</code>, <code>node:crypto</code>, <code>node:fs</code>, <code>node:path</code>).',
        '<code>Number.parseInt</code> instead of <code>parseInt</code> in <code>server.cjs</code> (SonarQube linting rule).',
        'Reduced cognitive complexity of <code>handleRequest</code>: the <code>/files/*</code> block was extracted into <code>serveStaticFile()</code>.',
        '<code>catch</code> block without unused variable: <code>catch (e)</code> becomes <code>catch {}</code> in <code>serveStaticFile</code>.',
        'Cognitive complexity in <code>config_loader.py</code>: <code>_count_source_files</code> and <code>suggest_optional_agents</code> were simplified by extracting reusable helpers.',
        'SonarQube skill registered in <code>plugin.json</code>: the file existed but was missing from the plugin manifest.',
        'Docker execution in subagents: scoped <code>Bash(docker ...)</code> entries let <code>security-officer</code> run the SonarQube workflow after <code>/audit</code> confirms Docker is operational or the user authorizes preparing it.',
      ],
    },
    {
      version: '0.4.7',
      date: '2026-03-31',
      fixed: [
        'SessionStart hook fixed: the session context JSON output no longer truncates when content exceeds kernel ARG_MAX or contains special characters.',
      ],
      changed: [
        'Hook JSON generation moves from bash heredoc interpolation to direct stdin emission via json.dumps, eliminating the entire error class.',
        'Version aligned to 0.4.7 across plugin, marketplace, installers, packages, structured metadata, README, changelog, docs and landing.',
      ],
    },
    {
      version: '0.4.6',
      date: '2026-03-23',
      added: [
        'New local Memory UI: /alfred-dev:memory-ui opens overview, timeline, decisions, commits, search and health directly on top of the project SQLite.',
        'Memory UI now starts with useful data: map-codebase, discuss and quick seed progress, traceability, kanban and lightweight iterations naturally.',
        'The UI imports recent Git commits when memory still has no linked commits and explains empty states better in temporary or non-repo workspaces.',
        'Expanded E2E coverage for Memory UI, helper-first seeding and local server rendering.',
      ],
      changed: [
        'Alfred now exposes 25 visible commands and adds memory-ui as a first-class public surface in the website, README, help and session-start.',
        'This release removes internal planning docs from the published repo and aligns homepage, metadata and operational docs for 0.4.6.',
      ],
    },
    {
      version: '0.4.5',
      date: '2026-03-22',
      added: [
        'New PM layer for SonIA: /alfred-dev:standup, /alfred-dev:blocked, /alfred-dev:in-progress, /alfred-dev:validate and /alfred-dev:search.',
        'SonIA Sync for GitHub through /alfred-dev:sync-github, while keeping docs/project and SQLite as the source of truth.',
        'Expanded E2E coverage for PM helpers, board parsing and issue synchronization.',
      ],
      changed: [
        'Alfred now exposes 24 commands and 13 visible hooks: continuity, operational PM, persistent memory and multi-agent workflows in one interface.',
        'The website, README and docs now reflect SonIA as a CLI operational layer and the new GitHub collaboration surface.',
      ],
    },
    {
      version: '0.4.4',
      date: '2026-03-22',
      added: [
        'Operational continuity layer: new commands /alfred-dev:map-codebase, /alfred-dev:next, /alfred-dev:pause, /alfred-dev:resume, /alfred-dev:verify and /alfred-dev:progress.',
        'New /alfred-dev:discuss command to refine ideas before building, with discovery.md and current.md artifacts.',
        'New /alfred-dev:quick 2-phase workflow for small changes with tests and security review.',
        'Shared memory configuration parser and new coverage for event FTS, purge + health, Git import with "|" and sync beyond 1000 decisions.',
      ],
      changed: [
        '/alfred becomes a contextual router: it decides whether continuity, brownfield mapping, refinement or a multi-agent workflow should happen next.',
        'SessionStart bootstraps local configuration and recommends the next step from the very first session.',
        'The website now reflects the current model: 6 execution workflows, 18 commands and a visible operational layer.',
        'Persistent memory stops producing false negatives: content-bearing events are searchable, purge cleans FTS, retention_days is read from project config and size_bytes includes WAL.',
      ],
    },
    {
      version: '0.4.2',
      date: '2026-03-14',
      fixed: [
        'False positive in evidence guard: the failure detection pattern matched "0 failures" as a failure. Fixed to exclude zero.',
        'Architecture gate mistyped: the architecture phase had gate "user" instead of "user+security", making security validation inoperative.',
        'Divergent patterns: quality-gate.py had its own patterns that diverged from evidence_guard_lib.py. Unified to use a single source of truth.',
        'Inconsistent autopilot key: commands looked for "mode: autopilot" but code wrote "autopilot: true". Fixed.',
      ],
      added: [
        'Go test support in evidence guard: go test output is correctly detected as success.',
        'Partial session reports: the stop-hook generates a report when a session is interrupted, not only when completed.',
        'Autopilot mode and iterations in reports: reports show whether the session was autopilot and how many retries each phase had.',
        'Evidence verification in markdown: explicit instruction to read alfred-evidence.json before advancing automatic gates.',
        'Iterative loop documented in feature, fix and ship commands (max 5 retries per phase).',
      ],
      changed: [
        'Stop-hook refactored into testable functions: should_block, build_block_message, handle_session_report.',
        'Block message adapted for autopilot: does not ask for user confirmation but instructs to investigate the error.',
        'Dynamic version in reports: template reads version from plugin.json.',
        'Evidence cleanup between sessions to avoid cross-contamination.',
      ],
    },
    {
      version: '0.4.1',
      date: '2026-03-13',
      added: [
        'Automatic initial setup: when using Alfred for the first time in a project, it asks whether you want interactive or autopilot mode. No manual steps required.',
      ],
      fixed: [
        'Autopilot mode disconnected from actual flow: autopilot detection was not reaching the composition. Fixed so user gates are auto-approved when mode is autopilot.',
      ],
    },
    {
      version: '0.4.0',
      date: '2026-03-13',
      added: [
        'Evidence verification (evidence guard): hook that records each test execution as verifiable evidence. When an agent claims tests pass, the system checks they were actually run.',
        'Session report on close: automatic summary in docs/alfred-reports/ with phases, test evidence, team and artifacts.',
        'Iterative loop within phases: agents iterate up to 5 times within a phase until the gate is passed, enabling natural TDD cycles.',
        'Autopilot mode: full execution without human interruption. User gates are auto-approved; automatic and security gates are evaluated normally.',
      ],
      changed: [
        '17 agent personalities rewritten with Alfred Pennyworth tone: impeccable service, subtle irony, technical precision.',
        'Orchestrator extended with iterative loop functions (should_retry_phase, reset_phase_iterations) and autopilot (is_autopilot_gate_passable, run_flow_autopilot).',
        'Stop-hook automatically generates session report when closing a completed session.',
      ],
    },
    {
      version: '0.3.9',
      date: '2026-03-13',
      added: [
        'Optional i18n-specialist agent for multilingual projects: automatic detection of i18n signals (i18n/, locales/, translations/ directories), integration in development and quality phases.',
        'Automatic i18n detection in suggest_optional_agents(): analyzes i18n directories and configuration files in the project.',
      ],
      changed: [
        'Optional agent selection redesigned: 2 multiSelect questions grouped by theme (technical + content/UX) instead of a long list, compatible with AskUserQuestion 4-option limit.',
        'Product Owner reformulated: product phase questions are asked one at a time (one per turn) instead of in bulk, following the progressive refinement pattern from superpowers:brainstorming.',
        '8 optional agents (previously 7): added i18n-specialist to catalog, config, orchestrator, documentation, and tests.',
      ],
    },
    {
      version: '0.3.8',
      date: '2026-03-13',
      added: [
        'SQLite to native memory sync layer: decisions, iterations, and commits stored in alfred-memory.db are automatically projected as .md files in ~/.claude/projects/<hash>/memory/ using native Claude Code format.',
        'Hybrid synchronization: full regeneration on session start + incremental updates after each SQLite write.',
        'Safe MEMORY.md management with delimited markers that preserve user manual content.',
        'Automatic memory directory creation when Alfred loads for the first time.',
        'New E2E testing skill (calidad/e2e-testing) for setting up Playwright or Cypress.',
      ],
      changed: [
        '60 skills reviewed and improved: enriched descriptions for better triggering, "What NOT to do" section in 51 skills, persistent memory integration in 10 skills, detect_stack reference in 9 skills.',
        '3 standalone protocols (incident-response, dependency-strategy, release-planning) reorganized into their logical categories (calidad/, seguridad/, devops/).',
        'Overlaps between skills explicitly documented. Normative versions (GDPR, NIS2, CRA, OWASP, WCAG) added.',
      ],
    },
    {
      version: '0.3.7',
      date: '2026-03-12',
      added: [
        '<strong>SonIA -- Project Manager</strong> -- new transversal core agent. Decomposes the PRD into tasks, manages a kanban board in <code>docs/project/kanban/</code> with 4 MD files (backlog, in-progress, done, blocked), maintains the traceability matrix (criterion -- task -- test -- doc) and generates progress reports per phase.',
        '<strong>The Interpreter -- i18n Specialist</strong> -- new optional agent for internationalisation. i18n key audit, hardcoded string detection, per-locale format validation, skeleton generation for new languages. HARD-GATE: key completeness (N in base = N in all languages).',
        '<strong>QA Engineer expanded</strong> -- new integration and E2E testing section with strategies for Playwright/Cypress, decision table for test types (unit, integration, E2E, regression) and selection criteria.',
      ],
      changed: [
        '<strong>The Scribe (formerly The Translator)</strong> -- tech-writer rewritten as a core agent with dual activation: phase 3b (inline code documentation: headers, docstrings, context comments) and phase 5 (project documentation: API, architecture with Mermaid diagrams, guides, changelogs). Strict style guide: Castilian Spanish without Latinisms, anglicisms allowed, no emojis.',
        '<strong>HARD-GATEs on 5 optional agents</strong> -- data-engineer (migration integrity), ux-reviewer (WCAG 2.1 level A), performance-engineer (performance thresholds), seo-specialist (minimum indexing requirements), github-manager (destructive operations require confirmation).',
        '<strong>Team expanded to 17 agents</strong> -- 9 core (previously 8) + 8 optional (previously 7). All counts updated across web, README and manifest.',
        '<strong>Agent colours unified</strong> -- QA Engineer from red to amber (conflict with security-officer), performance-engineer and copywriter aligned between frontmatter and agent body.',
        '<strong>Persistent memory improved</strong> -- SQLite module optimisations, more efficient queries and better database management between sessions.',
        '<strong>Capture hooks unified</strong> -- <code>memory-capture.py</code> and <code>commit-capture.py</code> merged into <code>activity-capture.py</code>, a single hook with internal dispatch by event type. From 11 to 10 hooks.',
        '<strong>All agents reviewed</strong> -- frontmatter inconsistencies fixed, descriptions aligned with actual capabilities, personalities refined and integration chains updated.',
      ],
      removed: [
        '<strong>Dashboard GUI removed</strong> -- the dashboard web interface (introduced in v0.3.0) is retired as it did not meet usability expectations. Project status functionality is covered by <code>/alfred-dev:status</code>.',
      ],
    },
    {
      version: '0.3.6',
      date: '2026-03-10',
      fixed: [
        '<strong>Core agents registered</strong> -- the core agents were missing from the plugin manifest, so Claude Code could not load their system prompts. All 15 agents (8 core + 7 optional) are now registered and operational.',
        '<strong>Librarian MCP tools</strong> -- the librarian agent referenced 5 MCP tools with incorrect names. Fixed to match the real server tool names.',
        '<strong>Empty dashboard on first session</strong> -- the data pipeline failed in cascade: config without memory, commits without iteration and empty queries. Fixed with auto-config creation, automatic iteration and global fallback.',
        '<strong>Port conflict</strong> -- if another project was using the dashboard ports, it now detects the conflict and finds alternatives automatically.',
      ],
    },
    {
      version: '0.3.5',
      date: '2026-03-10',
      changed: [
        '<strong>SonarQube moved to security-officer</strong> -- the SonarQube analysis is now run by the security-officer instead of the qa-engineer during <code>/alfred-dev:audit</code>. When Docker is operational or authorized, it runs the scanner and integrates findings into its security report.',
        '<strong>Imperative instructions</strong> -- the subagent receives explicit, sequential steps (read the skill, execute all 7 steps, integrate results) instead of a textual reference that could be ignored.',
      ],
    },
    {
      version: '0.3.4',
      date: '2026-03-03',
      fixed: [
        '<strong>Command nomenclature</strong> -- all web commands updated from <code>/alfred X</code> to <code>/alfred-dev:X</code> to reflect the actual Claude Code convention.',
        '<strong>Stats corrected</strong> -- skills from 56 to 59, commands from 10 to 11, hooks from 7 to 11. Aligned with actual implementation.',
        '<strong>Command /alfred-dev:gui visible</strong> -- added to the public commands table in both languages.',
        '<strong>SonarQube integrated in audit</strong> -- the security-officer runs the SonarQube skill after the audit preflight confirms Docker is operational or the user authorizes preparing it.',
        '<strong>Dashboard port file</strong> -- <code>session-start.sh</code> creates <code>.claude/alfred-gui-port</code> and verifies real server connection instead of relying on <code>kill -0</code>.',
        '<strong>Optional agent colours</strong> -- the 5 agents without colour in their frontmatter now have assigned colours for the dashboard.',
      ],
    },
    {
      version: '0.3.3',
      date: '2026-02-24',
      fixed: [
        '<strong>SQLite initialization at startup</strong> -- the memory database is automatically created on each session if it does not exist. Removes the circular dependency that prevented the GUI server from starting on the first session.',
        '<strong>GUI server always operational</strong> -- the dashboard starts from minute 1. The WebSocket is immediately available for the client.',
        '<strong>Agents served via WebSocket</strong> -- the 15-agent catalogue is sent from the server in the <code>init</code> message, removing the hardcoded list from the dashboard.',
        '<strong>Hooks resilient to updates</strong> -- <code>test -f</code> guards on all hooks for graceful degradation when the plugin directory has changed.',
      ],
    },
    {
      version: '0.3.2',
      date: '2026-02-23',
      added: [
        '<strong>Dynamic team composition</strong> -- 4-layer system (heuristic, reasoning, presentation, execution) that suggests optional agents based on the task description. The selection is ephemeral and does not modify persistent configuration.',
        '<strong>run_flow() function</strong> -- entry point for flows with ephemeral session team. Validates structure, injects team and records error diagnostics.',
        '<strong>TASK_KEYWORDS table</strong> -- map of 8 optional agents with contextual keywords and base weights for dynamic composition.',
      ],
      fixed: [
        '<strong>Whole-word matching</strong> -- <code>match_task_keywords()</code> uses word boundaries instead of substrings, eliminating false positives for short keywords.',
        '<strong>Validation feedback</strong> -- the reason for team rejection is recorded in the session for downstream diagnostics.',
        '<strong>Truncation warning</strong> -- task descriptions longer than 10,000 characters emit a warning instead of being silently truncated.',
      ],
      changed: [
        '<code>_KNOWN_OPTIONAL_AGENTS</code> derived from <code>TASK_KEYWORDS</code> (single source of truth). 6 command skills updated. 326 tests.',
      ],
    },
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
        '<strong>Dashboard GUI</strong> (Alpha Phase) -- real-time web dashboard with 7 views: status, timeline, decisions, agents, memory, commits and pinned items. Launched with <code>/alfred-dev:gui</code>.',
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
        '<strong>activity-capture.py hook</strong> -- unified capture hook (workflow events + commits).',
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
        '<code>/alfred-dev:feature</code> allows selecting start phase.',
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
        '<strong>activity-capture.py</strong> -- diagnostics in silent except blocks.',
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
        '<strong>activity-capture.py hook</strong> -- automatic workflow event capture.',
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
        'More reliable version detection in <code>/alfred-dev:update</code>.',
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
    version: 'v0.7.0',
    license: 'MIT License',
    githubUrl: 'https://github.com/686f6c61/alfred-dev',
    docsUrl: 'https://github.com/686f6c61/alfred-dev/tree/main/docs',
    tagline: 'Claude Code plugin. 10 agents. 11 flat skills. 10 hooks. 18 /alfred-dev:* commands. Official MCP. Local Memory UI. Evidence-backed gates. No global /alfred.',
    slogan: 'Software engineering with method for Claude Code.',
    disclaimer: {
      linkText: 'Disclaimer',
      title: 'Disclaimer',
      closeText: 'Close',
      contentHtml: `
        <p><strong>Alfred Dev</strong> is an independent open-source project. It is not affiliated with <strong>Anthropic</strong> or <strong>Claude Code</strong>.</p>
        <p>The software is provided as is, without warranties. You review and approve the actions the plugin proposes.</p>
        <p>Agents use language models that can be wrong. Treat outputs as suggestions.</p>
        <p>Use is subject to the <a href="https://github.com/686f6c61/alfred-dev/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">MIT license</a>.</p>
      `,
    },
  },
};

export default data;
