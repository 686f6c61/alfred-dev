---
name: spelling-check
description: "Verificar ortografía en castellano: tildes, concordancia y erratas en código y documentación. También: ortografía, tildes, erratas, castellano, acentos."
---

# Verificación ortográfica

## Resumen

Este skill verifica la ortografía de los textos generados o existentes en el proyecto: documentación, comentarios de código, mensajes de interfaz, strings visibles para el usuario y commits. La prioridad absoluta son las tildes en castellano, que es el error más frecuente y el que más credibilidad resta.

Escribir bien no es opcional. Un texto con faltas transmite descuido, independientemente de la calidad técnica del código.

## Proceso

### Paso 1: identificar los textos a revisar

Según el contexto:

- **Documentación**: README, docs/, comentarios de cabecera, changelogs.
- **Interfaz**: strings visibles para el usuario (labels, mensajes de error, placeholders, tooltips).
- **Código**: nombres de variables y funciones en castellano (si aplica), comentarios.
- **Git**: mensajes de commit recientes.

### Paso 2: verificar tildes

Lista de palabras que frecuentemente se escriben sin tilde (y deben llevarla):

| Incorrecto | Correcto |
|-----------|----------|
| funcion | función |
| configuracion | configuración |
| informacion | información |
| autenticacion | autenticación |
| descripcion | descripción |
| documentacion | documentación |
| sesion | sesión |
| version | versión |
| conexion | conexión |
| aplicacion | aplicación |
| operacion | operación |
| validacion | validación |
| creacion | creación |
| instalacion | instalación |
| actualizacion | actualización |
| ejecucion | ejecución |
| implementacion | implementación |
| investigacion | investigación |
| auditoria | auditoría |
| automatico | automático |
| codigo | código |
| metodo | método |
| numero | número |
| parametro | parámetro |
| unico | único |
| publico | público |
| tecnico | técnico |
| basico | básico |
| dinamico | dinámico |
| pagina | página |
| tambien | también |
| mas | más (cuando no es conjunción adversativa) |
| como | cómo (interrogativo/exclamativo) |
| que | qué (interrogativo/exclamativo) |

### Paso 3: verificar concordancia

- Género: "la función" (no "el función"), "el parámetro" (no "la parámetro").
- Número: "las funciones devuelven" (no "las funciones devuelve").
- Artículos: "un error" (no "una error"), "una excepción" (no "un excepción").

### Paso 4: verificar puntuación

- Signos de interrogación y exclamación de apertura: "¿Funciona?" (no "Funciona?").
- Comas antes de "pero", "aunque", "sin embargo".
- Punto final en frases completas.

### Paso 5: entregar correcciones

- Listar cada error encontrado con ubicación (fichero:línea), texto incorrecto y corrección.
- Aplicar las correcciones directamente si el usuario lo autoriza.
- Priorizar: primero tildes (más frecuentes y visibles), después concordancia, después puntuación.

## Qué NO hacer

- No cambiar el estilo del texto, solo la ortografía. Las preferencias de redacción son del autor.
- No corregir nombres propios, marcas o términos técnicos en inglés.
- No añadir signos de apertura en contextos donde la convención del proyecto no los usa (algunos proyectos eligen omitirlos en código).
