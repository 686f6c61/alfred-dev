---
name: security-review
description: "Usar para revisar código contra OWASP Top 10. También: buscar vulnerabilidades, OWASP, inyección SQL, XSS, CSRF, revisión de seguridad del código."
---

# Revisión de seguridad OWASP Top 10

## Resumen

Este skill revisa el código del proyecto contra las 10 categorías de vulnerabilidades más críticas según OWASP (Open Web Application Security Project). No sustituye un pentest profesional, pero detecta los problemas más comunes que se cuelan en el desarrollo diario.

Cada categoría se revisa de forma sistemática, buscando patrones de código vulnerables y verificando que las protecciones adecuadas están implementadas.

## Proceso

1. **A01: Broken Access Control (control de acceso roto).** Verificar:

   - Todos los endpoints protegidos requieren autenticación.
   - Las autorizaciones se verifican en el servidor, no solo en el cliente.
   - No hay acceso directo a objetos sin verificación de propiedad (IDOR).
   - Los roles y permisos se aplican de forma consistente.
   - CORS está configurado correctamente, no con `*` en producción.

2. **A02: Cryptographic Failures (fallos criptográficos).** Verificar:

   - Datos sensibles cifrados en tránsito (TLS) y en reposo.
   - No se usan algoritmos obsoletos (MD5, SHA1 para hashing de contraseñas, DES).
   - Las contraseñas se almacenan con hash + salt (bcrypt, argon2, scrypt).
   - Las claves y secretos no están hardcodeados en el código ni en el repositorio.
   - Los certificados se validan correctamente.

3. **A03: Injection (inyección).** Verificar:

   - Consultas SQL parametrizadas o uso de ORM.
   - Sanitización de entrada en comandos del sistema operativo.
   - Escapado correcto en consultas NoSQL, LDAP, XPath.
   - No se construyen queries concatenando strings con entrada del usuario.

4. **A04: Insecure Design (diseño inseguro).** Verificar:

   - Rate limiting en endpoints sensibles (login, registro, password reset).
   - Validación de entrada en el servidor, no solo en el cliente.
   - Principio de menor privilegio aplicado.
   - Separación de entornos (desarrollo, staging, producción).

5. **A05: Security Misconfiguration (configuración insegura).** Verificar:

   - Cabeceras de seguridad HTTP configuradas (CSP, X-Frame-Options, HSTS).
   - Mensajes de error que no revelan información interna del sistema.
   - Features por defecto desactivadas si no se usan (directorios de listado, consola de depuración).
   - Permisos de ficheros y directorios correctos.

6. **A06: Vulnerable and Outdated Components.** Delegar en el skill `dependency-audit` para un análisis completo.

7. **A07: Identification and Authentication Failures.** Verificar:

   - Política de contraseñas adecuada (longitud mínima, complejidad).
   - Protección contra fuerza bruta (lockout, CAPTCHA, rate limiting).
   - Tokens de sesión seguros (HttpOnly, Secure, SameSite).
   - Cierre de sesión funcional que invalida el token en el servidor.

8. **A08: Software and Data Integrity Failures.** Verificar:

   - Dependencias descargadas con verificación de integridad (checksums, lock files).
   - Pipeline de CI/CD protegido contra manipulación.
   - Deserialización segura de datos no confiables.

9. **A09: Security Logging and Monitoring Failures.** Verificar:

   - Eventos de seguridad registrados (logins, fallos de autenticación, accesos denegados).
   - Los logs no contienen datos sensibles (contraseñas, tokens, datos personales).
   - Alertas configuradas para patrones sospechosos.

10. **A10: Server-Side Request Forgery (SSRF).** Verificar:

    - URLs proporcionadas por el usuario se validan contra una lista blanca.
    - No se permiten requests a redes internas desde entrada del usuario.
    - Las respuestas de requests a URLs externas se sanitizan antes de devolverlas.

## Criterios de éxito

- Se han revisado las 10 categorías de OWASP contra el código del proyecto.
- Los hallazgos están clasificados por severidad (crítica, alta, media, baja).
- Cada hallazgo incluye la ubicación en el código, el riesgo y la remediación sugerida.
- No quedan vulnerabilidades críticas o altas sin plan de acción.

## Nota de versión

Basado en OWASP Top 10 (edición 2021). Verificar si existe una edición más reciente antes de ejecutar la revisión, ya que las categorías y su priorización pueden haber cambiado.

## Qué NO hacer

- No tratar esta revisión como un pentest completo. Es una evaluación de código estática basada en patrones conocidos; un atacante real usará técnicas que van más allá de OWASP Top 10.
- No limitarse a buscar patrones sin entender el contexto. Una función de evaluación dinámica en un script de build no es lo mismo que una con entrada del usuario.
- No ignorar las categorías que "no aplican" sin verificarlo. A menudo se descarta SSRF o inyección asumiendo que "aquí no pasa", cuando sí hay superficie de ataque.
- No reportar hallazgos sin propuesta de remediación concreta. Un informe de problemas sin soluciones no es accionable.
