---
name: meta-tags
description: "Auditar y corregir meta tags para SEO y redes sociales. Activar ante: SEO basico, meta description, Open Graph, Twitter Cards, titulo de pagina, etiquetas meta"
---

# Auditar y corregir meta tags

## Resumen

Este skill realiza una auditoria completa de las meta tags de un sitio web, cubriendo tanto las necesarias para SEO en buscadores como las requeridas para que el contenido se comparta correctamente en redes sociales. Una pagina sin meta tags adecuadas pierde visibilidad en buscadores y se muestra de forma pobre cuando se comparte un enlace.

La auditoria se hace pagina por pagina, porque cada URL necesita meta tags unicos y relevantes para su contenido especifico.

## Proceso

1. **Obtener el listado de paginas a auditar.** Identificar las paginas del sitio que necesitan revision. Priorizar las paginas mas importantes: home, landing pages, paginas de producto y contenido principal. Si hay sitemap.xml, usarlo como punto de partida.

2. **Auditar las meta tags basicas de cada pagina.** Para cada URL, verificar la presencia y calidad de:

   - **title**: presente, unico por pagina, entre 50 y 60 caracteres. Debe incluir la palabra clave principal y el nombre de marca al final.
   - **meta description**: presente, unica por pagina, entre 150 y 160 caracteres. Debe resumir el contenido e incentivar el clic.
   - **canonical**: presente y apuntando a la URL canonica correcta. Critico para evitar contenido duplicado.
   - **lang**: atributo en la etiqueta `<html>` con el idioma correcto (por ejemplo, `es` o `es-ES`).
   - **viewport**: `<meta name="viewport" content="width=device-width, initial-scale=1">` para responsive.

3. **Auditar las meta tags de Open Graph.** Estas controlan como se muestra la pagina al compartirla en Facebook, LinkedIn y otras plataformas:

   - **og:title**: puede diferir del title, optimizado para engagement social.
   - **og:description**: resumen atractivo del contenido.
   - **og:image**: imagen de al menos 1200x630 px. Verificar que la URL es absoluta y accesible.
   - **og:url**: URL canonica de la pagina.
   - **og:type**: `website`, `article`, `product` segun corresponda.
   - **og:site_name**: nombre del sitio.

4. **Auditar las meta tags de Twitter Card.** Controlan la visualizacion al compartir en Twitter/X:

   - **twitter:card**: `summary_large_image` para contenido con imagen prominente, `summary` para el resto.
   - **twitter:title**: titulo para la card.
   - **twitter:description**: descripcion para la card.
   - **twitter:image**: imagen para la card (puede reutilizar og:image).

5. **Generar el informe de hallazgos.** Para cada pagina, listar las meta tags que faltan, las que tienen valores incorrectos (demasiado largas, duplicadas entre paginas, URLs rotas en imagenes) y las que son correctas.

6. **Generar las correcciones.** Proporcionar el HTML exacto de las meta tags corregidas o nuevas para cada pagina, listas para copiar e insertar en el `<head>` del documento.

7. **Verificar las correcciones.** Tras aplicar los cambios, usar herramientas de validacion como el Facebook Sharing Debugger y el Twitter Card Validator para confirmar que las tarjetas se generan correctamente.

## Que NO hacer

- No usar la misma meta description en todas las paginas: Google las ignora si detecta duplicacion.
- No superar los limites de caracteres recomendados, ya que los buscadores truncan el texto.
- No usar imagenes de Open Graph con URLs relativas: deben ser absolutas.
- No olvidar la etiqueta canonical, especialmente en sitios con parametros de URL o paginacion.
