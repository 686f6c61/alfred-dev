/**
 * Tipos TypeScript para la landing page de Alfred Dev.
 *
 * Este modulo centraliza todas las interfaces que describen los datos
 * de contenido de la pagina. Los ficheros de datos (data.es.ts, data.en.ts)
 * exportan objetos conformes a PageData, y los layouts y componentes Astro
 * los consumen con tipado estricto.
 *
 * @module types
 */

// ──────────────────────────────────────────────────────────────────
// Meta y navegacion
// ──────────────────────────────────────────────────────────────────

/** Meta tags de la pagina: title, description, Open Graph y Twitter Card. */
export interface PageMeta {
  /** Titulo del documento (<title>). */
  title: string;
  /** Meta description para motores de busqueda. */
  description: string;
  /** URL canonica de la pagina. */
  canonical: string;
  /** Idioma principal (es_ES, en_US...). */
  locale: string;
  /** Propiedades Open Graph. */
  og: {
    type: string;
    title: string;
    description: string;
    url: string;
    siteName: string;
    locale: string;
    image: string;
    imageWidth: number;
    imageHeight: number;
    imageType: string;
  };
  /** Propiedades Twitter Card. */
  twitter: {
    card: string;
    title: string;
    description: string;
    image: string;
  };
}

/** Enlace de navegacion con icono SVG inline. */
export interface NavLink {
  /** Ancla destino (#agentes, #flujos...). */
  href: string;
  /** Texto visible del enlace. */
  label: string;
  /**
   * Contenido SVG del icono (elementos internos del <svg>).
   * Cada string es un fragmento HTML valido para inyectar dentro del <svg>.
   */
  svgContent: string;
}

// ──────────────────────────────────────────────────────────────────
// Hero y stats
// ──────────────────────────────────────────────────────────────────

/** Boton CTA del hero con comando copiable. */
export interface HeroCta {
  /** Etiqueta de plataforma (macOS / Linux, Windows...). */
  label: string;
  /** Comando completo que se copia al portapapeles. */
  command: string;
  /** Texto aria-label para accesibilidad. */
  ariaLabel: string;
}

/** Seccion hero de la landing. */
export interface HeroData {
  /** Titulo principal con HTML inline (soporta <br>, <em>, etc.). */
  titleHtml: string;
  /** Texto de plataforma con HTML inline (Claude Code, OpenCode...). */
  platformHtml: string;
  /** Subtitulo descriptivo (texto plano). */
  subtitle: string;
  /** Botones CTA con comando de instalacion. */
  ctas: HeroCta[];
}

/** Cifra destacada de la barra de stats. */
export interface Stat {
  /** Valor numerico. */
  number: number;
  /** Etiqueta descriptiva. */
  label: string;
}

// ──────────────────────────────────────────────────────────────────
// Agentes
// ──────────────────────────────────────────────────────────────────

/**
 * Agente del equipo Alfred Dev.
 *
 * Cada agente tiene un rol definido, personalidad propia y frase
 * caracteristica. Los agentes de nucleo estan siempre activos; los
 * opcionales se activan con /alfred config.
 */
export interface Agent {
  /** Nombre publico del agente. */
  name: string;
  /** Modelo de LLM que utiliza (opus, sonnet...). */
  model: string;
  /** Alias descriptivo del rol (Mayordomo jefe, Senior Dev...). */
  alias: string;
  /** Descripcion breve de sus responsabilidades. */
  role: string;
  /** Frase caracteristica con comillas. */
  phrase: string;
  /** Color CSS del agente (variable CSS o valor directo). */
  color: string;
}

// ──────────────────────────────────────────────────────────────────
// Flujos de trabajo
// ──────────────────────────────────────────────────────────────────

/**
 * Flujo de trabajo orquestado por Alfred.
 *
 * Cada flujo tiene un comando, fases secuenciales y quality gates
 * entre ellas. Los agentes opcionales se integran automaticamente
 * en las fases que les corresponden.
 */
export interface WorkflowFlow {
  /** Comando que inicia el flujo (/alfred feature, /alfred fix...). */
  command: string;
  /** Subtitulo corto (Ciclo completo, Correccion rapida...). */
  subtitle: string;
  /** Descripcion de lo que hace el flujo. */
  description: string;
  /** Nombres de las fases secuenciales. */
  stages: string[];
}

// ──────────────────────────────────────────────────────────────────
// Quality gates
// ──────────────────────────────────────────────────────────────────

/** Quality gate individual. */
export interface Gate {
  /** Texto descriptivo de lo que comprueba la gate. */
  text: string;
  /** Indica si es una gate de agente opcional. */
  optional?: boolean;
}

