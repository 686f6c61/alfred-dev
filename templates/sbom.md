# Software Bill of Materials (SBOM)

**Proyecto:** {{nombre_proyecto}}
**Fecha:** {{fecha}}
**Autor:** security-officer
**Formato:** CycloneDX (simplificado)

## Componente principal

- **Nombre:** {{nombre_proyecto}}
- **Version:** {{version}}
- **Licencia:** {{licencia}}

## Dependencias directas

| Componente | Version | Licencia | Proveedor | Hash |
|------------|---------|----------|-----------|------|
| {{dep_1}} | {{ver_1}} | {{lic_1}} | {{prov_1}} | {{hash_1}} |

## Dependencias transitivas

| Componente | Version | Licencia | Requerido por |
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
- [ ] Sin vulnerabilidades criticas pendientes
- [ ] Licencias compatibles verificadas
