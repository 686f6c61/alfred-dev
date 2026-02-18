---
description: "Configura Alfred Dev: autonomia, stack, compliance y personalidad"
---

# Configuracion de Alfred Dev

Lee el fichero `.claude/alfred-dev.local.md` si existe. Si no existe, crealo con la configuracion por defecto.

Presenta al usuario la configuracion actual organizada en secciones:

1. **Autonomia por fase** (interactivo/semi-autonomo/autonomo): producto, arquitectura, desarrollo, seguridad, calidad, documentacion, devops
2. **Proyecto** (detectado o manual): nombre, lenguaje, framework, runtime, gestor de paquetes, base de datos, ORM
3. **Compliance**: RGPD, NIS2, CRA, sector, jurisdiccion
4. **Integraciones**: CI, contenedores, registro, hosting, monitoring
5. **Personalidad**: nivel de sarcasmo (1-5), celebrar victorias, insultar malas practicas

Usa AskUserQuestion para preguntar que seccion quiere modificar. Despues de cada cambio, actualiza el fichero .local.md.

Si el proyecto no tiene configuracion y hay ficheros en el directorio actual, ejecuta deteccion automatica de stack y presenta los resultados al usuario para confirmar.