// ──────────────────────────────────────────────────────────────────
// Skills
// ──────────────────────────────────────────────────────────────────

/** Skill individual dentro de un dominio. */
export interface Skill {
  /** Nombre tecnico del skill (write-prd, tdd-cycle...). */
  name: string;
  /** Descripcion breve de lo que hace. */
  description: string;
}

/** Dominio de skills (agrupacion tematica). */
export interface SkillDomain {
  /** Nombre del dominio (Producto, Seguridad...). */
  name: string;
  /** Lista de skills dentro del dominio. */
  skills: Skill[];
  /** Indica si pertenece a un agente opcional. */
  optional?: boolean;
}

// ──────────────────────────────────────────────────────────────────
// Infraestructura
// ──────────────────────────────────────────────────────────────────

/** Elemento de infraestructura (hook, template o modulo core). */
export interface InfraItem {
  /** Nombre del fichero o modulo. */
  name: string;
  /**
   * Etiqueta descriptiva.
   * Para hooks es el tipo de evento (SessionStart, PreToolUse...).
   * Para templates y core es la descripcion breve.
   */
  label: string;
}

/** Grupo de infraestructura (hooks, templates, core). */
export interface InfraGroup {
  /** Titulo del grupo. */
  title: string;
  /** Elementos del grupo. */
  items: InfraItem[];
  /** Nota adicional al pie del grupo (ej. "114 passing"). */
  footnote?: string;
}

// ──────────────────────────────────────────────────────────────────
// Comandos
// ──────────────────────────────────────────────────────────────────

/** Comando de la interfaz de Alfred Dev. */
export interface Command {
  /** Texto del comando (/alfred, /alfred feature...). */
  command: string;
  /** Descripcion de lo que hace. */
  description: string;
}

// ──────────────────────────────────────────────────────────────────
// Stack detection
// ──────────────────────────────────────────────────────────────────

/** Stack tecnologico detectable por Alfred. */
export interface DetectableStack {
  /** Nombre del lenguaje/plataforma. */
  name: string;
  /** Descripcion con gestores de paquetes y frameworks. */
  description: string;
}

// ──────────────────────────────────────────────────────────────────
// Casos de uso
// ──────────────────────────────────────────────────────────────────

/**
 * Caso de uso de la seccion "Como se usa".
 *
 * Cada caso describe un escenario real paso a paso, desde la
 * invocacion del comando hasta el resultado final.
 */
export interface UseCase {
  /** Categoria (Desarrollo, Correccion, Investigacion...). */
  category: string;
  /** Color CSS de la etiqueta. */
  color: string;
  /** Color de fondo de la etiqueta (con transparencia). */
  background: string;
  /** Titulo del caso de uso. */
  title: string;
  /** Comando que se ejecuta (puede estar vacio en el caso automatico). */
  command?: string;
  /**
   * Pasos del flujo. Si es un caso con descripcion libre (como el
   * de proteccion automatica), se usa `description` en su lugar.
   */
  steps?: string[];
  /** Descripcion HTML libre (para casos sin pasos ordenados). */
  description?: string;
  /** Si true, la tarjeta ocupa todo el ancho (grid-column: 1 / -1). */
  wide?: boolean;
}

// ──────────────────────────────────────────────────────────────────
// Memoria persistente
// ──────────────────────────────────────────────────────────────────

/** Nodo del diagrama de trazabilidad. */
export interface TraceabilityNode {
  /** Texto visible. */
  label: string;
  /** Color CSS del nodo. */
  color: string;
  /** Color de fondo con transparencia. */
  background: string;
  /** Color del borde. */
  borderColor: string;
}

/** Tarjeta de componente de la seccion de memoria. */
export interface MemoryCard {
  /** Titulo de la tarjeta. */
  title: string;
  /** Contenido descriptivo con HTML inline. */
  descriptionHtml: string;
}

/** FAQ inline de la seccion de memoria. */
export interface MemoryFaqItem {
  /** Pregunta. */
  question: string;
  /** Respuesta con HTML inline. */
  answerHtml: string;
}

/** Datos del Bibliotecario (agente de memoria). */
export interface LibrarianData {
  /** Titulo del agente. */
  title: string;
  /** Subtitulo. */
  subtitle: string;
  /** Parrafos descriptivos con HTML inline. */
  descriptionHtml: string[];
  /** Ejemplo de consulta interactiva. */
  example: {
    /** Etiqueta del ejemplo. */
    label: string;
    /** Pregunta de ejemplo. */
    question: string;
    /** Respuesta de ejemplo con HTML inline. */
    answerHtml: string;
  };
  /** Nota de activacion con HTML inline. */
  activationHtml: string;
}

