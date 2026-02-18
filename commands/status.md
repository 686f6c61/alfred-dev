---
description: "Muestra el estado de la sesion activa de Alfred Dev"
---

# Estado de la sesion

Lee el fichero `.claude/alfred-dev-state.json`. Si no existe, informa de que no hay sesion activa.

Si existe, presenta:
- Comando activo y descripcion
- Fase actual y numero de fase
- Fases completadas con timestamps y artefactos generados
- Gates pendientes o fallidas
- Dependencias nuevas anadidas
- Hallazgos de seguridad
- Notas acumuladas

Presenta la informacion de forma legible con tablas y formato claro.
