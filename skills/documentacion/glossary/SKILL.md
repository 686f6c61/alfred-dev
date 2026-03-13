---
name: glossary
description: "Crear y mantener un glosario de términos del proyecto para evitar ambigüedades. Activar ante: glosario, definir terminos, vocabulario del proyecto, que significa"
---

# Corpus lingüístico / Glosario del proyecto

## Resumen

Este skill crea y mantiene un glosario de términos del proyecto: un documento de referencia donde cada concepto tiene una definición única, consensuada y sin ambigüedades. El objetivo es que todo el equipo hable el mismo idioma: cuando alguien dice "usuario", todos entienden lo mismo.

Las malas interpretaciones entre miembros del equipo son una de las fuentes más frecuentes de bugs y retrabajos. Un glosario bien mantenido previene estos problemas de raíz.

## Proceso

### Paso 1: identificar términos clave

- Revisar el código fuente: nombres de entidades, modelos, servicios, tipos.
- Revisar la documentación existente: README, PRDs, historias de usuario.
- Identificar términos que se usan de forma inconsistente o ambigua.
- Preguntar al usuario si hay términos que generen confusión en el equipo.

### Paso 2: crear el fichero de glosario

Crear `docs/glossary.md` con la siguiente estructura:

```markdown
# Glosario del proyecto

| Término | Definición | Contexto | No confundir con |
|---------|-----------|----------|------------------|
| Usuario | Persona registrada con cuenta activa | Backend, API | Visitante (no registrado) |
| Sesión | Período de actividad autenticada | Auth | Conexión (socket) |
```

Cada entrada incluye:
- **Término**: la palabra o expresión exacta.
- **Definición**: qué significa en el contexto de este proyecto. Una frase, precisa.
- **Contexto**: dónde se usa (módulo, capa, dominio).
- **No confundir con**: términos similares que significan otra cosa.

### Paso 3: vincular con el código

- Verificar que los nombres en el código (variables, clases, funciones) son coherentes con el glosario.
- Si hay inconsistencias, proponer renombramientos o documentar la discrepancia.

### Paso 4: mantener actualizado

- Cada vez que se introduce un concepto nuevo en el proyecto, añadirlo al glosario.
- Si un término cambia de significado, actualizar la definición y notificar al equipo.

## Qué NO hacer

- No incluir términos genéricos de programación (API, endpoint, función). Solo términos específicos del dominio del proyecto.
- No escribir definiciones largas. Una frase por término, dos como máximo.
- No crear el glosario y olvidarlo. Un glosario desactualizado es peor que no tener ninguno.