/** Datos completos de la seccion de memoria. */
export interface MemorySection {
  /** Etiqueta de la seccion. */
  sectionLabel: string;
  /** Titulo principal. */
  title: string;
  /** Descripcion con HTML inline. */
  descriptionHtml: string;
  /** Diagrama de trazabilidad. */
  traceability: {
    title: string;
    descriptionHtml: string;
    nodes: TraceabilityNode[];
  };
  /** Tarjetas de componentes. */
  cards: MemoryCard[];
  /** Datos del Bibliotecario. */
  librarian: LibrarianData;
  /** FAQ inline de memoria. */
  faq: MemoryFaqItem[];
}

// ──────────────────────────────────────────────────────────────────
// Instalacion
// ──────────────────────────────────────────────────────────────────

/** Tab de instalacion por plataforma. */
export interface InstallTab {
  /** Identificador del tab (macos, linux, windows). */
  id: string;
  /** Etiqueta visible. */
  label: string;
  /** Comando de instalacion. */
  command: string;
  /** Requisitos con HTML inline. */
  requirementsHtml: string;
}

/** Tarjeta de desinstalacion. */
export interface UninstallCard {
  /** Titulo (macOS / Linux, Windows). */
  title: string;
  /** Comando de desinstalacion. */
  command: string;
  /** aria-label para accesibilidad. */
  ariaLabel: string;
}

/** Datos de la seccion de instalacion. */
export interface InstallSection {
  /** Etiqueta de la seccion. */
  sectionLabel: string;
  /** Titulo principal. */
  title: string;
  /** Descripcion. */
  description: string;
  /** Tabs por plataforma. */
  tabs: InstallTab[];
  /** Desinstalacion. */
  uninstall: {
    title: string;
    description: string;
    cards: UninstallCard[];
  };
  /** Actualizacion. */
  update: {
    title: string;
    descriptionHtml: string;
  };
}

// ──────────────────────────────────────────────────────────────────
// Configuracion
// ──────────────────────────────────────────────────────────────────

/** Bloque explicativo de configuracion. */
export interface ConfigBlock {
  /** Titulo del bloque. */
  title: string;
  /** Descripcion con HTML inline. */
  descriptionHtml: string;
}

/** Datos de la seccion de configuracion. */
export interface ConfigSection {
  /** Etiqueta de la seccion. */
  sectionLabel: string;
  /** Titulo principal. */
  title: string;
  /** Descripcion con HTML inline. */
  descriptionHtml: string;
  /** Contenido YAML del fichero de ejemplo. */
  yamlExample: string;
  /** Bloques explicativos de la columna derecha. */
  blocks: ConfigBlock[];
}

// ──────────────────────────────────────────────────────────────────
// FAQ
// ──────────────────────────────────────────────────────────────────

/**
 * Pregunta frecuente con icono SVG.
 *
 * El SVG path se extrae del atributo `d` de cada <path> dentro
 * del icono asociado a la pregunta en el HTML original.
 */
export interface FaqItem {
  /**
   * Contenido SVG del icono (elementos internos del <svg>).
   * Fragmento HTML valido para inyectar dentro de un <svg>.
   */
  svgContent: string;
  /** Texto de la pregunta. */
  question: string;
  /** Texto de la respuesta con HTML inline. */
  answerHtml: string;
}

// ──────────────────────────────────────────────────────────────────
// Changelog
// ──────────────────────────────────────────────────────────────────

/** Version del changelog con sus categorias (added, changed, fixed). */
export interface ChangelogVersion {
  /** Numero de version (0.3.1, 0.2.0...). */
  version: string;
  /** Fecha de publicacion (YYYY-MM-DD). */
  date: string;
  /** Funcionalidades nuevas. */
  added?: string[];
  /** Cambios en funcionalidades existentes. */
  changed?: string[];
  /** Correcciones de errores. */
  fixed?: string[];
}

// ──────────────────────────────────────────────────────────────────
// Dashboard
// ──────────────────────────────────────────────────────────────────

/** Imagen de la galeria del dashboard. */
export interface DashboardImage {
  /** Ruta relativa a la imagen. */
  src: string;
  /** Texto alternativo para accesibilidad. */
  alt: string;
  /** Pie de imagen visible. */
  caption: string;
}

/** Feature del dashboard. */
export interface DashboardFeature {
  /** Titulo de la feature. */
  title: string;
  /** Descripcion breve. */
  description: string;
}

