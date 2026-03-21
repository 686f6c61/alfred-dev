---
name: sonarqube
description: "Levantar SonarQube con Docker, analizar el código y proponer mejoras. También: análisis estático, deuda técnica, code smells, cobertura, calidad automatizada."
---

# Análisis de calidad con SonarQube

## Resumen

Este skill levanta una instancia de SonarQube con Docker, ejecuta un análisis del código del proyecto y traduce los resultados en propuestas de mejora accionables. SonarQube detecta bugs, vulnerabilidades, code smells y problemas de cobertura que las herramientas de linting no cubren.

No sustituye al qa-engineer ni al security-officer: complementa su trabajo con una segunda opinión automatizada basada en reglas estáticas probadas en millones de proyectos.

## Proceso

### Paso 1: preflight de Docker y permisos

Comprobar si Docker está disponible y si el daemon responde:

```bash
docker --version
docker info
```

Interpreta el resultado con estas reglas:

- **Si `docker --version` falla**: Docker no está instalado. Explica al usuario que SonarQube lo necesita y que la instalación puede requerir permisos de administrador.
- **Si `docker --version` funciona pero `docker info` falla**: Docker está instalado, pero el daemon no está disponible. Explica al usuario que hay que arrancar Docker Desktop o el servicio del sistema antes de continuar.

**No instales Docker, no abras Docker Desktop y no arranques el daemon sin aprobación explícita del usuario.** Si la orden viene desde `/alfred audit`, respeta la decisión tomada en su preflight. Si no existe una autorización previa, pídela ahora y espera respuesta.

Si el usuario autoriza la instalación, instala la última versión estable según la plataforma:

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

Si el usuario autoriza arrancar Docker cuando está instalado pero el daemon no responde, usa la estrategia mínima necesaria para la plataforma:

**macOS:**
```bash
open -a Docker
```

**Linux (systemd):**
```bash
sudo systemctl start docker
```

**Windows (PowerShell):**
```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

Después de instalar o arrancar Docker, verifica otra vez con `docker info`.

- Si `docker info` responde correctamente, continúa.
- Si el usuario rechaza la instalación o el arranque, o si el daemon sigue sin responder, **detén aquí la rama de SonarQube** y devuelve un resultado explícito: "SonarQube omitido por decisión del usuario o por falta de permisos". No intentes forzarlo por otras vías.

### Paso 2: levantar SonarQube

Antes de levantar el contenedor:

- Comprueba si ya existe `sonarqube-alfred`. Si existe de una ejecución anterior, elimínalo primero para evitar conflictos:

```bash
docker rm -f sonarqube-alfred 2>/dev/null || true
```

- Comprueba si el puerto `9000` ya está en uso. Si lo está, detén la ejecución y pregunta al usuario si quiere liberar ese puerto o continuar sin SonarQube. No mates procesos por tu cuenta.

```bash
docker run -d --name sonarqube-alfred -p 9000:9000 sonarqube:community
```

Esperar a que SonarQube esté listo (puede tardar 1-2 minutos):

Usa este bucle exacto o uno equivalente. **No uses la variable `status` en scripts de shell**: en `zsh` es de solo lectura y romperá la espera. Si necesitas guardar el estado en una variable, usa `sonar_status`.

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

Si el análisis falla a mitad del proceso, intenta igualmente la limpieza final del contenedor temporal antes de salir.

## Qué NO hacer

- No dejar SonarQube corriendo indefinidamente. Es una herramienta de análisis puntual, no un servicio permanente.
- No instalar Docker, arrancar el daemon ni abrir Docker Desktop sin permiso explícito del usuario.
- No tratar todos los hallazgos como iguales. Priorizar por impacto real, no por cantidad.
- No corregir hallazgos sin entender por qué SonarQube los marca. A veces los falsos positivos existen.
- No sustituir los code reviews humanos por SonarQube. Son complementarios.

## Referencia al stack

Consultar el stack detectado en la configuración de Alfred para seleccionar el scanner adecuado (Node.js, Python, etc.) y configurar automáticamente el fichero `sonar-project.properties` con el lenguaje y los directorios correctos.
