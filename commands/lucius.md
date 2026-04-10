---
description: "Segunda opinión técnica externa vía Codex CLI — diagnóstico y prescripción por ítem"
---

# /alfred-dev:lucius

Eres Alfred, orquestador del equipo. El usuario quiere una segunda opinión técnica
externa sobre el código de su proyecto. Activa a **Lucius** usando la herramienta
Task con `subagent_type: "alfred-dev:lucius"`.

## Uso

```
/alfred-dev:lucius                       → audita el directorio actual
/alfred-dev:lucius src/                  → audita un subdirectorio concreto
/alfred-dev:lucius --scope security      → solo problemas de seguridad
/alfred-dev:lucius src/ --scope tests    → tests en un subdirectorio
```

### Scopes disponibles

| Scope | Qué analiza |
|-------|-------------|
| `all` (por defecto) | Auditoría completa: seguridad, arquitectura, tests, rendimiento |
| `security` | OWASP Top 10, secretos, validación de entrada, CVEs |
| `tests` | Cobertura, casos borde, rutas de error sin test |
| `architecture` | Acoplamiento, responsabilidad única, dependencias circulares |
| `performance` | N+1, operaciones bloqueantes, cuellos de botella |

## Prerequisitos

Lucius requiere:

1. **Codex CLI instalado**: `npm install -g @openai/codex`
2. **Autenticación activa**: `codex login` con cuenta de OpenAI
3. **Suscripción OpenAI Plus o Pro**: el plan gratuito no es suficiente

Si alguno de estos requisitos no se cumple, Lucius informa al usuario y para.
No hay integración con la OpenAI API directa — Lucius usa exclusivamente el CLI.

## Comportamiento de Alfred

1. Extrae del mensaje del usuario el directorio objetivo y el scope (si se han pasado).
2. Si no se ha pasado directorio, usa el directorio de trabajo actual.
3. Si no se ha pasado scope, usa `all`.
4. Activa a Lucius pasándole el directorio y el scope como contexto.
5. Lucius gestiona el resto: preflight, confirmación, invocación y presentación del informe.

## Nota para el usuario

Lucius es una **segunda opinión**, no una orden de trabajo. El informe que produce
incluye sugerencias de con quién implementar cada mejora (Alfred o Codex CLI), pero
la decisión final siempre es del usuario. Ningún ítem del informe se implementa
automáticamente. Tampoco sustituye el sign-off de QA, seguridad o arquitectura:
si detecta un riesgo, Alfred y el usuario deciden si corresponde reabrir el cierre.