/** Datos de la seccion del dashboard. */
export interface DashboardSection {
  /** Etiqueta de la seccion. */
  sectionLabel: string;
  /** Titulo principal. */
  title: string;
  /** Descripcion con HTML inline. */
  descriptionHtml: string;
  /** Imagen hero (primera, a pantalla completa). */
  heroImage: DashboardImage;
  /** Imagenes de la cuadricula. */
  gridImages: DashboardImage[];
  /** Features destacadas. */
  features: DashboardFeature[];
}

// ──────────────────────────────────────────────────────────────────
// Secciones con header estandar
// ──────────────────────────────────────────────────────────────────

/** Header reutilizable de seccion. */
export interface SectionHeader {
  /** Etiqueta superior (section-label). */
  label: string;
  /** Color CSS de la etiqueta (por defecto blue). */
  labelColor?: string;
  /** Titulo de la seccion. */
  title: string;
  /** Descripcion de la seccion. */
  description?: string;
}

/** Nota contextual sobre agentes opcionales en flujos. */
export interface OptionalAgentsNote {
  /** Contenido HTML de la nota. */
  html: string;
}

/** Elemento de proteccion automatica (caso de uso wide). */
export interface ProtectionItem {
  /** Titulo en negrita. */
  title: string;
  /** Descripcion. */
  description: string;
}

// ──────────────────────────────────────────────────────────────────
// Footer
// ──────────────────────────────────────────────────────────────────

/** Datos del footer. */
export interface FooterData {
  /** Version actual. */
  version: string;
  /** Licencia. */
  license: string;
  /** URL de GitHub. */
  githubUrl: string;
  /** URL de documentacion tecnica. */
  docsUrl: string;
  /** Texto de la segunda linea. */
  tagline: string;
  /** Texto de la tercera linea (slogan). */
  slogan: string;
}

// ──────────────────────────────────────────────────────────────────
// PageData (interfaz raiz)
// ──────────────────────────────────────────────────────────────────

/**
 * Interfaz raiz que agrupa todos los datos que necesita una pagina
 * de la landing de Alfred Dev.
 *
 * Los ficheros de datos (data.es.ts, data.en.ts) exportan un objeto
 * conforme a esta interfaz, y el layout principal lo recibe como prop.
 */
export interface PageData {
  /** Meta tags de la pagina. */
  meta: PageMeta;
  /** Enlaces de navegacion con iconos SVG. */
  nav: NavLink[];
  /** Seccion hero. */
  hero: HeroData;
  /** Cifras destacadas. */
  stats: Stat[];
  /** Seccion de agentes de nucleo. */
  coreAgents: {
    header: SectionHeader;
    agents: Agent[];
  };
  /** Seccion de agentes opcionales. */
  optionalAgents: {
    header: SectionHeader;
    agents: Agent[];
  };
  /** Seccion del dashboard. */
  dashboard: DashboardSection;
  /** Seccion de flujos de trabajo. */
  workflows: {
    header: SectionHeader;
    flows: WorkflowFlow[];
  };
  /** Seccion de quality gates. */
  gates: {
    header: SectionHeader;
    /** Etiqueta del grupo de nucleo. */
    coreLabel: string;
    /** Gates del nucleo. */
    core: Gate[];
    /** Etiqueta del grupo opcional. */
    optionalLabel: string;
    /** Gates opcionales. */
    optional: Gate[];
  };
  /** Seccion de skills. */
  skills: {
    header: SectionHeader;
    domains: SkillDomain[];
  };
  /** Seccion de infraestructura. */
  infra: {
    header: SectionHeader;
    groups: InfraGroup[];
  };
  /** Seccion de comandos. */
  commands: {
    header: SectionHeader;
    list: Command[];
    /** Nota sobre agentes opcionales en flujos. */
    optionalNote: OptionalAgentsNote;
  };
  /** Seccion de deteccion de stack. */
  stacks: {
    header: SectionHeader;
    list: DetectableStack[];
  };
  /** Seccion de casos de uso. */
  useCases: {
    header: SectionHeader;
    cases: UseCase[];
  };
  /** Seccion de memoria persistente. */
  memory: MemorySection;
  /** Seccion de instalacion. */
  install: InstallSection;
  /** Seccion de configuracion. */
  config: ConfigSection;
  /** Seccion de FAQ. */
  faq: {
    header: SectionHeader;
    items: FaqItem[];
  };
  /** Changelog completo. */
  changelog: ChangelogVersion[];
  /** Footer. */
  footer: FooterData;
}
