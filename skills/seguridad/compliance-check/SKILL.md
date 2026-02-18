---
name: compliance-check
description: "Usar para verificar cumplimiento RGPD, NIS2 y CRA"
---

# Verificacion de cumplimiento normativo

## Resumen

Este skill evalua el proyecto contra tres marcos regulatorios europeos fundamentales: RGPD (proteccion de datos), NIS2 (ciberseguridad de infraestructuras) y CRA (Cyber Resilience Act, seguridad de productos con elementos digitales). El resultado es un informe de conformidad con el estado actual del proyecto frente a cada requisito y las acciones necesarias para alcanzar el cumplimiento.

No se trata de un dictamen juridico, sino de una evaluacion tecnica que identifica las lagunas y orienta las acciones de desarrollo necesarias.

## Proceso

1. **Determinar que normativas aplican.** No todos los proyectos estan sujetos a las tres:

   - **RGPD:** aplica si el software trata datos personales de personas en la UE.
   - **NIS2:** aplica si la organizacion opera en sectores criticos o es proveedor de servicios digitales.
   - **CRA:** aplica a productos con elementos digitales comercializados en la UE (incluyendo software open source con uso comercial).

2. **Checklist RGPD:**

   - [ ] Base juridica para el tratamiento de datos (consentimiento, interes legitimo, contrato, etc.).
   - [ ] Minimizacion de datos: solo se recogen los datos estrictamente necesarios.
   - [ ] Evaluacion de impacto (DPIA) para tratamientos de alto riesgo.
   - [ ] Registro de actividades de tratamiento documentado.
   - [ ] Derecho de acceso: el usuario puede consultar sus datos.
   - [ ] Derecho de rectificacion: el usuario puede corregir sus datos.
   - [ ] Derecho al olvido: el usuario puede solicitar la eliminacion de sus datos.
   - [ ] Portabilidad: el usuario puede exportar sus datos en formato estandar.
   - [ ] Notificacion de brechas en 72 horas.
   - [ ] Cifrado de datos personales en transito y en reposo.
   - [ ] Delegado de Proteccion de Datos (DPO) designado si aplica.

3. **Checklist NIS2:**

   - [ ] Gestion de riesgos de ciberseguridad documentada.
   - [ ] Politica de seguridad de la informacion aprobada por la direccion.
   - [ ] Notificacion de incidentes: alerta temprana en 24h, informe completo en 72h.
   - [ ] Seguridad de la cadena de suministro: evaluacion de proveedores.
   - [ ] Gobernanza: responsabilidades de ciberseguridad asignadas.
   - [ ] Plan de continuidad de negocio y recuperacion ante desastres.
   - [ ] Formacion en ciberseguridad para el personal.
   - [ ] Gestion de vulnerabilidades y actualizaciones.
   - [ ] Autenticacion multifactor para accesos criticos.

4. **Checklist CRA (Cyber Resilience Act):**

   - [ ] SBOM (Software Bill of Materials) generado y mantenido.
   - [ ] Actualizaciones de seguridad disponibles durante todo el ciclo de vida.
   - [ ] Diseno seguro por defecto (secure by default).
   - [ ] Documentacion tecnica del producto disponible.
   - [ ] Gestion de vulnerabilidades con proceso de reporte.
   - [ ] Notificacion de vulnerabilidades activamente explotadas en 24h a ENISA.
   - [ ] Evaluacion de conformidad (autoevaluacion o certificacion segun categoria).
   - [ ] Marcado CE para productos conformes.

5. **Generar informe de conformidad.** Para cada requisito: estado (cumple/no cumple/parcial), evidencia, acciones necesarias y prioridad.

## Criterios de exito

- Se han identificado las normativas aplicables al proyecto.
- Cada checklist se ha revisado punto por punto con estado documentado.
- Las acciones necesarias estan priorizadas por riesgo e impacto.
- El informe es accionable: un desarrollador puede tomar cada accion y ejecutarla.
