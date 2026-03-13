---
name: threat-model
description: "Usar para modelar amenazas con metodología STRIDE. También: análisis de amenazas, STRIDE, superficie de ataque, vectores de ataque, modelado de amenazas."
---

# Modelado de amenazas STRIDE

## Resumen

Este skill aplica la metodología STRIDE para identificar y clasificar amenazas de seguridad en el sistema. STRIDE es un modelo desarrollado por Microsoft que categoriza las amenazas en seis tipos, proporcionando un framework sistemático para no dejarse nada en el tintero.

El modelado de amenazas se hace idealmente al principio del desarrollo (cuando es más barato corregir), pero también es valioso como ejercicio periódico para sistemas existentes.

## Proceso

1. **Identificar los componentes del sistema.** Listar todos los elementos relevantes:

   - Aplicaciones y servicios.
   - Bases de datos y almacenes de datos.
   - APIs e interfaces externas.
   - Infraestructura (servidores, redes, balanceadores).
   - Usuarios y roles.
   - Flujos de datos entre componentes.

2. **Generar diagrama de flujo de datos (DFD).** Dibujar con Mermaid los flujos de datos entre componentes, identificando los límites de confianza (trust boundaries). Las amenazas suelen concentrarse en los puntos donde los datos cruzan un límite de confianza.

3. **Aplicar STRIDE a cada componente.** Para cada elemento del diagrama, evaluar las seis categorías:

   | Categoría | Descripción | Pregunta clave |
   |-----------|-------------|----------------|
   | **S**poofing (suplantación) | Un atacante se hace pasar por otro usuario o sistema. | Cómo se verifica la identidad en este punto? |
   | **T**ampering (manipulación) | Un atacante modifica datos en tránsito o en reposo. | Cómo se garantiza la integridad de los datos? |
   | **R**epudiation (repudio) | Un usuario niega haber realizado una acción. | Hay registro de auditoría fiable? |
   | **I**nformation Disclosure (fuga de información) | Datos sensibles se exponen a quien no debería verlos. | Qué datos se exponen y a quién? |
   | **D**enial of Service (denegación de servicio) | El sistema se vuelve inaccesible para usuarios legítimos. | Qué recursos se pueden agotar? |
   | **E**levation of Privilege (elevación de privilegios) | Un usuario obtiene permisos que no le corresponden. | Cómo se aplican los controles de acceso? |

4. **Clasificar cada amenaza por riesgo.** Usar una matriz de probabilidad e impacto:

   - **Probabilidad:** alta (fácil de explotar, atacante poco sofisticado) / media / baja (requiere acceso interno y conocimiento especializado).
   - **Impacto:** crítico (pérdida de datos, brecha de seguridad) / alto (interrupción del servicio) / medio (degradación parcial) / bajo (molestia menor).

5. **Proponer mitigaciones para cada amenaza.** Las mitigaciones deben ser concretas y accionables:

   - No: "mejorar la seguridad".
   - Sí: "implementar rate limiting de 100 peticiones/minuto en el endpoint de login".

6. **Priorizar por ratio riesgo/esfuerzo.** Las mitigaciones de alto impacto y bajo esfuerzo van primero. Las de bajo impacto y alto esfuerzo se documentan pero se posponen.

7. **Documentar el modelo.** Utilizar `templates/threat-model.md` si existe. Guardar en la documentación del proyecto para referencia futura.

## Criterios de éxito

- Todos los componentes del sistema han sido evaluados contra las 6 categorías STRIDE.
- Las amenazas están clasificadas por probabilidad e impacto.
- Cada amenaza tiene al menos una mitigación propuesta.
- Las mitigaciones están priorizadas por ratio riesgo/esfuerzo.
- El modelo de amenazas está documentado y es mantenible.
- Las amenazas y mitigaciones se han registrado en la memoria del proyecto.

## Paso de memoria

Registrar las amenazas identificadas y las mitigaciones propuestas en la memoria del proyecto con `memory_log_decision`. Esto permite hacer seguimiento del estado de las mitigaciones entre sesiones y detectar si aparecen nuevas superficies de ataque con la evolución del sistema.

## Qué NO hacer

- No modelar amenazas en abstracto sin conocer la arquitectura real del sistema. El modelo debe partir de los componentes y flujos de datos concretos, no de una lista genérica.
- No limitarse a las amenazas técnicas. Las amenazas organizativas (ingeniería social, acceso físico, insiders) también son relevantes si el sistema maneja datos sensibles.
- No dejar el modelo de amenazas como un documento estático. Debe revisarse cuando cambia la arquitectura, se añaden integraciones o se despliega en un nuevo entorno.
- No proponer mitigaciones vagas como "mejorar la seguridad". Cada mitigación debe ser concreta, implementable y verificable.
