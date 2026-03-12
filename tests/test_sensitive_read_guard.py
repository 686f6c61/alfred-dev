#!/usr/bin/env python3
"""
Tests para hooks/sensitive-read-guard.py.

Verifica que el hook detecta correctamente ficheros sensibles (claves
privadas, variables de entorno, credenciales de servicios, directorios
SSH/GPG) y que permite sin aviso ficheros normales.

El hook es informativo (exit 0 siempre), asi que los tests verifican la
salida por stderr para comprobar si se emitio aviso o no.
"""

import importlib.util
import io
import json
import os
import sys
import unittest


def _load_module():
    """Carga el modulo sensitive-read-guard.py por ruta (tiene guion)."""
    module_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "hooks",
        "sensitive-read-guard.py",
    )
    spec = importlib.util.spec_from_file_location("sensitive_read_guard", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_guard = _load_module()


class TestSensitivePatterns(unittest.TestCase):
    """Verifica que _SENSITIVE_PATTERNS detecta los ficheros esperados."""

    def _check(self, base_name: str, expected_match: bool):
        """Comprueba si un nombre de fichero coincide con algun patron."""
        _, ext = os.path.splitext(base_name)
        matched = False
        for check_fn, _desc in _guard._SENSITIVE_PATTERNS:
            try:
                if check_fn(base_name, ext):
                    matched = True
                    break
            except Exception:
                continue
        self.assertEqual(
            matched,
            expected_match,
            f"{base_name}: esperado {'match' if expected_match else 'no match'}",
        )

    # --- Ficheros .env ---
    def test_dotenv_base(self):
        self._check(".env", True)

    def test_dotenv_local(self):
        self._check(".env.local", True)

    def test_dotenv_production(self):
        self._check(".env.production", True)

    def test_env_without_dot(self):
        """Un fichero llamado 'env' sin punto no es sensible."""
        self._check("env", False)

    # --- Claves privadas ---
    def test_pem_file(self):
        self._check("server.pem", True)

    def test_key_file(self):
        self._check("private.key", True)

    def test_p12_file(self):
        self._check("cert.p12", True)

    def test_pfx_file(self):
        self._check("cert.pfx", True)

    # --- SSH keys ---
    def test_id_rsa(self):
        self._check("id_rsa", True)

    def test_id_ed25519(self):
        self._check("id_ed25519", True)

    def test_id_ecdsa(self):
        self._check("id_ecdsa", True)

    def test_id_dsa(self):
        self._check("id_dsa", True)

    def test_id_rsa_pub_not_sensitive(self):
        """Las claves publicas no son sensibles."""
        self._check("id_rsa.pub", False)

    # --- Credenciales de servicios ---
    def test_credentials_json(self):
        self._check("credentials.json", True)

    def test_service_account_json(self):
        self._check("service-account.json", True)

    def test_npmrc(self):
        self._check(".npmrc", True)

    def test_pypirc(self):
        self._check(".pypirc", True)

    def test_htpasswd(self):
        self._check(".htpasswd", True)

    # --- Keystore Java ---
    def test_jks(self):
        self._check("keystore.jks", True)

    def test_keystore(self):
        self._check("app.keystore", True)

    # --- Ficheros normales (no sensibles) ---
    def test_readme(self):
        self._check("README.md", False)

    def test_python_file(self):
        self._check("main.py", False)

    def test_json_config(self):
        self._check("config.json", False)

    def test_package_json(self):
        self._check("package.json", False)

    def test_txt_file(self):
        self._check("notes.txt", False)


class TestPathPatterns(unittest.TestCase):
    """Verifica que _PATH_PATTERNS detecta rutas sensibles."""

    def _check_path(self, file_path: str, expected_match: bool):
        """Comprueba si una ruta completa coincide con algun patron."""
        matched = False
        for pattern, _desc in _guard._PATH_PATTERNS:
            if pattern in file_path:
                matched = True
                break
        self.assertEqual(
            matched,
            expected_match,
            f"{file_path}: esperado {'match' if expected_match else 'no match'}",
        )

    def test_aws_credentials(self):
        self._check_path("/home/user/.aws/credentials", True)

    def test_aws_config(self):
        self._check_path("/home/user/.aws/config", True)

    def test_ssh_dir(self):
        self._check_path("/home/user/.ssh/id_rsa", True)

    def test_gnupg_dir(self):
        self._check_path("/home/user/.gnupg/private-keys-v1.d/key.key", True)

    def test_normal_path(self):
        self._check_path("/home/user/projects/app/main.py", False)

    def test_aws_not_in_path(self):
        self._check_path("/home/user/projects/aws-sdk/index.js", False)


class TestMainFunction(unittest.TestCase):
    """Verifica el flujo completo del hook main()."""

    def _run_hook(self, hook_input: dict) -> str:
        """Ejecuta main() con el input dado y captura stderr."""
        old_stdin = sys.stdin
        old_stderr = sys.stderr
        captured_stderr = io.StringIO()

        try:
            sys.stdin = io.StringIO(json.dumps(hook_input))
            sys.stderr = captured_stderr
            _guard.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = old_stdin
            sys.stderr = old_stderr

        return captured_stderr.getvalue()

    def test_sensitive_file_emits_warning(self):
        """Leer un .env debe generar aviso en stderr."""
        output = self._run_hook({
            "tool_input": {"file_path": "/project/.env"}
        })
        self.assertIn("AVISO", output)
        self.assertIn("variables de entorno", output.lower())

    def test_normal_file_no_warning(self):
        """Leer un fichero normal no debe generar aviso."""
        output = self._run_hook({
            "tool_input": {"file_path": "/project/src/main.py"}
        })
        self.assertEqual(output, "")

    def test_ssh_key_emits_warning(self):
        """Leer una clave SSH debe generar aviso."""
        output = self._run_hook({
            "tool_input": {"file_path": "/home/user/.ssh/id_rsa"}
        })
        self.assertIn("AVISO", output)

    def test_empty_path_no_warning(self):
        """Ruta vacia no debe generar aviso."""
        output = self._run_hook({
            "tool_input": {"file_path": ""}
        })
        self.assertEqual(output, "")

    def test_invalid_json_no_crash(self):
        """JSON invalido no debe hacer crash."""
        old_stdin = sys.stdin
        try:
            sys.stdin = io.StringIO("esto no es json")
            _guard.main()
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        finally:
            sys.stdin = old_stdin

    def test_path_key_fallback(self):
        """El hook debe probar tanto file_path como path."""
        output = self._run_hook({
            "tool_input": {"path": "/project/.env.local"}
        })
        self.assertIn("AVISO", output)

    def test_pem_file_warning(self):
        """Leer un fichero .pem debe generar aviso."""
        output = self._run_hook({
            "tool_input": {"file_path": "/certs/server.pem"}
        })
        self.assertIn("AVISO", output)
        self.assertIn("Clave privada", output)


if __name__ == "__main__":
    unittest.main()
