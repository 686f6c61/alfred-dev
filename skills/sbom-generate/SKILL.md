---
name: sbom-generate
description: "Usar para generar Software Bill of Materials para cumplimiento del CRA. También: Software Bill of Materials, inventario de componentes, CycloneDX, SPDX, cadena de suministro."
---

# Generar SBOM (Software Bill of Materials)

## Resumen

Este skill genera un inventario completo de todos los componentes de software incluidos en el proyecto, tanto dependencias directas como transitivas. El SBOM es un requisito del Cyber Resilience Act (CRA) europeo y una práctica recomendada de seguridad de la cadena de suministro.

El SBOM permite responder rápidamente a preguntas como "usamos la versión afectada por esta vulnerabilidad?" sin necesidad de investigar manualmente cada proyecto.

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
   - Versión exacta instalada.
   - Licencia.
   - Proveedor o autor.
   - URL del repositorio.
   - Hash de verificación (si está disponible en el lock file).

3. **Listar dependencias transitivas.** Repetir el mismo proceso para todas las dependencias de las dependencias. Las transitivas suelen ser la mayoría y las más difíciles de rastrear.

4. **Incluir componentes no gestionados por paquetes.** Algunos componentes se incluyen de forma manual:

   - Librerías copiadas directamente (vendoring).
   - Scripts de terceros incluidos vía CDN.
   - Binarios precompilados.
   - Componentes del sistema operativo base (especialmente relevante en contenedores Docker).

5. **Generar en formato estándar.** Usar uno de los dos formatos aceptados por la industria:

   - **CycloneDX:** formato JSON o XML, preferido por OWASP. Más ligero y centrado en seguridad.
   - **SPDX:** formato estándar ISO (ISO/IEC 5962:2021). Más completo en información de licencias.

   Si existen herramientas automáticas para el ecosistema (como `cyclonedx-npm`, `syft`, `cdxgen`), usarlas. Si no, generar manualmente con la plantilla `templates/sbom.md`.

6. **Verificar completitud.** Cruzar el SBOM generado con el lock file para asegurar que no falta ninguna dependencia. Verificar que todas las licencias están identificadas (ninguna como "desconocida").

7. **Firmar o versionar el SBOM.** Asociar el SBOM a una versión concreta del software (tag de Git, versión del paquete). El SBOM debe regenerarse con cada release.

## Criterios de éxito

- El SBOM incluye todas las dependencias directas y transitivas.
- Cada componente tiene: nombre, versión, licencia, proveedor y hash.
- El formato es compatible con CycloneDX o SPDX.
- No hay licencias marcadas como "desconocida" sin justificación.
- El SBOM está asociado a una versión concreta del software.
- Se ha verificado la completitud contra el lock file del proyecto.
