---
name: security-review
description: "Usar para revisar codigo contra OWASP Top 10"
---

# Revision de seguridad OWASP Top 10

## Resumen

Este skill revisa el codigo del proyecto contra las 10 categorias de vulnerabilidades mas criticas segun OWASP (Open Web Application Security Project). No sustituye un pentest profesional, pero detecta los problemas mas comunes que se cuelan en el desarrollo diario.

Cada categoria se revisa de forma sistematica, buscando patrones de codigo vulnerables y verificando que las protecciones adecuadas estan implementadas.

## Proceso

1. **A01: Broken Access Control (control de acceso roto).** Verificar:

   - Todos los endpoints protegidos requieren autenticacion.
   - Las autorizaciones se verifican en el servidor, no solo en el cliente.
   - No hay acceso directo a objetos sin verificacion de propiedad (IDOR).
   - Los roles y permisos se aplican de forma consistente.
   - CORS esta configurado correctamente, no con `*` en produccion.

2. **A02: Cryptographic Failures (fallos criptograficos).** Verificar:

   - Datos sensibles cifrados en transito (TLS) y en reposo.
   - No se usan algoritmos obsoletos (MD5, SHA1 para hashing de contrasenas, DES).
   - Las contrasenas se almacenan con hash + salt (bcrypt, argon2, scrypt).
   - Las claves y secretos no estan hardcodeados en el codigo ni en el repositorio.
   - Los certificados se validan correctamente.

3. **A03: Injection (inyeccion).** Verificar:

   - Consultas SQL parametrizadas o uso de ORM.
   - Sanitizacion de entrada en comandos del sistema operativo.
   - Escapado correcto en consultas NoSQL, LDAP, XPath.
   - No se construyen queries concatenando strings con entrada del usuario.

4. **A04: Insecure Design (diseno inseguro).** Verificar:

   - Rate limiting en endpoints sensibles (login, registro, password reset).
   - Validacion de entrada en el servidor, no solo en el cliente.
   - Principio de menor privilegio aplicado.
   - Separacion de entornos (desarrollo, staging, produccion).

5. **A05: Security Misconfiguration (configuracion insegura).** Verificar:

   - Cabeceras de seguridad HTTP configuradas (CSP, X-Frame-Options, HSTS).
   - Mensajes de error que no revelan informacion interna del sistema.
   - Features por defecto desactivadas si no se usan (directorios de listado, consola de depuracion).
   - Permisos de ficheros y directorios correctos.

6. **A06: Vulnerable and Outdated Components.** Delegar en el skill `dependency-audit` para un analisis completo.

7. **A07: Identification and Authentication Failures.** Verificar:

   - Politica de contrasenas adecuada (longitud minima, complejidad).
   - Proteccion contra fuerza bruta (lockout, CAPTCHA, rate limiting).
   - Tokens de sesion seguros (HttpOnly, Secure, SameSite).
   - Cierre de sesion funcional que invalida el token en el servidor.

8. **A08: Software and Data Integrity Failures.** Verificar:

   - Dependencias descargadas con verificacion de integridad (checksums, lock files).
   - Pipeline de CI/CD protegido contra manipulacion.
   - Deserializacion segura de datos no confiables.

9. **A09: Security Logging and Monitoring Failures.** Verificar:

   - Eventos de seguridad registrados (logins, fallos de autenticacion, accesos denegados).
   - Los logs no contienen datos sensibles (contrasenas, tokens, datos personales).
   - Alertas configuradas para patrones sospechosos.

10. **A10: Server-Side Request Forgery (SSRF).** Verificar:

    - URLs proporcionadas por el usuario se validan contra una lista blanca.
    - No se permiten requests a redes internas desde entrada del usuario.
    - Las respuestas de requests a URLs externas se sanitizan antes de devolverlas.

## Criterios de exito

- Se han revisado las 10 categorias de OWASP contra el codigo del proyecto.
- Los hallazgos estan clasificados por severidad (critica, alta, media, baja).
- Cada hallazgo incluye la ubicacion en el codigo, el riesgo y la remediacion sugerida.
- No quedan vulnerabilidades criticas o altas sin plan de accion.
