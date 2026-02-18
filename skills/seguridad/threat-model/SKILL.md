---
name: threat-model
description: "Usar para modelar amenazas con metodologia STRIDE"
---

# Modelado de amenazas STRIDE

## Resumen

Este skill aplica la metodologia STRIDE para identificar y clasificar amenazas de seguridad en el sistema. STRIDE es un modelo desarrollado por Microsoft que categoriza las amenazas en seis tipos, proporcionando un framework sistematico para no dejarse nada en el tintero.

El modelado de amenazas se hace idealmente al principio del desarrollo (cuando es mas barato corregir), pero tambien es valioso como ejercicio periodico para sistemas existentes.

## Proceso

1. **Identificar los componentes del sistema.** Listar todos los elementos relevantes:

   - Aplicaciones y servicios.
   - Bases de datos y almacenes de datos.
   - APIs y interfaces externas.
   - Infraestructura (servidores, redes, balanceadores).
   - Usuarios y roles.
   - Flujos de datos entre componentes.

2. **Generar diagrama de flujo de datos (DFD).** Dibujar con Mermaid los flujos de datos entre componentes, identificando los limites de confianza (trust boundaries). Las amenazas suelen concentrarse en los puntos donde los datos cruzan un limite de confianza.

3. **Aplicar STRIDE a cada componente.** Para cada elemento del diagrama, evaluar las seis categorias:

   | Categoria | Descripcion | Pregunta clave |
   |-----------|-------------|----------------|
   | **S**poofing (suplantacion) | Un atacante se hace pasar por otro usuario o sistema. | Como se verifica la identidad en este punto? |
   | **T**ampering (manipulacion) | Un atacante modifica datos en transito o en reposo. | Como se garantiza la integridad de los datos? |
   | **R**epudiation (repudio) | Un usuario niega haber realizado una accion. | Hay registro de auditoria fiable? |
   | **I**nformation Disclosure (fuga de informacion) | Datos sensibles se exponen a quien no deberia verlos. | Que datos se exponen y a quien? |
   | **D**enial of Service (denegacion de servicio) | El sistema se vuelve inaccesible para usuarios legitimos. | Que recursos se pueden agotar? |
   | **E**levation of Privilege (elevacion de privilegios) | Un usuario obtiene permisos que no le corresponden. | Como se aplican los controles de acceso? |

4. **Clasificar cada amenaza por riesgo.** Usar una matriz de probabilidad e impacto:

   - **Probabilidad:** alta (facil de explotar, atacante poco sofisticado) / media / baja (requiere acceso interno y conocimiento especializado).
   - **Impacto:** critico (perdida de datos, brecha de seguridad) / alto (interrupcion del servicio) / medio (degradacion parcial) / bajo (molestia menor).

5. **Proponer mitigaciones para cada amenaza.** Las mitigaciones deben ser concretas y accionables:

   - No: "mejorar la seguridad".
   - Si: "implementar rate limiting de 100 peticiones/minuto en el endpoint de login".

6. **Priorizar por ratio riesgo/esfuerzo.** Las mitigaciones de alto impacto y bajo esfuerzo van primero. Las de bajo impacto y alto esfuerzo se documentan pero se posponen.

7. **Documentar el modelo.** Utilizar `templates/threat-model.md` si existe. Guardar en la documentacion del proyecto para referencia futura.

## Criterios de exito

- Todos los componentes del sistema han sido evaluados contra las 6 categorias STRIDE.
- Las amenazas estan clasificadas por probabilidad e impacto.
- Cada amenaza tiene al menos una mitigacion propuesta.
- Las mitigaciones estan priorizadas por ratio riesgo/esfuerzo.
- El modelo de amenazas esta documentado y es mantenible.
