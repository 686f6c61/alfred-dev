# Alfred Dev -- plan atomizado para endurecer `/alfred audit` con SonarQube

**Fecha:** 2026-03-21
**Objetivo:** evitar que `/alfred audit` omita SonarQube silenciosamente cuando Docker no está disponible o requiere permisos, y dejar el comportamiento cubierto por tests.

## Fase 1 -- Preflight interactivo

**Meta:** decidir antes de lanzar agentes si SonarQube puede ejecutarse realmente.

### Task 1.1 -- Verificar Docker antes de la auditoría
- Ejecutar `docker --version` y `docker info` al inicio de `/alfred audit`.
- Distinguir tres estados:
  - Docker operativo.
  - Docker no instalado.
  - Docker instalado pero daemon inaccesible.

### Task 1.2 -- Pedir confirmación cuando haya impacto en el sistema
- Si Docker no está listo, usar `AskUserQuestion` antes de lanzar agentes.
- Ofrecer continuar sin SonarQube como alternativa explícita.
- Mantener esta pregunta incluso en autopilot.

### Task 1.3 -- Propagar la decisión al `security-officer`
- Si SonarQube está autorizado, obligar a ejecutar el skill.
- Si no lo está, prohibir instalación/arranque y exigir que la omisión quede documentada.

## Fase 2 -- Hardening del skill `sonarqube`

**Meta:** que el skill no asuma permisos ni deje huecos operativos.

### Task 2.1 -- Convertir el paso 1 en un preflight real
- Documentar que no se puede instalar Docker ni arrancar el daemon sin permiso explícito.
- Si la orden viene desde `/alfred audit`, respetar la decisión tomada allí.

### Task 2.2 -- Manejar conflictos frecuentes
- Limpiar contenedor previo `sonarqube-alfred` si existe.
- Detectar puerto 9000 ocupado y escalar al usuario en vez de forzar cambios.

### Task 2.3 -- Garantizar limpieza
- Intentar parar y borrar el contenedor temporal aunque el análisis falle.

## Fase 3 -- Cobertura de regresión

**Meta:** detectar futuras regresiones del contrato textual del plugin.

### Task 3.1 -- Test de contrato para `commands/audit.md`
- Verificar que existe un preflight de Docker.
- Verificar que se usa `AskUserQuestion` si Docker no está listo.
- Verificar que el preflight sigue siendo interactivo incluso en autopilot.

### Task 3.2 -- Test de contrato para `skills/calidad/sonarqube/SKILL.md`
- Verificar que el skill exige permiso explícito antes de instalar o arrancar Docker.
- Verificar que contempla puerto 9000 ocupado y limpieza final.

### Task 3.3 -- Corregir inconsistencias detectadas
- Revisar ayudas o prompts vecinos que fallen en las comprobaciones.

## Fase 4 -- Verificación e instalación

**Meta:** comprobar que Alfred sigue funcionando y dejar la versión corregida instalada en Claude Code.

### Task 4.1 -- Ejecutar tests
- Ejecutar tests nuevos y suite existente.
- Corregir cualquier regresión encontrada.

### Task 4.2 -- Reinstalar el plugin desde la copia local
- Apuntar el marketplace de Claude Code a este repositorio local.
- Reinstalar `alfred-dev`.
- Verificar que el comando instalado contiene el nuevo preflight.
