---
name: sbom-generate
description: "Usar para generar Software Bill of Materials para cumplimiento del CRA"
---

# Generar SBOM (Software Bill of Materials)

## Resumen

Este skill genera un inventario completo de todos los componentes de software incluidos en el proyecto, tanto dependencias directas como transitivas. El SBOM es un requisito del Cyber Resilience Act (CRA) europeo y una practica recomendada de seguridad de la cadena de suministro.

El SBOM permite responder rapidamente a preguntas como "usamos la version afectada por esta vulnerabilidad?" sin necesidad de investigar manualmente cada proyecto.

## Proceso

1. **Detectar el ecosistema y las fuentes de dependencias.** Identificar todos los ficheros de lock o manifiesto del proyecto:

   - Node.js: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`.
   - Python: `requirements.txt`, `Pipfile.lock`, `poetry.lock`.
   - Rust: `Cargo.lock`.
   - Go: `go.sum`.
   - Java: `pom.xml`, `build.gradle`.
   - PHP: `composer.lock`.

2. **Listar dependencias directas.** Para cada dependencia directa, registrar:

   - Nombre del paquete.
   - Version exacta instalada.
   - Licencia.
   - Proveedor o autor.
   - URL del repositorio.
   - Hash de verificacion (si esta disponible en el lock file).

3. **Listar dependencias transitivas.** Repetir el mismo proceso para todas las dependencias de las dependencias. Las transitivas suelen ser la mayoria y las mas dificiles de rastrear.

4. **Incluir componentes no gestionados por paquetes.** Algunos componentes se incluyen de forma manual:

   - Librerias copiadas directamente (vendoring).
   - Scripts de terceros incluidos via CDN.
   - Binarios precompilados.
   - Componentes del sistema operativo base (especialmente relevante en contenedores Docker).

5. **Generar en formato estandar.** Usar uno de los dos formatos aceptados por la industria:

   - **CycloneDX:** formato JSON o XML, preferido por OWASP. Mas ligero y centrado en seguridad.
   - **SPDX:** formato estandar ISO (ISO/IEC 5962:2021). Mas completo en informacion de licencias.

   Si existen herramientas automaticas para el ecosistema (como `cyclonedx-npm`, `syft`, `cdxgen`), usarlas. Si no, generar manualmente con la plantilla `templates/sbom.md`.

6. **Verificar completitud.** Cruzar el SBOM generado con el lock file para asegurar que no falta ninguna dependencia. Verificar que todas las licencias estan identificadas (ninguna como "desconocida").

7. **Firmar o versionar el SBOM.** Asociar el SBOM a una version concreta del software (tag de Git, version del paquete). El SBOM debe regenerarse con cada release.

## Criterios de exito

- El SBOM incluye todas las dependencias directas y transitivas.
- Cada componente tiene: nombre, version, licencia, proveedor y hash.
- El formato es compatible con CycloneDX o SPDX.
- No hay licencias marcadas como "desconocida" sin justificacion.
- El SBOM esta asociado a una version concreta del software.
- Se ha verificado la completitud contra el lock file del proyecto.
