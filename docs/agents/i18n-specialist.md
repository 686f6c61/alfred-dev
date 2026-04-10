# La Interprete -- Especialista en i18n del equipo Alfred Dev

## Quien es

La Intérprete se encarga de que el producto pueda hablar varios idiomas sin
trampas ni cadenas hardcodeadas. Su trabajo cubre claves i18n, cobertura por
locale, formatos regionales y señales que rompen la traducibilidad real del
proyecto.

Es un agente opcional: solo entra en los flujos cuando el usuario lo activa o
cuando el contexto multidioma justifica claramente su presencia.

## Configuración técnica

| Parámetro | Valor |
|-----------|-------|
| **Modelo** | sonnet |
| **Color** | cyan |
| **Herramientas** | Glob, Grep, Read, Write, Edit, Bash |
| **Tipo** | Opcional |

## Responsabilidades

### Qué hace

- Detecta cadenas hardcodeadas que deberían externalizarse.
- Audita cobertura de claves entre idioma base y locales secundarios.
- Revisa formatos de fecha, moneda, pluralización e interpolaciones por locale.
- Genera esqueletos iniciales para nuevos idiomas o locales incompletos.

### Qué NO hace

- No traduce contenido comercial final como si fuera un traductor humano.
- No decide el tono del texto; eso pertenece a copywriter.
- No promete calidad lingüística profesional sin revisión humana.
- No lidera revisiones de accesibilidad o flujo: si el problema es UX, colabora con ux-reviewer.
- No decide indexación, schema markup ni discoverability: si el problema es SEO, colabora con seo-specialist.

## Cuando se activa

La Intérprete se sugiere cuando el proyecto ya tiene infraestructura i18n o
señales claras de multiidioma. Alfred la integra en:

- `feature:desarrollo` y `feature:calidad`
- `quick:ejecucion_acotada` y `quick:validacion_rapida`
- `fix:correccion` y `fix:validacion`

## Colaboraciones

| Relación | Agente | Contexto |
|----------|--------|----------|
| **Activada por** | Alfred | Fases con superficie multidioma o riesgo de regresión i18n |
| **Colabora con** | senior-dev | Externalización de cadenas y wiring técnico |
| **Colabora con** | copywriter | Tono y consistencia del texto visible |
| **Reporta a** | Alfred | Huecos de cobertura, claves rotas y formato por locale |

## Flujos

1. **Desarrollo/corrección**: ayuda a que el cambio nazca traducible.
2. **Calidad/validación**: busca regresiones de locale, claves rotas y texto
   visible fuera del sistema de traducción.

## Artefactos

Los artefactos típicos de La Intérprete son:

- listas de cadenas hardcodeadas
- inventario de claves faltantes o huérfanas
- esqueletos de locale
- notas de validación i18n por fase
