---
name: repo-setup
description: "Configurar un repositorio GitHub con branch protection, templates y labels"
disable-model-invocation: true
---

# Configurar repositorio GitHub

## Resumen

Este skill configura un repositorio GitHub desde cero o ajusta uno existente para que cumpla con las convenciones de un proyecto profesional. Cubre protección de ramas, plantillas de issues y PR, etiquetas estandarizadas, .gitignore y metadatos del repositorio.

La configuración se realiza íntegramente mediante la CLI `gh`, lo que permite automatizar y reproducir el proceso en cualquier proyecto sin depender de la interfaz web.

## Proceso

1. **Verificar prerrequisitos.** Comprobar que `gh` está instalada y autenticada. Si no lo está, preguntar al usuario si quiere que Alfred la instale. Si acepta, instalarla según la plataforma (`brew install gh` en macOS, `sudo apt install gh` en Linux, `winget install GitHub.cli` en Windows) y lanzar la autenticación con `gh auth login`. Sin esta herramienta no se puede continuar.

2. **Crear el repositorio o verificar el existente.** Si el repositorio no existe, crearlo con `gh repo create`. Si ya existe, verificar que se tiene acceso de administración para poder configurar las protecciones de rama. Establecer la descripción del repositorio y los topics relevantes con `gh repo edit`.

3. **Configurar branch protection en main.** Aplicar las siguientes reglas sobre la rama principal:

   - Requerir pull request antes de hacer merge.
   - Requerir al menos una aprobación.
   - Requerir que los checks de estado pasen antes de hacer merge.
   - No permitir force push.
   - No permitir borrado de la rama.

   Usar `gh api` para configurar las reglas de protección, ya que `gh` no tiene un comando directo para todas las opciones.

4. **Crear templates de issues.** Generar dos plantillas en `.github/ISSUE_TEMPLATE/`:

   - **bug_report.yml**: título, descripción del bug, pasos para reproducir, resultado esperado, resultado actual y entorno (SO, navegador, versión).
   - **feature_request.yml**: título, descripción del problema que se quiere resolver, solución propuesta y alternativas consideradas.

5. **Crear template de PR.** Generar `.github/pull_request_template.md` con secciones: resumen de cambios, motivación, plan de pruebas y checklist (tests, documentación, changelog).

6. **Configurar labels estándar.** Crear las siguientes etiquetas con `gh label create`:

   - Tipo: `bug`, `feature`, `docs`, `refactor`, `security`, `chore`.
   - Prioridad: `priority/critical`, `priority/high`, `priority/medium`, `priority/low`.
   - Estado: `needs-review`, `in-progress`, `blocked`.

   Eliminar las etiquetas por defecto que no se usen para evitar ruido.

7. **Generar .gitignore.** Crear o actualizar el fichero `.gitignore` según el stack del proyecto. Incluir siempre: `.env`, `.env.*`, `node_modules/`, `__pycache__/`, `.DS_Store`, `*.log`, ficheros de IDE (`.idea/`, `.vscode/`).

8. **Verificar la configuración.** Comprobar que las reglas de protección están activas, que los templates se renderizan correctamente al crear un issue o PR nuevo, y que las etiquetas son visibles.

## Que NO hacer

- No mencionar herramientas de IA ni asistentes en ninguno de los artefactos generados (templates, descripción, etc.).
- No configurar reglas de protección que bloqueen al usuario sin posibilidad de override en repositorios personales.
- No asumir que `gh` está instalada: verificar siempre primero.
- No borrar etiquetas existentes sin confirmar con el usuario.
