---
name: structured-data
description: "Generar datos estructurados JSON-LD validados contra schema.org. Activar ante: JSON-LD, schema.org, rich snippets, datos estructurados, marcado semantico"
---

# Generar datos estructurados JSON-LD

## Resumen

Este skill genera datos estructurados en formato JSON-LD basados en el vocabulario de schema.org. Los datos estructurados permiten a los buscadores entender el contenido de una pagina de forma semantica, lo que puede resultar en rich snippets (resultados enriquecidos) que mejoran la visibilidad y el CTR en las paginas de resultados.

El formato JSON-LD es el recomendado por Google porque se inserta como un bloque `<script>` independiente en el `<head>`, sin modificar el HTML visible. Esto lo hace mas facil de mantener y menos propenso a errores que los formatos alternativos (Microdata, RDFa).

## Proceso

1. **Identificar los tipos de schema aplicables.** Analizar cada pagina del sitio para determinar que tipos de datos estructurados son relevantes. Los tipos mas comunes son:

   - **Organization**: pagina principal o "Acerca de". Campos obligatorios: `name`, `url`, `logo`. Recomendados: `sameAs` (perfiles sociales), `contactPoint`, `address`.
   - **WebSite**: pagina principal. Campos obligatorios: `name`, `url`. Recomendados: `potentialAction` con SearchAction si hay buscador interno.
   - **Article / BlogPosting**: paginas de blog o noticias. Campos obligatorios: `headline`, `author`, `datePublished`, `image`. Recomendados: `dateModified`, `publisher`, `description`.
   - **Product**: paginas de producto. Campos obligatorios: `name`, `image`, `offers` (con `price`, `priceCurrency`, `availability`). Recomendados: `brand`, `sku`, `aggregateRating`.
   - **FAQPage**: paginas con preguntas frecuentes. Campos obligatorios: `mainEntity` con array de `Question`, cada una con `acceptedAnswer`.
   - **BreadcrumbList**: todas las paginas con navegacion de migas de pan. Campos obligatorios: `itemListElement` con `position`, `name` e `item` (URL).

2. **Generar el markup JSON-LD para cada pagina.** Crear el bloque `<script type="application/ld+json">` correspondiente. Ejemplo para Organization:

   ```json
   {
     "@context": "https://schema.org",
     "@type": "Organization",
     "name": "Nombre de la empresa",
     "url": "https://ejemplo.com",
     "logo": "https://ejemplo.com/logo.png",
     "sameAs": [
       "https://twitter.com/ejemplo",
       "https://linkedin.com/company/ejemplo"
     ]
   }
   ```

3. **Combinar tipos cuando corresponda.** Una pagina puede tener multiples bloques JSON-LD. Por ejemplo, la pagina principal puede incluir Organization, WebSite y BreadcrumbList simultaneamente. Cada uno va en su propio bloque `<script>` o se combinan en un array con `@graph`.

4. **Validar el markup.** Antes de publicar, verificar cada bloque contra:

   - **Schema Markup Validator** (validator.schema.org): comprueba la sintaxis y el vocabulario.
   - **Rich Results Test** (search.google.com/test/rich-results): comprueba si Google puede generar resultados enriquecidos a partir del markup.

   Corregir cualquier error o advertencia antes de desplegar.

5. **Insertar en el HTML.** Colocar los bloques JSON-LD dentro del `<head>` de cada pagina. Si se usa un framework o CMS, verificar que no genera duplicados.

## Que NO hacer

- No inventar datos que no existen en la pagina: el markup debe reflejar el contenido visible.
- No usar tipos de schema incorrectos (por ejemplo, marcar un articulo como Product).
- No omitir campos obligatorios, ya que el markup no generara rich snippets sin ellos.
- No asumir que el markup es correcto sin validarlo: un JSON mal formado se ignora silenciosamente.
