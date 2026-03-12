## [{{version}}] - {{fecha}}

### Added
{{added}}

### Changed
{{changed}}

### Deprecated
{{deprecated}}

### Removed
{{removed}}

### Fixed
{{fixed}}

### Security
{{security}}

<!-- EJEMPLO COMPLETADO ─────────────────────────────────────────────────

## [0.2.0] - 2026-02-20

### Added
- **Memoria persistente**: base de datos SQLite local por proyecto para
  almacenar decisiones, commits e iteraciones entre sesiones.
- **El Bibliotecario**: agente opcional que responde consultas historicas
  citando fuentes con formato [D#id], [C#sha], [I#id].
- **Servidor MCP**: 15 herramientas para buscar, registrar y consultar
  la memoria desde cualquier agente.
- **Hooks de captura automatica**: memory-capture.py y commit-capture.py
  registran eventos y commits sin intervencion del usuario.

### Changed
- session-start.sh ahora inyecta las decisiones de la iteracion activa
  en el contexto de la sesion.

### Fixed
- Corregido race condition en escritura concurrente al fichero de estado
  cuando dos hooks PostToolUse se ejecutan en paralelo.

### Security
- sanitize_content() aplica 14 patrones regex para detectar y redactar
  secretos antes de persistirlos en la base de datos.
- Permisos 0600 en el fichero de base de datos (solo propietario).

──────────────────────────────────────────────── FIN DEL EJEMPLO -->
