---
name: pr-workflow
description: "Crear pull requests completas con descripcion, labels y reviewers"
disable-model-invocation: true
---

# Crear pull requests completas

## Resumen

Este skill guia el proceso de creacion de una pull request bien documentada, desde la verificacion de cambios hasta la asignacion de reviewers. Una PR no es solo un mecanismo de merge: es una pieza de comunicacion que explica a los revisores que se ha cambiado, por que y como verificarlo.

El objetivo es que cualquier miembro del equipo pueda entender la PR sin necesidad de leer cada linea de codigo antes de abrir el diff.

## Proceso

1. **Verificar el estado de los cambios.** Ejecutar `git diff` y `git status` para confirmar que los cambios pendientes corresponden a lo que se quiere incluir en la PR. Si hay cambios sin commitear, confirmar con el usuario si deben incluirse o quedarse fuera.

2. **Verificar la rama.** Asegurarse de que se trabaja en una rama feature o fix, no directamente en main. Si no existe rama, crearla con un nombre descriptivo: `feature/nombre-funcionalidad` o `fix/descripcion-bug`.

3. **Redactar el titulo.** El titulo debe tener menos de 70 caracteres y describir el cambio de forma clara. Formato recomendado: `tipo: descripcion breve`. Ejemplos:

   - `feat: anadir filtro de busqueda por fecha`
   - `fix: corregir calculo de IVA en facturas`
   - `refactor: extraer logica de validacion a modulo propio`

4. **Redactar la descripcion.** Seguir esta estructura estandarizada:

   ```markdown
   ## Resumen
   - [1-3 puntos explicando que cambia y por que]

   ## Motivacion
   [Por que es necesario este cambio. Enlazar al issue si existe.]

   ## Plan de pruebas
   - [ ] [Pasos concretos para verificar que el cambio funciona]
   - [ ] [Comprobaciones de regresion]

   ## Notas para el revisor
   [Contexto adicional, decisiones de diseno, areas que necesitan atencion especial]
   ```

5. **Asignar labels.** Etiquetar la PR segun el tipo de cambio (`bug`, `feature`, `refactor`, `docs`) y la prioridad si aplica. Usar `gh pr edit --add-label` para asignarlas.

6. **Enlazar issues.** Si la PR resuelve un issue, incluir `Closes #XX` en la descripcion para que GitHub lo cierre automaticamente al hacer merge.

7. **Asignar reviewers.** Seleccionar revisores relevantes segun el area del codigo afectada. Usar `gh pr create --reviewer usuario1,usuario2` o `gh pr edit --add-reviewer` si la PR ya existe.

8. **Crear la PR.** Ejecutar `gh pr create` con titulo, descripcion, labels y reviewers. Verificar que la PR aparece correctamente en GitHub y que los checks de CI arrancan.

9. **Revisar el resultado.** Comprobar que la descripcion se renderiza bien, que los enlaces a issues funcionan y que los reviewers han sido notificados.

## Que NO hacer

- No incluir lineas `Co-Authored-By` ni menciones a asistentes o herramientas de IA en la PR.
- No crear PRs sin descripcion: el titulo no es suficiente para comunicar el contexto.
- No asignar reviewers de forma indiscriminada; elegir a quienes conocen el area afectada.
- No mezclar cambios no relacionados en la misma PR.
