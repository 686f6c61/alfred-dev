---
name: architecture-docs
description: "Usar para documentar la arquitectura del sistema"
---

# Documentar arquitectura del sistema

## Resumen

Este skill genera documentacion arquitectonica que permite a cualquier desarrollador nuevo entender como funciona el sistema sin necesidad de leer todo el codigo. Cubre la vision general, los componentes principales, los flujos de datos, las dependencias externas y los enlaces a las decisiones arquitectonicas (ADRs) que explican el por que de cada eleccion.

La documentacion arquitectonica es un mapa del sistema: no necesita cubrir cada detalle, pero debe permitir orientarse y saber donde buscar.

## Proceso

1. **Redactar la vision general.** En 2-3 parrafos, explicar:

   - Que es el sistema y que problema resuelve.
   - A quien va dirigido (usuarios, otros servicios, el equipo interno).
   - Que principios de diseno guian la arquitectura.

2. **Documentar los componentes principales.** Para cada componente significativo:

   - Nombre y proposito.
   - Responsabilidades (que hace y que no hace).
   - Tecnologias que usa.
   - Interfaces publicas (como se comunica con otros componentes).
   - Ubicacion en el codigo (directorio o modulo).

3. **Generar diagrama de componentes con Mermaid.** Un diagrama vale mas que mil palabras, pero solo si es claro:

   ```mermaid
   graph TD
     subgraph Frontend
       A[SPA React]
     end
     subgraph Backend
       B[API REST]
       C[Worker Jobs]
     end
     subgraph Datos
       D[(PostgreSQL)]
       E[(Redis Cache)]
     end
     A -->|HTTP/JSON| B
     B --> D
     B --> E
     B -->|Encola| C
     C --> D
   ```

   Mantener el diagrama simple. Si es demasiado complejo, dividir en multiples diagramas por dominio.

4. **Documentar los flujos de datos principales.** Para los 2-3 flujos mas importantes del sistema, generar diagramas de secuencia que muestren como se mueven los datos entre componentes:

   ```mermaid
   sequenceDiagram
     participant U as Usuario
     participant F as Frontend
     participant A as API
     participant D as DB
     U->>F: Accion del usuario
     F->>A: Request HTTP
     A->>D: Query
     D-->>A: Resultado
     A-->>F: Response JSON
     F-->>U: Actualiza interfaz
   ```

5. **Listar dependencias externas.** Servicios de terceros de los que depende el sistema:

   - Nombre del servicio.
   - Para que se usa.
   - Que pasa si no esta disponible (fallback, degradacion, fallo total).
   - Enlace a su documentacion.

6. **Enlazar decisiones arquitectonicas.** Referenciar los ADRs relevantes que explican por que se tomaron las decisiones de diseno. Si no hay ADRs, considerar crearlos con el skill `write-adr`.

7. **Incluir instrucciones de desarrollo.** Como levantar el entorno de desarrollo:

   - Requisitos previos (versiones de lenguaje, herramientas).
   - Pasos para arrancar el proyecto desde cero.
   - Como ejecutar tests.
   - Variables de entorno necesarias.

## Criterios de exito

- La vision general explica que es el sistema y para que sirve en 2-3 parrafos.
- Cada componente principal esta documentado con proposito, responsabilidades e interfaces.
- Hay al menos un diagrama de componentes y un diagrama de secuencia en Mermaid.
- Las dependencias externas estan listadas con su impacto en caso de fallo.
- Las decisiones arquitectonicas estan referenciadas o documentadas.
- Las instrucciones de desarrollo permiten a un nuevo miembro del equipo arrancar el proyecto.
