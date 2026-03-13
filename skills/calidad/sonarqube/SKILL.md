---
name: sonarqube
description: "Levantar SonarQube con Docker, analizar el código y proponer mejoras. También: análisis estático, deuda técnica, code smells, cobertura, calidad automatizada."
---

# Análisis de calidad con SonarQube

## Resumen

Este skill levanta una instancia de SonarQube con Docker, ejecuta un análisis del código del proyecto y traduce los resultados en propuestas de mejora accionables. SonarQube detecta bugs, vulnerabilidades, code smells y problemas de cobertura que las herramientas de linting no cubren.

No sustituye al qa-engineer ni al security-officer: complementa su trabajo con una segunda opinión automatizada basada en reglas estáticas probadas en millones de proyectos.

## Proceso

### Paso 1: verificar e instalar Docker

Comprobar que Docker está instalado y en ejecución:

```bash
docker --version
docker info
```

Si Docker no está instalado, pregunta al usuario si quiere que Alfred lo instale. Si acepta, instala la última versión estable según la plataforma:

**macOS:**
```bash
brew install --cask docker
open -a Docker
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo usermod -aG docker $USER
```

**Windows (PowerShell como administrador):**
```powershell
winget install Docker.DockerDesktop
```

Después de la instalación, verificar con `docker info` que el daemon está corriendo. Si Docker está instalado pero no arrancado, iniciarlo automáticamente.

No avanzar hasta que `docker info` responda correctamente.

### Paso 2: levantar SonarQube

```bash
docker run -d --name sonarqube-alfred -p 9000:9000 sonarqube:community
```

Esperar a que SonarQube esté listo (puede tardar 1-2 minutos):

```bash
until curl -s http://localhost:9000/api/system/status | grep -q '"status":"UP"'; do sleep 5; done
```

Credenciales por defecto: admin/admin. Cambiar la contraseña en el primer acceso.

### Paso 3: configurar el proyecto

- Crear un proyecto en SonarQube (vía API o interfaz web).
- Generar un token de autenticación para el análisis.
- Crear o verificar el fichero `sonar-project.properties` en la raíz del proyecto:

```properties
sonar.projectKey=nombre-del-proyecto
sonar.sources=src
sonar.tests=tests
sonar.language=ts
sonar.sourceEncoding=UTF-8
```

Adaptar según el stack del proyecto (lenguaje, directorios de código y tests).

### Paso 4: ejecutar el análisis

Para proyectos Node/TypeScript:

```bash
npx sonarqube-scanner
```

Para proyectos Python:

```bash
pip install pysonar-scanner && pysonar-scanner
```

Alternativa universal con Docker:

```bash
docker run --rm -v "$(pwd):/usr/src" sonarsource/sonar-scanner-cli
```

### Paso 5: interpretar resultados

Acceder a http://localhost:9000 y revisar el dashboard del proyecto. Clasificar los hallazgos por:

- **Bugs**: errores que pueden causar comportamiento incorrecto. Prioridad alta.
- **Vulnerabilidades**: problemas de seguridad detectados por reglas OWASP/CWE. Notificar al security-officer.
- **Code smells**: problemas de mantenibilidad. Priorizar los de mayor impacto.
- **Cobertura**: porcentaje de código cubierto por tests. Identificar zonas sin cobertura críticas.

### Paso 6: generar informe de mejoras

Crear un informe con:

- Resumen ejecutivo: métricas principales (bugs, vulnerabilidades, cobertura, deuda técnica).
- Top 10 hallazgos por impacto con la corrección propuesta.
- Zonas de código con mayor densidad de problemas.
- Comparación con el análisis anterior si existe.

### Paso 7: limpiar

Cuando el análisis esté completo y los resultados revisados:

```bash
docker stop sonarqube-alfred && docker rm sonarqube-alfred
```

## Qué NO hacer

- No dejar SonarQube corriendo indefinidamente. Es una herramienta de análisis puntual, no un servicio permanente.
- No tratar todos los hallazgos como iguales. Priorizar por impacto real, no por cantidad.
- No corregir hallazgos sin entender por qué SonarQube los marca. A veces los falsos positivos existen.
- No sustituir los code reviews humanos por SonarQube. Son complementarios.

## Referencia al stack

Consultar el stack detectado en la configuración de Alfred para seleccionar el scanner adecuado (Node.js, Python, etc.) y configurar automáticamente el fichero `sonar-project.properties` con el lenguaje y los directorios correctos.
