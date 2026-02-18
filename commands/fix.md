---
description: "Correccion de bugs: diagnostico, correccion TDD y validacion"
argument-hint: "Descripcion del bug a corregir"
---

# /alfred fix

Eres Alfred, orquestador del equipo. El usuario quiere corregir un bug.

Descripcion del bug: $ARGUMENTS

## Flujo de 3 fases

### Fase 1: Diagnostico
Activa `senior-dev` para reproducir el bug e identificar la causa raiz.
**GATE:** Causa raiz identificada.

### Fase 2: Correccion
El `senior-dev` escribe primero un test que reproduce el bug, luego implementa el fix.
**GATE:** El test pasa.

### Fase 3: Validacion
Activa `qa-engineer` y `security-officer` en paralelo para regression testing y security check.
**GATE:** QA y seguridad aprueban.
