# Software Bill of Materials (SBOM)

**Proyecto:** {{nombre_proyecto}}
**Fecha:** {{fecha}}
**Autor:** security-officer
**Formato:** CycloneDX (simplificado)

## Componente principal

- **Nombre:** {{nombre_proyecto}}
- **Versión:** {{version}}
- **Licencia:** {{licencia}}

## Dependencias directas

| Componente | Versión | Licencia | Proveedor | Hash |
|------------|---------|----------|-----------|------|
| {{dep_1}} | {{ver_1}} | {{lic_1}} | {{prov_1}} | {{hash_1}} |

## Dependencias transitivas

| Componente | Versión | Licencia | Requerido por |
|------------|---------|----------|---------------|
| {{tdep_1}} | {{tver_1}} | {{tlic_1}} | {{treq_1}} |

## Vulnerabilidades conocidas

| CVE | Componente | Severidad | Estado |
|-----|------------|-----------|--------|
| {{cve_1}} | {{comp_1}} | {{sev_1}} | {{estado_1}} |

## Licencias

| Licencia | Componentes | Compatible |
|----------|-------------|------------|
| {{lic_tipo_1}} | {{lic_count_1}} | {{lic_ok_1}} |

## Conformidad CRA

- [ ] Todos los componentes identificados
- [ ] Versiones actualizadas
- [ ] Sin vulnerabilidades críticas pendientes
- [ ] Licencias compatibles verificadas

<!-- EJEMPLO COMPLETADO ─────────────────────────────────────────────────

# Software Bill of Materials (SBOM)

**Proyecto:** alfred-dev
**Fecha:** 2026-03-10
**Autor:** security-officer
**Formato:** CycloneDX (simplificado)

## Componente principal

- **Nombre:** alfred-dev
- **Version:** 0.3.6
- **Licencia:** MIT

## Dependencias directas

| Componente | Version | Licencia | Proveedor | Hash |
|------------|---------|----------|-----------|------|
| Python stdlib (sqlite3) | 3.10+ | PSF | Python Software Foundation | N/A (stdlib) |
| Python stdlib (json) | 3.10+ | PSF | Python Software Foundation | N/A (stdlib) |
| Python stdlib (re) | 3.10+ | PSF | Python Software Foundation | N/A (stdlib) |

Nota: Alfred Dev no tiene dependencias externas. Todo el codigo usa
exclusivamente la biblioteca estandar de Python.

## Dependencias transitivas

| Componente | Version | Licencia | Requerido por |
|------------|---------|----------|---------------|
| (ninguna) | - | - | - |

## Vulnerabilidades conocidas

| CVE | Componente | Severidad | Estado |
|-----|------------|-----------|--------|
| (ninguna detectada) | - | - | - |

## Licencias

| Licencia | Componentes | Compatible |
|----------|-------------|------------|
| MIT | 1 (alfred-dev) | Si |
| PSF | stdlib | Si |

## Conformidad CRA

- [x] Todos los componentes identificados
- [x] Versiones actualizadas
- [x] Sin vulnerabilidades criticas pendientes
- [x] Licencias compatibles verificadas

──────────────────────────────────────────────── FIN DEL EJEMPLO -->
