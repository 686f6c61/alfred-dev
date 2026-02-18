---
name: dockerize
description: "Usar para generar Dockerfile optimizado"
---

# Generar Dockerfile optimizado

## Resumen

Este skill genera un Dockerfile siguiendo las mejores practicas de la industria: multi-stage builds para reducir el tamano de la imagen final, ejecucion con usuario no-root para seguridad, capas optimizadas para aprovechar la cache y health checks para la orquestacion.

Un buen Dockerfile no es solo "que funcione", sino que sea seguro, rapido de construir, pequeno y mantenible.

## Proceso

1. **Detectar el stack del proyecto.** Identificar el lenguaje, framework y runtime necesarios para determinar la imagen base adecuada:

   - Node.js: `node:XX-alpine` o `node:XX-slim`.
   - Python: `python:XX-slim` o `python:XX-alpine`.
   - Rust: multi-stage con `rust:XX` para build y `debian:XX-slim` o `gcr.io/distroless` para runtime.
   - Go: multi-stage con `golang:XX` para build y `scratch` o `gcr.io/distroless` para runtime.

2. **Disenar multi-stage build.** Separar la fase de construccion de la de ejecucion:

   ```dockerfile
   # Fase de build: incluye herramientas de compilacion
   FROM node:20-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   RUN npm run build

   # Fase de runtime: solo lo necesario para ejecutar
   FROM node:20-alpine AS runtime
   WORKDIR /app
   COPY --from=builder /app/dist ./dist
   COPY --from=builder /app/node_modules ./node_modules
   ```

3. **Optimizar el orden de capas para cache.** Las capas que cambian menos van primero:

   - Primero: ficheros de dependencias (package.json, requirements.txt, Cargo.toml).
   - Segundo: instalacion de dependencias.
   - Tercero: copia del codigo fuente.
   - Cuarto: build.

   Esto asegura que un cambio en el codigo no invalida la cache de dependencias.

4. **Configurar usuario no-root.** Nunca ejecutar la aplicacion como root dentro del contenedor:

   ```dockerfile
   RUN addgroup --system app && adduser --system --ingroup app app
   USER app
   ```

5. **Anadir health check.** Permitir al orquestador (Docker Compose, Kubernetes) verificar que la aplicacion esta sana:

   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:3000/health || exit 1
   ```

6. **Generar .dockerignore.** Excluir todo lo que no es necesario en la imagen:

   ```
   node_modules
   .git
   .env
   *.md
   tests/
   .github/
   ```

7. **Configurar variables de entorno.** Usar `ENV` para valores por defecto y documentar que variables se deben pasar en runtime con `ARG` o `-e`.

8. **Verificar la imagen resultante.** Comprobar el tamano final, que no incluye herramientas de build innecesarias y que arranca correctamente.

## Criterios de exito

- El Dockerfile usa multi-stage build.
- La imagen base es minima (alpine, slim o distroless).
- La aplicacion se ejecuta con usuario no-root.
- Las capas estan ordenadas para maximizar el uso de cache.
- Hay un health check configurado.
- Existe un .dockerignore que excluye ficheros innecesarios.
- La imagen final no incluye herramientas de build, tests ni codigo fuente innecesario.
