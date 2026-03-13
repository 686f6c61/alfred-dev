---
name: readme-review
description: "Auditar y mejorar el README del proyecto: estructura, completitud y claridad. Activar ante: mejorar README, auditar README, primera impresion del proyecto, readme incompleto"
---

# Revisión del README

## Resumen

Este skill audita el README del proyecto de forma sistemática. El README es la primera impresión del proyecto: si está vacío, desactualizado o confuso, el visitante se va. Un buen README responde en menos de 30 segundos a las preguntas: qué es esto, para qué sirve y cómo lo uso.

## Proceso

### Paso 1: leer el README actual

- Si no existe, crearlo desde cero con la estructura base.
- Si existe, leerlo completo y evaluar cada sección.

### Paso 2: verificar secciones obligatorias

Comprobar que el README tiene, como mínimo:

1. **Título y descripción**: qué es el proyecto, en una frase.
2. **Instalación**: cómo instalarlo paso a paso. Probarlo desde cero.
3. **Uso rápido**: ejemplo mínimo de cómo usarlo (código o comando).
4. **Requisitos**: dependencias, versiones mínimas, sistema operativo.
5. **Licencia**: qué licencia tiene y dónde leerla.

### Paso 3: verificar secciones recomendadas

Evaluar si faltan y si serían útiles:

- **Contribución**: cómo contribuir al proyecto.
- **Configuración**: variables de entorno, ficheros de configuración.
- **Tests**: cómo ejecutar los tests.
- **Arquitectura**: enlace a documentación detallada si existe.
- **Changelog**: enlace al changelog o sección con cambios recientes.

### Paso 4: revisar calidad del contenido

- **Actualizado**: la información refleja el estado actual del código?
- **Completo**: un desarrollador nuevo puede arrancar solo con el README?
- **Claro**: se entiende sin conocimiento previo del proyecto?
- **Ortografía**: tildes, concordancia, sin erratas.
- **Formateo**: markdown correcto, bloques de código con lenguaje, enlaces que funcionen.

### Paso 5: entregar informe y correcciones

- Lista de hallazgos con severidad (falta sección crítica, texto desactualizado, error menor).
- Correcciones directas para los problemas encontrados.
- Sugerencias de mejora para las secciones que existen pero podrían ser mejores.

## Qué NO hacer

- No añadir badges innecesarios solo por estética.
- No escribir párrafos largos en el README. Preferir listas y ejemplos de código.
- No duplicar documentación extensa: el README enlaza a docs/, no lo reemplaza.
