---
name: write-adr
description: "Usar para documentar decisiones arquitectonicas como ADR"
---

# Escribir ADR (Architecture Decision Record)

## Resumen

Este skill genera un registro de decision arquitectonica (ADR) siguiendo un formato estandarizado. Los ADR capturan no solo que se decidio, sino por que y que alternativas se descartaron. Son la memoria institucional del proyecto: cuando dentro de seis meses alguien pregunte "por que usamos X en vez de Y", el ADR tiene la respuesta.

Cada ADR es un fichero independiente, numerado secuencialmente, que se guarda en `docs/adr/`. Una vez aceptado, un ADR no se modifica; si la decision cambia, se crea uno nuevo que lo sustituye.

## Proceso

1. **Identificar la decision a documentar.** Un ADR se escribe cuando hay una decision arquitectonica significativa: eleccion de tecnologia, patron de diseno, estructura de datos, estrategia de despliegue, etc. No documentar decisiones triviales.

2. **Obtener el siguiente numero secuencial.** Listar los ADR existentes en `docs/adr/` y asignar el siguiente numero (formato `NNN`, por ejemplo `001`, `002`, `015`).

3. **Redactar el ADR con la siguiente estructura:**

   - **Titulo:** `NNN - Descripcion breve de la decision`. Ejemplo: `003 - Usar PostgreSQL como base de datos principal`.
   - **Estado:** uno de `propuesto`, `aceptado`, `sustituido por [NNN]`, `rechazado`.
   - **Fecha:** cuando se tomo la decision.
   - **Contexto:** que situacion o problema motiva esta decision. Incluir restricciones tecnicas, de negocio o de equipo que influyen.
   - **Opciones evaluadas:** minimo 3 alternativas, cada una con:
     - Descripcion breve.
     - Ventajas.
     - Desventajas.
     - Riesgos.
   - **Decision:** que opcion se elige y un parrafo explicando el razonamiento.
   - **Consecuencias:** divididas en positivas y negativas. Ser honesto con los compromisos que se asumen.

4. **Utilizar la plantilla base.** Si existe `templates/adr.md`, usarla como punto de partida para mantener consistencia entre ADRs del proyecto.

5. **Guardar el fichero.** Nombre: `docs/adr/NNN-titulo-en-kebab-case.md`. Ejemplo: `docs/adr/003-usar-postgresql.md`.

6. **Actualizar el indice si existe.** Si hay un fichero indice de ADRs (como `docs/adr/README.md` o `docs/adr/index.md`), anadir la nueva entrada.

7. **Revisar con el usuario.** El ADR es un registro de decision consensuada. No se da por final hasta que el usuario lo aprueba.

## Criterios de exito

- El ADR sigue la estructura estandar: titulo, estado, contexto, opciones, decision, consecuencias.
- Se han evaluado al menos 3 alternativas con ventajas y desventajas documentadas.
- El contexto explica el "por que" de la decision, no solo el "que".
- Las consecuencias son honestas e incluyen los compromisos asumidos.
- El fichero esta guardado en `docs/adr/` con el formato de numeracion correcto.
- El usuario ha aprobado el ADR.
