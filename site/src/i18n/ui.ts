/**
 * Literales cortos de la interfaz de usuario.
 *
 * Este modulo contiene las cadenas breves que aparecen en elementos
 * interactivos de la pagina (botones, tooltips, aria-labels) y que
 * no forman parte del contenido principal. Al estar separados de los
 * datos de contenido, se pueden traducir de forma independiente y
 * mantener sincronizados con facilidad.
 *
 * @module i18n/ui
 */

/** Idiomas soportados por la landing. */
export type Locale = 'es' | 'en';

/** Locale por defecto. */
export const DEFAULT_LOCALE: Locale = 'es';

/**
 * Mapa de literales de UI indexado por clave.
 *
 * Cada clave tiene un valor por cada locale soportado.
 * Las claves usan camelCase para consistencia con el resto del codigo.
 */
export const ui: Record<string, Record<Locale, string>> = {
  // ── Accesibilidad y navegacion ──────────────────────────────
  skipLink: {
    es: 'Saltar al contenido',
    en: 'Skip to content',
  },
  navAriaLabel: {
    es: 'Menu de navegacion',
    en: 'Navigation menu',
  },
  navHamburgerAriaLabel: {
    es: 'Menu de navegacion',
    en: 'Navigation menu',
  },

  // ── Changelog ───────────────────────────────────────────────
  changelogBtn: {
    es: 'Ver changelog',
    en: 'View changelog',
  },
  changelogTitle: {
    es: 'Changelog',
    en: 'Changelog',
  },
  changelogClose: {
    es: 'Cerrar changelog',
    en: 'Close changelog',
  },
  changelogFullLink: {
    es: 'ver completo',
    en: 'view full',
  },

  // ── Copiar al portapapeles ──────────────────────────────────
  copyHint: {
    es: 'clic para copiar',
    en: 'click to copy',
  },
  copiedHint: {
    es: 'copiado',
    en: 'copied',
  },
  installCopied: {
    es: 'Copiado al portapapeles',
    en: 'Copied to clipboard',
  },

  // ── Lightbox de imagenes ────────────────────────────────────
  lightboxClose: {
    es: 'Cerrar imagen',
    en: 'Close image',
  },
  lightboxPrev: {
    es: 'Imagen anterior',
    en: 'Previous image',
  },
  lightboxNext: {
    es: 'Imagen siguiente',
    en: 'Next image',
  },

  // ── FAQ ─────────────────────────────────────────────────────
  faqLabel: {
    es: 'Preguntas frecuentes',
    en: 'Frequently asked questions',
  },

  // ── Selector de idioma ──────────────────────────────────────
  langSwitcher: {
    es: 'English',
    en: 'Español',
  },
  langSwitcherHref: {
    es: '/en/',
    en: '/',
  },

  // ── Instalacion ─────────────────────────────────────────────
  installTabMacos: {
    es: 'macOS',
    en: 'macOS',
  },
  installTabLinux: {
    es: 'Linux',
    en: 'Linux',
  },
  installTabWindows: {
    es: 'Windows',
    en: 'Windows',
  },
  installAriaLabel: {
    es: 'Plataformas de instalacion',
    en: 'Installation platforms',
  },

  // ── Changelog categorias ────────────────────────────────────
  changelogAdded: {
    es: 'Added',
    en: 'Added',
  },
  changelogChanged: {
    es: 'Changed',
    en: 'Changed',
  },
  changelogFixed: {
    es: 'Fixed',
    en: 'Fixed',
  },
} as const;

/**
 * Obtiene un literal de UI para el locale indicado.
 *
 * @param key - Clave del literal (ej. 'skipLink', 'copyHint').
 * @param locale - Idioma deseado. Por defecto el locale principal.
 * @returns El literal traducido, o la clave si no existe.
 *
 * @example
 * ```ts
 * t('copyHint', 'es') // "clic para copiar"
 * t('copyHint', 'en') // "click to copy"
 * ```
 */
export function t(key: string, locale: Locale = DEFAULT_LOCALE): string {
  return ui[key]?.[locale] ?? key;
}
