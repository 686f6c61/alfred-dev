#!/usr/bin/env python3
"""
Capa de memoria persistente por proyecto para Alfred Dev.

Este modulo proporciona almacenamiento SQLite local para conservar decisiones
de diseno, eventos del flujo de trabajo y metadatos de commits entre sesiones.
La trazabilidad completa (problema -> decision -> commit -> validacion) permite
que Alfred y el Bibliotecario respondan preguntas historicas con evidencia real,
no con inferencias.

La memoria es una capa lateral opcional: si no se activa, el flujo del plugin
sigue igual que siempre. Cuando esta activa, cada proyecto tiene su propia base
de datos en ``.claude/alfred-memory.db``.

Componentes principales:
    - sanitize_content(): limpia texto de posibles secretos antes de persistir.
    - MemoryDB: clase que encapsula la conexion SQLite, el esquema y todas las
      operaciones de lectura y escritura sobre la memoria.

Seguridad:
    Todo texto que entra en la base de datos pasa por sanitize_content(), que
    aplica los mismos patrones regex de secret-guard.sh. Los secretos detectados
    se reemplazan por marcadores [REDACTED:<tipo>] para evitar fugas accidentales.
"""

import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Patrones de sanitizacion
# ---------------------------------------------------------------------------
# Compilados a partir de los mismos regex que usa hooks/secret-guard.sh.
# Cada tupla contiene (patron_compilado, etiqueta_para_el_marcador).
# El orden importa: los patrones mas especificos van primero para evitar
# que un patron generico consuma un match que deberia ser mas preciso.

_SECRET_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS_KEY"),
    (re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"), "ANTHROPIC_KEY"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "SK_KEY"),
    (
        re.compile(r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{20,})"),
        "GITHUB_TOKEN",
    ),
    (re.compile(r"xox[bpsa]-[a-zA-Z0-9\-]{10,}"), "SLACK_TOKEN"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "GOOGLE_KEY"),
    (
        re.compile(r"SG\.[a-zA-Z0-9\-_]{22,}\.[a-zA-Z0-9\-_]{22,}"),
        "SENDGRID_KEY",
    ),
    (
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        "PRIVATE_KEY",
    ),
    (
        re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
        ),
        "JWT",
    ),
    (
        re.compile(
            r"(?:mysql|postgresql|postgres|mongodb(?:\+srv)?|redis|amqp)"
            r"://[^\s\"']{10,}@"
        ),
        "CONNECTION_STRING",
    ),
    (
        re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/]+"),
        "SLACK_WEBHOOK",
    ),
    (
        re.compile(
            r"https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+"
        ),
        "DISCORD_WEBHOOK",
    ),
    # Asignaciones directas de credenciales en codigo
    (
        re.compile(
            r"(?i)(?:password|passwd|api_key|apikey|api_secret|secret_key"
            r"|auth_token|access_token|private_key)"
            r"""\s*[:=]\s*["'][^"']{8,}["']"""
        ),
        "HARDCODED_CREDENTIAL",
    ),
]

# Version actual del esquema. Se almacena en la tabla meta y se usa
# para detectar si es necesario aplicar migraciones en el futuro.
_SCHEMA_VERSION = 2

# Migraciones de esquema. Cada entrada es una lista de sentencias SQL
# que transforman la base de datos de la version N a la N+1. Se ejecutan
# secuencialmente dentro de una transaccion. Antes de aplicar cualquier
# migracion, se crea una copia de seguridad (.bak) del fichero.
_MIGRATIONS: Dict[int, List[str]] = {
    1: [
        # v1 -> v2: etiquetas y estado en decisiones, ficheros en commits,
        # tabla de relaciones entre decisiones.
        "ALTER TABLE decisions ADD COLUMN tags TEXT DEFAULT '[]'",
        "ALTER TABLE decisions ADD COLUMN status TEXT DEFAULT 'active'",
        "ALTER TABLE commits ADD COLUMN files TEXT DEFAULT '[]'",
        """CREATE TABLE IF NOT EXISTS decision_links (
            source_id   INTEGER NOT NULL REFERENCES decisions(id),
            target_id   INTEGER NOT NULL REFERENCES decisions(id),
            link_type   TEXT    NOT NULL,
            created_at  TEXT    NOT NULL,
            PRIMARY KEY (source_id, target_id)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_decision_links_target ON decision_links(target_id)",
    ],
}

# Estados validos para decisiones. Se usa en update_decision_status
# para validar la entrada antes de modificar la base de datos.
_VALID_DECISION_STATUSES = {"active", "superseded", "deprecated"}


def sanitize_content(text: Optional[str]) -> Optional[str]:
    """
    Elimina posibles secretos del texto antes de persistirlo.

    Recorre los patrones de secretos conocidos (claves API, tokens, cadenas
    de conexion, credenciales hardcodeadas) y reemplaza cada coincidencia
    por un marcador ``[REDACTED:<tipo>]``. Esto garantiza que la memoria
    del proyecto nunca almacene material sensible, incluso si un agente
    intenta registrar texto que lo contenga.

    Los patrones son identicos a los del hook secret-guard.sh para mantener
    coherencia en toda la cadena de seguridad del plugin.

    Args:
        text: texto a sanitizar. Si es None, se devuelve None sin mas.

    Returns:
        Texto limpio con los secretos reemplazados por marcadores, o None
        si la entrada era None.
    """
    if text is None:
        return None

    result = text
    for pattern, label in _SECRET_PATTERNS:
        result = pattern.sub(f"[REDACTED:{label}]", result)
    return result


# ---------------------------------------------------------------------------
# SQL de creacion del esquema
# ---------------------------------------------------------------------------
# Se usa una cadena multilinea para mayor legibilidad. Las sentencias se
# ejecutan dentro de una transaccion para garantizar atomicidad.

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS iterations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    command          TEXT    NOT NULL,
    description      TEXT,
    status           TEXT    NOT NULL DEFAULT 'active',
    started_at       TEXT    NOT NULL,
    completed_at     TEXT,
    phases_completed TEXT,
    artifacts        TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id  INTEGER REFERENCES iterations(id),
    title         TEXT    NOT NULL,
    context       TEXT,
    chosen        TEXT    NOT NULL,
    alternatives  TEXT,
    rationale     TEXT,
    impact        TEXT,
    phase         TEXT,
    tags          TEXT    DEFAULT '[]',
    status        TEXT    DEFAULT 'active',
    decided_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS commits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sha           TEXT    UNIQUE NOT NULL,
    message       TEXT,
    author        TEXT,
    files_changed INTEGER,
    insertions    INTEGER,
    deletions     INTEGER,
    files         TEXT    DEFAULT '[]',
    committed_at  TEXT    NOT NULL,
    iteration_id  INTEGER REFERENCES iterations(id)
);

CREATE TABLE IF NOT EXISTS commit_links (
    commit_id   INTEGER REFERENCES commits(id),
    decision_id INTEGER REFERENCES decisions(id),
    link_type   TEXT,
    PRIMARY KEY (commit_id, decision_id)
);

CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id  INTEGER REFERENCES iterations(id),
    event_type    TEXT    NOT NULL,
    phase         TEXT,
    payload       TEXT,
    created_at    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_iterations_status
    ON iterations(status);
CREATE INDEX IF NOT EXISTS idx_decisions_iteration
    ON decisions(iteration_id);
CREATE INDEX IF NOT EXISTS idx_commits_iteration
    ON commits(iteration_id);
CREATE INDEX IF NOT EXISTS idx_events_iteration
    ON events(iteration_id);
CREATE INDEX IF NOT EXISTS idx_events_type
    ON events(event_type);

CREATE TABLE IF NOT EXISTS decision_links (
    source_id   INTEGER NOT NULL REFERENCES decisions(id),
    target_id   INTEGER NOT NULL REFERENCES decisions(id),
    link_type   TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    PRIMARY KEY (source_id, target_id)
);
CREATE INDEX IF NOT EXISTS idx_decision_links_target ON decision_links(target_id);
"""


class MemoryDB:
    """
    Interfaz de acceso a la memoria persistente de un proyecto.

    Encapsula una conexion SQLite con WAL activado y foreign keys habilitadas.
    Gestiona el ciclo de vida del esquema (creacion, deteccion de FTS5,
    versionado) y expone metodos de escritura y lectura para iteraciones,
    decisiones, commits y eventos.

    El fichero de base de datos se crea con permisos 0600 (solo el propietario
    puede leer y escribir) para proteger la informacion almacenada.

    Args:
        db_path: ruta absoluta o relativa al fichero SQLite.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._fts_enabled = False

        # Crear el directorio padre si no existe
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

        # Activar WAL para mejor concurrencia y foreign keys para integridad
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

        self._ensure_schema()
        self._detect_fts5()

        # Permisos 0600: solo el propietario puede leer y escribir.
        # Se aplica despues de la creacion para cubrir el caso de DB nueva.
        try:
            os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            # En algunos sistemas de ficheros (ej. FAT32) chmod no funciona.
            # No es critico: se continua sin permisos restrictivos.
            pass

    # --- Gestion del esquema ------------------------------------------------

    def _ensure_schema(self) -> None:
        """
        Crea las tablas e indices si no existen.

        Si la base de datos es nueva, registra la version del esquema y la
        fecha de creacion en la tabla meta. Si ya existe, se mantiene intacta
        (las sentencias usan ``IF NOT EXISTS``).
        """
        self._conn.executescript(_SCHEMA_SQL)

        # Registrar metadatos si es la primera vez
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()

        if row is None:
            now = datetime.now(timezone.utc).isoformat()
            self._conn.executemany(
                "INSERT INTO meta (key, value) VALUES (?, ?)",
                [
                    ("schema_version", str(_SCHEMA_VERSION)),
                    ("created_at", now),
                ],
            )
            self._conn.commit()
        else:
            # DB existente: comprobar si necesita migracion
            current = int(row[0])
            if current < _SCHEMA_VERSION:
                self._run_migrations(current)

    def _run_migrations(self, current_version: int) -> None:
        """Aplica migraciones pendientes de forma secuencial.

        Crea un backup del fichero antes de la primera migracion y ejecuta
        cada paso dentro de una transaccion. Si una migracion falla, la
        transaccion se revierte y la DB queda en el ultimo estado consistente.

        Args:
            current_version: version del esquema actual en la DB.
        """
        # Solo migrar si hay versiones pendientes
        pending = [v for v in sorted(_MIGRATIONS.keys()) if v >= current_version]
        if not pending:
            return

        # Backup antes de migrar
        bak_path = self._db_path + ".bak"
        try:
            shutil.copy2(self._db_path, bak_path)
        except OSError:
            # Si no se puede hacer backup (permisos, disco lleno), continuar
            # pero no abortar la migracion.
            pass

        for version in pending:
            statements = _MIGRATIONS[version]
            try:
                for sql in statements:
                    self._conn.execute(sql)
                # Actualizar la version en meta
                new_version = version + 1
                self._conn.execute(
                    "UPDATE meta SET value = ? WHERE key = 'schema_version'",
                    (str(new_version),),
                )
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def _detect_fts5(self) -> None:
        """
        Comprueba si el entorno SQLite soporta FTS5 y crea la tabla virtual.

        Si FTS5 esta disponible, se crea la tabla ``memory_fts`` y los triggers
        que la mantienen sincronizada con ``decisions`` y ``commits``. Si no
        esta disponible, se registra el resultado para que las busquedas usen
        el fallback con LIKE.
        """
        try:
            # Intentar crear una tabla FTS5 temporal para detectar soporte
            self._conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_test "
                "USING fts5(test_col)"
            )
            self._conn.execute("DROP TABLE IF EXISTS _fts5_test")

            # FTS5 disponible: crear la tabla de busqueda real
            self._conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts "
                "USING fts5(source_type, source_id, content)"
            )

            # Triggers para mantener el indice actualizado.
            # Se usa INSERT OR REPLACE porque FTS5 no soporta UPDATE directo.
            self._conn.executescript("""
                CREATE TRIGGER IF NOT EXISTS fts_insert_decision
                AFTER INSERT ON decisions
                BEGIN
                    INSERT INTO memory_fts(source_type, source_id, content)
                    VALUES (
                        'decision',
                        CAST(NEW.id AS TEXT),
                        COALESCE(NEW.title, '') || ' ' ||
                        COALESCE(NEW.context, '') || ' ' ||
                        COALESCE(NEW.chosen, '') || ' ' ||
                        COALESCE(NEW.alternatives, '') || ' ' ||
                        COALESCE(NEW.rationale, '')
                    );
                END;

                CREATE TRIGGER IF NOT EXISTS fts_insert_commit
                AFTER INSERT ON commits
                BEGIN
                    INSERT INTO memory_fts(source_type, source_id, content)
                    VALUES (
                        'commit',
                        CAST(NEW.id AS TEXT),
                        COALESCE(NEW.message, '')
                    );
                END;
            """)

            self._fts_enabled = True
        except sqlite3.OperationalError:
            # FTS5 no disponible: se usara LIKE como fallback
            self._fts_enabled = False

        # Registrar el resultado en meta para que otros componentes lo sepan
        self._conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("fts_enabled", "1" if self._fts_enabled else "0"),
        )
        self._conn.commit()

    @property
    def fts_enabled(self) -> bool:
        """Indica si la busqueda de texto completo (FTS5) esta activa."""
        return self._fts_enabled

    # --- Escritura: iteraciones ---------------------------------------------

    def start_iteration(
        self,
        command: str,
        description: Optional[str] = None,
    ) -> int:
        """
        Inicia una nueva iteracion de trabajo.

        Cada iteracion representa un ciclo completo de un flujo (feature, fix,
        spike, etc.). Al crearla queda en estado ``active`` hasta que se complete
        o abandone.

        Args:
            command: tipo de flujo (feature, fix, spike, ship, audit).
            description: descripcion en lenguaje natural de la tarea.

        Returns:
            ID de la iteracion creada.
        """
        now = datetime.now(timezone.utc).isoformat()
        description = sanitize_content(description)
        cursor = self._conn.execute(
            "INSERT INTO iterations (command, description, status, started_at) "
            "VALUES (?, ?, 'active', ?)",
            (command, description, now),
        )
        self._conn.commit()
        return cursor.lastrowid

    def complete_iteration(
        self,
        iteration_id: int,
        status: str = "completed",
    ) -> None:
        """
        Marca una iteracion como completada o abandonada.

        Args:
            iteration_id: ID de la iteracion a cerrar.
            status: estado final (``completed`` o ``abandoned``).
        """
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE iterations SET status = ?, completed_at = ? WHERE id = ?",
            (status, now, iteration_id),
        )
        self._conn.commit()

    # --- Escritura: decisiones ----------------------------------------------

    def log_decision(
        self,
        title: str,
        chosen: str,
        context: Optional[str] = None,
        alternatives: Optional[List[str]] = None,
        rationale: Optional[str] = None,
        impact: Optional[str] = None,
        phase: Optional[str] = None,
        iteration_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Registra una decision de diseno.

        Si no se proporciona ``iteration_id``, se vincula automaticamente a la
        iteracion activa (si existe). Todos los campos de texto se sanitizan
        antes de persistir. Las etiquetas se almacenan como JSON; si no se
        proporcionan, se guarda una lista vacia.

        Args:
            title: titulo corto de la decision.
            chosen: opcion elegida.
            context: problema que se resolvia.
            alternatives: lista de opciones descartadas.
            rationale: justificacion de la eleccion.
            impact: nivel de impacto (low, medium, high, critical).
            phase: fase del flujo en la que se tomo la decision.
            iteration_id: ID de la iteracion (auto-detectado si se omite).
            tags: lista de etiquetas para clasificar la decision.

        Returns:
            ID de la decision creada.
        """
        # Auto-vincular a la iteracion activa si no se especifica
        if iteration_id is None:
            active = self.get_active_iteration()
            if active is not None:
                iteration_id = active["id"]

        now = datetime.now(timezone.utc).isoformat()

        # Sanitizar todos los campos de texto
        title = sanitize_content(title) or title
        chosen = sanitize_content(chosen) or chosen
        context = sanitize_content(context)
        rationale = sanitize_content(rationale)

        # Las alternativas se almacenan como JSON
        alt_json = None
        if alternatives is not None:
            sanitized_alts = [sanitize_content(a) or a for a in alternatives]
            alt_json = json.dumps(sanitized_alts, ensure_ascii=False)

        # Las etiquetas se almacenan como JSON; lista vacia por defecto
        tags_json = json.dumps(tags or [], ensure_ascii=False)

        cursor = self._conn.execute(
            "INSERT INTO decisions "
            "(iteration_id, title, context, chosen, alternatives, "
            " rationale, impact, phase, tags, decided_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                iteration_id, title, context, chosen, alt_json,
                rationale, impact, phase, tags_json, now,
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    # --- Escritura: estado y etiquetas de decisiones -------------------------

    def update_decision_status(self, decision_id: int, status: str) -> None:
        """
        Actualiza el estado de una decision existente.

        Los estados validos son ``active``, ``superseded`` y ``deprecated``.
        Cualquier otro valor provoca un ``ValueError`` para evitar estados
        inconsistentes en la base de datos.

        Args:
            decision_id: ID de la decision a actualizar.
            status: nuevo estado (debe estar en ``_VALID_DECISION_STATUSES``).

        Raises:
            ValueError: si el estado proporcionado no es valido.
        """
        if status not in _VALID_DECISION_STATUSES:
            raise ValueError(
                f"Estado no valido: '{status}'. "
                f"Valores permitidos: {sorted(_VALID_DECISION_STATUSES)}"
            )
        self._conn.execute(
            "UPDATE decisions SET status = ? WHERE id = ?",
            (status, decision_id),
        )
        self._conn.commit()

    def add_decision_tags(
        self, decision_id: int, tags: List[str]
    ) -> None:
        """
        Anade etiquetas a una decision sin duplicar las existentes.

        Lee las etiquetas actuales, fusiona con las nuevas conservando el
        orden de insercion y elimina duplicados. El resultado se persiste
        de vuelta en la columna ``tags`` como JSON.

        Args:
            decision_id: ID de la decision a etiquetar.
            tags: lista de etiquetas nuevas a anadir.
        """
        row = self._conn.execute(
            "SELECT tags FROM decisions WHERE id = ?",
            (decision_id,),
        ).fetchone()

        # Leer etiquetas actuales; si la decision no existe o no tiene,
        # se parte de una lista vacia
        existing: List[str] = []
        if row and row["tags"]:
            existing = json.loads(row["tags"])

        # Merge sin duplicados conservando el orden de aparicion
        merged = list(dict.fromkeys(existing + tags))
        merged_json = json.dumps(merged, ensure_ascii=False)

        self._conn.execute(
            "UPDATE decisions SET tags = ? WHERE id = ?",
            (merged_json, decision_id),
        )
        self._conn.commit()

    # --- Escritura: relaciones entre decisiones -----------------------------

    def link_decisions(
        self,
        source_id: int,
        target_id: int,
        link_type: str,
    ) -> None:
        """
        Crea una relacion dirigida entre dos decisiones.

        La relacion va de ``source_id`` a ``target_id`` con un tipo que
        describe la naturaleza del vinculo (p.ej. ``supersedes``, ``relates``,
        ``depends_on``). Si la relacion ya existe, la operacion es idempotente
        y no lanza excepcion.

        Args:
            source_id: ID de la decision origen.
            target_id: ID de la decision destino.
            link_type: tipo de relacion entre las dos decisiones.
        """
        now = datetime.now(timezone.utc).isoformat()
        try:
            self._conn.execute(
                "INSERT INTO decision_links "
                "(source_id, target_id, link_type, created_at) "
                "VALUES (?, ?, ?, ?)",
                (source_id, target_id, link_type, now),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            # La relacion ya existe: idempotencia
            pass

    def get_decision_links(
        self, decision_id: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las relaciones en las que participa una decision.

        La busqueda es bidireccional: devuelve tanto los enlaces donde la
        decision es origen como aquellos donde es destino. Esto permite
        navegar el grafo de decisiones en ambas direcciones.

        Args:
            decision_id: ID de la decision a consultar.

        Returns:
            Lista de diccionarios con los campos ``source_id``, ``target_id``,
            ``link_type`` y ``created_at`` de cada relacion encontrada.
        """
        rows = self._conn.execute(
            "SELECT * FROM decision_links "
            "WHERE source_id = ? OR target_id = ?",
            (decision_id, decision_id),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Escritura: commits -------------------------------------------------

    def log_commit(
        self,
        sha: str,
        message: Optional[str] = None,
        author: Optional[str] = None,
        files_changed: Optional[int] = None,
        insertions: Optional[int] = None,
        deletions: Optional[int] = None,
        iteration_id: Optional[int] = None,
        files: Optional[List[str]] = None,
    ) -> Optional[int]:
        """
        Registra un commit en la memoria.

        Si el SHA ya existe, se ignora silenciosamente (idempotencia). Si no se
        proporciona ``iteration_id``, se vincula a la iteracion activa. La lista
        de ficheros modificados se serializa como JSON tras sanitizar cada ruta
        para evitar fugas de informacion sensible en nombres de fichero.

        Args:
            sha: hash SHA del commit.
            message: mensaje del commit (se sanitiza).
            author: autor del commit.
            files_changed: numero de ficheros modificados.
            insertions: lineas anadidas.
            deletions: lineas eliminadas.
            iteration_id: ID de la iteracion.
            files: lista de rutas de ficheros modificados en el commit.

        Returns:
            ID del commit creado, o None si ya existia.
        """
        # Auto-vincular a la iteracion activa si no se especifica
        if iteration_id is None:
            active = self.get_active_iteration()
            if active is not None:
                iteration_id = active["id"]

        now = datetime.now(timezone.utc).isoformat()
        message = sanitize_content(message)

        # Serializar la lista de ficheros con sanitizacion preventiva.
        # Se usa el valor original como fallback si sanitize_content
        # devuelve None (caso de rutas sin secretos).
        files_json = json.dumps(
            [sanitize_content(f) or f for f in (files or [])],
            ensure_ascii=False,
        )

        try:
            cursor = self._conn.execute(
                "INSERT INTO commits "
                "(sha, message, author, files_changed, insertions, "
                " deletions, files, committed_at, iteration_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    sha, message, author, files_changed,
                    insertions, deletions, files_json, now, iteration_id,
                ),
            )
            self._conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # El SHA ya existe: idempotencia, no es un error
            return None

    def link_commit_decision(
        self,
        commit_id: int,
        decision_id: int,
        link_type: str = "implements",
    ) -> None:
        """
        Vincula un commit con una decision.

        Permite establecer la trazabilidad entre decisiones de diseno y los
        commits que las implementan, revierten o se relacionan con ellas.

        Args:
            commit_id: ID del commit.
            decision_id: ID de la decision.
            link_type: tipo de vinculo (implements, reverts, relates).
        """
        try:
            self._conn.execute(
                "INSERT INTO commit_links (commit_id, decision_id, link_type) "
                "VALUES (?, ?, ?)",
                (commit_id, decision_id, link_type),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            # El vinculo ya existe: idempotencia
            pass

    # --- Escritura: eventos -------------------------------------------------

    def log_event(
        self,
        event_type: str,
        phase: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        iteration_id: Optional[int] = None,
    ) -> int:
        """
        Registra un evento del flujo de trabajo.

        Los eventos capturan hechos mecanicos (fase completada, gate superada,
        aprobacion del usuario) que complementan las decisiones con la
        cronologia detallada del flujo.

        Args:
            event_type: tipo de evento (phase_completed, gate_passed, etc.).
            phase: fase del flujo en la que ocurrio.
            payload: datos adicionales en formato diccionario.
            iteration_id: ID de la iteracion (auto-detectado si se omite).

        Returns:
            ID del evento creado.
        """
        if iteration_id is None:
            active = self.get_active_iteration()
            if active is not None:
                iteration_id = active["id"]

        now = datetime.now(timezone.utc).isoformat()
        payload_json = None
        if payload is not None:
            # Sanitizar los valores del payload por si contienen secretos
            sanitized = {
                k: sanitize_content(str(v)) if isinstance(v, str) else v
                for k, v in payload.items()
            }
            payload_json = json.dumps(sanitized, ensure_ascii=False)

        cursor = self._conn.execute(
            "INSERT INTO events "
            "(iteration_id, event_type, phase, payload, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (iteration_id, event_type, phase, payload_json, now),
        )
        self._conn.commit()
        return cursor.lastrowid

    # --- Lectura: iteraciones -----------------------------------------------

    def get_iteration(self, iteration_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos completos de una iteracion por su ID.

        Args:
            iteration_id: ID de la iteracion a consultar.

        Returns:
            Diccionario con los datos de la iteracion, o None si no existe.
        """
        row = self._conn.execute(
            "SELECT * FROM iterations WHERE id = ?", (iteration_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_active_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene la iteracion activa mas reciente.

        Solo puede haber una iteracion activa a la vez en el modelo normal
        de uso. Si hay varias (por inconsistencia), se devuelve la mas
        reciente por ID.

        Returns:
            Diccionario con los datos de la iteracion activa, o None.
        """
        row = self._conn.execute(
            "SELECT * FROM iterations WHERE status = 'active' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def get_latest_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene la iteracion mas reciente independientemente de su estado.

        A diferencia de ``get_active_iteration``, no filtra por estado.
        Util como fallback cuando no hay iteracion activa y se necesita
        contexto de la ultima iteracion registrada.

        Returns:
            Diccionario con los datos de la iteracion mas reciente, o None.
        """
        row = self._conn.execute(
            "SELECT * FROM iterations ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    # --- Lectura: decisiones ------------------------------------------------

    def get_decisions(
        self,
        iteration_id: Optional[int] = None,
        limit: int = 50,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene decisiones con filtros opcionales por iteracion, etiquetas y estado.

        La query SQL se construye dinamicamente en funcion de los filtros
        proporcionados. El filtro de etiquetas compara contra el campo JSON
        ``tags`` usando ``LIKE`` para cada etiqueta; basta con que una
        coincida para incluir el registro (logica OR). El filtro de estado
        aplica una comparacion exacta.

        Args:
            iteration_id: si se proporciona, solo decisiones de esa iteracion.
            limit: numero maximo de resultados.
            tags: lista de etiquetas; al menos una debe coincidir con las
                del registro para que se incluya en los resultados.
            status: si se proporciona, solo decisiones con este estado.

        Returns:
            Lista de diccionarios con los datos de cada decision.
        """
        # Construccion dinamica de la query SQL
        conditions: List[str] = []
        params: List[Any] = []

        if iteration_id is not None:
            conditions.append("iteration_id = ?")
            params.append(iteration_id)

        if status is not None:
            conditions.append("status = ?")
            params.append(status)

        # Para etiquetas se usa LIKE sobre el campo JSON. Se busca la
        # presencia de al menos una etiqueta con logica OR. El patron
        # '"%tag%"' se apoya en que las etiquetas se serializan como
        # array JSON con comillas (p.ej. '["security", "api"]').
        if tags:
            tag_clauses = []
            for tag in tags:
                tag_clauses.append("tags LIKE ?")
                params.append(f'%"{tag}"%')
            conditions.append(f"({' OR '.join(tag_clauses)})")

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        sql = f"SELECT * FROM decisions {where} ORDER BY decided_at DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # --- Lectura: busqueda --------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 20,
        iteration_id: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca en decisiones y commits por texto con filtros opcionales.

        Si FTS5 esta disponible, usa MATCH para busqueda de texto completo.
        En caso contrario, usa LIKE como fallback (mas lento pero funcional).

        Los resultados se enriquecen con el tipo de fuente y los datos
        completos del registro original. Tras la busqueda inicial, se aplican
        filtros de post-procesado sobre fechas, etiquetas y estado.

        Args:
            query: termino de busqueda.
            limit: numero maximo de resultados.
            iteration_id: si se proporciona, filtra por iteracion.
            since: fecha ISO 8601 minima; excluye resultados cuyo
                ``decided_at`` o ``committed_at`` sea anterior.
            until: fecha ISO 8601 maxima; excluye resultados cuyo
                ``decided_at`` o ``committed_at`` sea posterior.
            tags: lista de etiquetas; para decisiones, al menos una debe
                coincidir con las etiquetas del registro.
            status: estado requerido; solo aplica a decisiones.

        Returns:
            Lista de diccionarios con los resultados, cada uno con la clave
            ``source_type`` ('decision' o 'commit') y los datos del registro.
        """
        results: List[Dict[str, Any]] = []

        if self._fts_enabled:
            results = self._search_fts(
                query, limit, iteration_id,
                since=since, until=until, tags=tags, status=status,
            )
        else:
            results = self._search_like(
                query, limit, iteration_id,
                since=since, until=until, tags=tags, status=status,
            )

        return results

    def _apply_post_filters(
        self,
        results: List[Dict[str, Any]],
        since: Optional[str] = None,
        until: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Aplica filtros de post-procesado sobre los resultados de busqueda.

        Este metodo centraliza la logica de filtrado que comparten tanto
        la busqueda FTS5 como el fallback LIKE. Los filtros de fecha se
        aplican a todos los tipos de resultado (decisiones y commits),
        mientras que los filtros de etiquetas y estado solo afectan a
        resultados de tipo ``decision``.

        Args:
            results: lista de resultados sin filtrar.
            since: fecha ISO minima (inclusive).
            until: fecha ISO maxima (inclusive).
            tags: etiquetas requeridas (al menos una debe coincidir).
            status: estado requerido para decisiones.

        Returns:
            Lista filtrada de resultados.
        """
        filtered: List[Dict[str, Any]] = []

        for r in results:
            source_type = r.get("source_type", "")

            # --- Filtro por fecha ---
            # Se usa decided_at para decisiones y committed_at para commits
            date_field = (
                "decided_at" if source_type == "decision" else "committed_at"
            )
            record_date = r.get(date_field, "")

            if since and record_date and record_date < since:
                continue
            if until and record_date and record_date > until:
                continue

            # --- Filtros exclusivos de decisiones ---
            if source_type == "decision":
                # Filtro por etiquetas: al menos una debe coincidir
                if tags:
                    record_tags_raw = r.get("tags", "[]")
                    try:
                        record_tags = json.loads(record_tags_raw)
                    except (json.JSONDecodeError, TypeError):
                        record_tags = []
                    if not any(t in record_tags for t in tags):
                        continue

                # Filtro por estado
                if status and r.get("status") != status:
                    continue

            # Los commits no tienen tags ni status, asi que si se
            # especifican esos filtros, los commits se excluyen
            elif source_type == "commit" and (tags or status):
                continue

            filtered.append(r)

        return filtered

    def _search_fts(
        self,
        query: str,
        limit: int,
        iteration_id: Optional[int],
        since: Optional[str] = None,
        until: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Busqueda con FTS5 MATCH y post-filtrado opcional.

        Se solicita un margen extra de resultados al indice FTS5 para
        compensar los registros que el post-filtrado pueda descartar.

        Args:
            query: termino de busqueda.
            limit: numero maximo de resultados finales.
            iteration_id: filtra por iteracion (pre-filtro).
            since: fecha ISO minima (post-filtro).
            until: fecha ISO maxima (post-filtro).
            tags: etiquetas requeridas (post-filtro, solo decisiones).
            status: estado requerido (post-filtro, solo decisiones).
        """
        results: List[Dict[str, Any]] = []

        # FTS5 requiere escapar caracteres especiales en la query.
        # Se envuelve entre comillas dobles para tratarla como frase literal.
        safe_query = '"' + query.replace('"', '""') + '"'

        # Solicitar un margen extra para compensar el post-filtrado
        fetch_limit = limit * 3 if (since or until or tags or status) else limit

        rows = self._conn.execute(
            "SELECT source_type, source_id FROM memory_fts "
            "WHERE memory_fts MATCH ? LIMIT ?",
            (safe_query, fetch_limit),
        ).fetchall()

        for row in rows:
            source_type = row["source_type"]
            source_id = int(row["source_id"])
            record = self._fetch_source_record(source_type, source_id)
            if record is None:
                continue
            # Filtrar por iteracion si se especifico
            if iteration_id is not None:
                if record.get("iteration_id") != iteration_id:
                    continue
            results.append({
                "source_type": source_type,
                **record,
            })

        # Aplicar post-filtros de fecha, etiquetas y estado
        results = self._apply_post_filters(
            results, since=since, until=until, tags=tags, status=status,
        )

        return results[:limit]

    def _search_like(
        self,
        query: str,
        limit: int,
        iteration_id: Optional[int],
        since: Optional[str] = None,
        until: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Busqueda con LIKE como fallback y post-filtrado opcional.

        Se solicita un margen extra de resultados SQL para compensar los
        registros que el post-filtrado pueda descartar.

        Args:
            query: termino de busqueda.
            limit: numero maximo de resultados finales.
            iteration_id: filtra por iteracion (pre-filtro SQL).
            since: fecha ISO minima (post-filtro).
            until: fecha ISO maxima (post-filtro).
            tags: etiquetas requeridas (post-filtro, solo decisiones).
            status: estado requerido (post-filtro, solo decisiones).
        """
        results: List[Dict[str, Any]] = []
        like_pattern = f"%{query}%"

        # Margen extra para compensar el post-filtrado
        fetch_limit = limit * 3 if (since or until or tags or status) else limit

        # Buscar en decisiones
        if iteration_id is not None:
            decision_rows = self._conn.execute(
                "SELECT * FROM decisions "
                "WHERE (title LIKE ? OR context LIKE ? OR chosen LIKE ? "
                "       OR rationale LIKE ?) "
                "  AND iteration_id = ? "
                "ORDER BY decided_at DESC LIMIT ?",
                (like_pattern, like_pattern, like_pattern, like_pattern,
                 iteration_id, fetch_limit),
            ).fetchall()
        else:
            decision_rows = self._conn.execute(
                "SELECT * FROM decisions "
                "WHERE title LIKE ? OR context LIKE ? OR chosen LIKE ? "
                "      OR rationale LIKE ? "
                "ORDER BY decided_at DESC LIMIT ?",
                (like_pattern, like_pattern, like_pattern, like_pattern,
                 fetch_limit),
            ).fetchall()

        for row in decision_rows:
            results.append({"source_type": "decision", **dict(row)})

        # Buscar en commits
        remaining = fetch_limit - len(results)
        if remaining > 0:
            if iteration_id is not None:
                commit_rows = self._conn.execute(
                    "SELECT * FROM commits "
                    "WHERE message LIKE ? AND iteration_id = ? "
                    "ORDER BY committed_at DESC LIMIT ?",
                    (like_pattern, iteration_id, remaining),
                ).fetchall()
            else:
                commit_rows = self._conn.execute(
                    "SELECT * FROM commits WHERE message LIKE ? "
                    "ORDER BY committed_at DESC LIMIT ?",
                    (like_pattern, remaining),
                ).fetchall()

            for row in commit_rows:
                results.append({"source_type": "commit", **dict(row)})

        # Aplicar post-filtros de fecha, etiquetas y estado
        results = self._apply_post_filters(
            results, since=since, until=until, tags=tags, status=status,
        )

        return results[:limit]

    def _fetch_source_record(
        self, source_type: str, source_id: int
    ) -> Optional[Dict[str, Any]]:
        """Obtiene el registro completo de una fuente (decision o commit)."""
        table = "decisions" if source_type == "decision" else "commits"
        row = self._conn.execute(
            f"SELECT * FROM {table} WHERE id = ?", (source_id,)
        ).fetchone()
        return dict(row) if row else None

    # --- Lectura: cronologia ------------------------------------------------

    def get_timeline(
        self,
        iteration_id: int,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene la cronologia de eventos de una iteracion.

        Args:
            iteration_id: ID de la iteracion.
            limit: numero maximo de eventos.

        Returns:
            Lista de diccionarios con los datos de cada evento, ordenados
            cronologicamente.
        """
        rows = self._conn.execute(
            "SELECT * FROM events WHERE iteration_id = ? "
            "ORDER BY created_at ASC LIMIT ?",
            (iteration_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Lectura: estadisticas ----------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """
        Devuelve estadisticas generales de la memoria del proyecto.

        Returns:
            Diccionario con contadores (iteraciones, decisiones, commits,
            eventos), estado de FTS5, version del esquema y fecha de creacion.
        """
        stats: Dict[str, Any] = {}

        # Contadores
        for table in ("iterations", "decisions", "commits", "events"):
            row = self._conn.execute(
                f"SELECT COUNT(*) as cnt FROM {table}"
            ).fetchone()
            stats[f"total_{table}"] = row["cnt"]

        # Metadatos
        meta_rows = self._conn.execute("SELECT key, value FROM meta").fetchall()
        for row in meta_rows:
            stats[row["key"]] = row["value"]

        return stats

    # --- Mantenimiento ------------------------------------------------------

    def check_health(self) -> Dict[str, Any]:
        """Valida la integridad de la base de datos de memoria.

        Ejecuta un conjunto de comprobaciones diagnosticas para detectar
        problemas de configuracion, sincronizacion o capacidad antes de
        que afecten al funcionamiento normal del plugin.

        Comprobaciones:
            - Version del esquema correcta.
            - FTS5 sincronizado (conteo en FTS vs tablas fuente).
            - Permisos del fichero (0600).
            - Tamano de la BD (aviso si > 50 MB).

        Returns:
            Diccionario con status (healthy, warnings, errors),
            lista de issues y metadatos de la DB.
        """
        issues: List[str] = []

        # Version del esquema
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        schema_version = row[0] if row else "unknown"
        if schema_version != str(_SCHEMA_VERSION):
            issues.append(
                f"Version del esquema desactualizada: {schema_version} "
                f"(esperada: {_SCHEMA_VERSION})"
            )

        # FTS5 sincronizado
        if self._fts_enabled:
            fts_count = self._conn.execute(
                "SELECT COUNT(*) FROM memory_fts"
            ).fetchone()[0]
            dec_count = self._conn.execute(
                "SELECT COUNT(*) FROM decisions"
            ).fetchone()[0]
            commit_count = self._conn.execute(
                "SELECT COUNT(*) FROM commits"
            ).fetchone()[0]
            expected = dec_count + commit_count
            if fts_count != expected:
                issues.append(
                    f"FTS5 desincronizado: {fts_count} entradas "
                    f"vs {expected} esperadas"
                )

        # Permisos del fichero
        permissions_ok = True
        try:
            mode = os.stat(self._db_path).st_mode
            perms = stat.S_IMODE(mode)
            if perms != 0o600:
                permissions_ok = False
                issues.append(
                    f"Permisos incorrectos: {oct(perms)} (esperado: 0600)"
                )
        except OSError:
            permissions_ok = False
            issues.append("No se pudo verificar los permisos del fichero")

        # Tamano de la BD
        size_bytes = 0
        try:
            size_bytes = os.path.getsize(self._db_path)
            if size_bytes > 50 * 1024 * 1024:  # 50 MB
                issues.append(
                    f"Base de datos grande: {size_bytes / (1024*1024):.1f} MB"
                )
        except OSError:
            pass

        # Estado global: errores criticos (esquema o FTS) vs avisos menores
        if any("desactualizada" in i or "desincronizado" in i for i in issues):
            status = "errors"
        elif issues:
            status = "warnings"
        else:
            status = "healthy"

        return {
            "status": status,
            "issues": issues,
            "schema_version": schema_version,
            "fts_enabled": self._fts_enabled,
            "permissions_ok": permissions_ok,
            "size_bytes": size_bytes,
        }

    def purge_old_events(self, retention_days: int) -> int:
        """
        Elimina eventos anteriores a la ventana de retencion.

        Solo se purgan eventos: las decisiones e iteraciones se conservan
        siempre por su alto valor para la trazabilidad.

        Args:
            retention_days: numero de dias de retencion.

        Returns:
            Numero de eventos eliminados.
        """
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=retention_days)
        ).isoformat()
        cursor = self._conn.execute(
            "DELETE FROM events WHERE created_at < ?", (cutoff,)
        )
        self._conn.commit()
        return cursor.rowcount

    # --- Export e import ----------------------------------------------------

    def export_decisions_markdown(
        self,
        path: str,
        iteration_id: Optional[int] = None,
    ) -> int:
        """Exporta las decisiones a un fichero Markdown con formato ADR-like.

        Genera un documento estructurado donde cada decision se presenta
        como un registro de arquitectura (Architecture Decision Record),
        incluyendo titulo, fecha, estado, etiquetas, contexto, decision
        elegida, alternativas descartadas y justificacion.

        Args:
            path: ruta del fichero Markdown de destino. Se crea el
                directorio padre si no existe.
            iteration_id: si se proporciona, solo exporta decisiones
                de esa iteracion.

        Returns:
            Numero de decisiones exportadas.
        """
        decisions = self.get_decisions(
            limit=1000, iteration_id=iteration_id,
        )

        lines: List[str] = []
        lines.append("# Registro de decisiones de arquitectura\n")
        lines.append("")

        for dec in decisions:
            lines.append(f"## {dec['title']}")
            lines.append("")
            lines.append(f"- **Fecha:** {dec.get('decided_at', 'N/A')}")
            lines.append(f"- **Estado:** {dec.get('status', 'active')}")

            # Etiquetas
            tags_raw = dec.get("tags", "[]")
            try:
                tags = json.loads(tags_raw) if tags_raw else []
            except (json.JSONDecodeError, TypeError):
                tags = []
            if tags:
                lines.append(f"- **Etiquetas:** {', '.join(tags)}")

            lines.append("")

            # Contexto
            if dec.get("context"):
                lines.append("### Contexto")
                lines.append("")
                lines.append(dec["context"])
                lines.append("")

            # Decision elegida
            lines.append("### Decision")
            lines.append("")
            lines.append(dec["chosen"])
            lines.append("")

            # Alternativas descartadas
            if dec.get("alternatives"):
                try:
                    alts = json.loads(dec["alternatives"])
                except (json.JSONDecodeError, TypeError):
                    alts = []
                if alts:
                    lines.append("### Alternativas descartadas")
                    lines.append("")
                    for alt in alts:
                        lines.append(f"- {alt}")
                    lines.append("")

            # Justificacion
            if dec.get("rationale"):
                lines.append("### Justificacion")
                lines.append("")
                lines.append(dec["rationale"])
                lines.append("")

            lines.append("---")
            lines.append("")

        # Crear directorio padre si no existe
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return len(decisions)

    def import_git_history(
        self,
        repo_path: str,
        limit: int = 100,
    ) -> int:
        """Importa el historial de commits de un repositorio Git.

        Ejecuta ``git log`` sobre el repositorio indicado y registra cada
        commit en la memoria. La operacion es idempotente: los commits
        cuyo SHA ya exista en la base de datos se ignoran silenciosamente.

        Args:
            repo_path: ruta al directorio raiz del repositorio Git.
            limit: numero maximo de commits a importar (por defecto 100).

        Returns:
            Numero de commits nuevos importados (excluye los que ya
            existian en la base de datos).
        """
        result = subprocess.run(
            [
                "git", "log",
                f"--max-count={limit}",
                "--format=%H|%s|%an|%aI",
                "--name-only",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        # Parsear la salida: cada commit empieza con la linea de formato
        # (contiene |), las lineas siguientes sin | son nombres de fichero,
        # y una linea vacia separa bloques.
        new_count = 0
        current_commit: Optional[Dict[str, str]] = None
        current_files: List[str] = []

        for line in result.stdout.splitlines():
            if "|" in line:
                # Si hay un commit pendiente, registrarlo
                if current_commit is not None:
                    commit_id = self.log_commit(
                        sha=current_commit["sha"],
                        message=current_commit["message"],
                        author=current_commit["author"],
                        files=current_files,
                    )
                    if commit_id is not None:
                        new_count += 1

                # Nuevo commit
                parts = line.split("|", 3)
                current_commit = {
                    "sha": parts[0],
                    "message": parts[1] if len(parts) > 1 else "",
                    "author": parts[2] if len(parts) > 2 else "",
                }
                current_files = []
            elif line.strip():
                # Nombre de fichero
                current_files.append(line.strip())
            # Linea vacia: separador entre bloques (no hace nada especial)

        # Registrar el ultimo commit pendiente
        if current_commit is not None:
            commit_id = self.log_commit(
                sha=current_commit["sha"],
                message=current_commit["message"],
                author=current_commit["author"],
                files=current_files,
            )
            if commit_id is not None:
                new_count += 1

        return new_count

    def import_adrs(self, adr_dir: str = "docs/adr") -> int:
        """Importa ficheros ADR (Architecture Decision Records) como decisiones.

        Recorre los ficheros ``*.md`` del directorio indicado y extrae
        de cada uno el titulo (primer encabezado ``#``), el contexto
        (seccion ``## Context`` o ``## Contexto``) y la decision
        (seccion ``## Decision`` o ``## Decision``). Cada fichero se
        registra como una nueva decision con la etiqueta ``imported-adr``.

        Args:
            adr_dir: ruta al directorio que contiene los ficheros ADR.
                Por defecto ``docs/adr``.

        Returns:
            Numero de decisiones importadas.
        """
        adr_path = Path(adr_dir)
        if not adr_path.is_dir():
            return 0

        count = 0
        for md_file in sorted(adr_path.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            title = self._extract_heading(content)
            context = self._extract_section(
                content, ["## Context", "## Contexto"]
            )
            chosen = self._extract_section(
                content, ["## Decision", u"## Decisi\u00f3n"]
            )

            if title and chosen:
                self.log_decision(
                    title=title,
                    chosen=chosen,
                    context=context,
                    tags=["imported-adr"],
                )
                count += 1

        return count

    @staticmethod
    def _extract_heading(content: str) -> Optional[str]:
        """Extrae el titulo del primer encabezado ``#`` del contenido Markdown.

        Args:
            content: texto Markdown completo del fichero.

        Returns:
            Texto del titulo sin el marcador ``#``, o None si no se
            encuentra ningun encabezado de nivel 1.
        """
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return None

    @staticmethod
    def _extract_section(
        content: str, headers: List[str]
    ) -> Optional[str]:
        """Extrae el cuerpo de una seccion Markdown identificada por su encabezado.

        Busca cualquiera de los encabezados proporcionados y devuelve
        el texto comprendido entre ese encabezado y el siguiente de
        igual o mayor nivel.

        Args:
            content: texto Markdown completo del fichero.
            headers: lista de encabezados a buscar (p.ej.
                ``["## Context", "## Contexto"]``).

        Returns:
            Texto de la seccion sin el encabezado, o None si no se
            encuentra ninguno de los encabezados buscados.
        """
        lines = content.splitlines()
        capture = False
        result_lines: List[str] = []

        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(h) for h in headers):
                capture = True
                continue
            if capture:
                # Parar al encontrar otro encabezado de nivel 2 o superior
                if stripped.startswith("## ") or stripped.startswith("# "):
                    break
                result_lines.append(line)

        if not result_lines:
            return None

        text = "\n".join(result_lines).strip()
        return text if text else None

    # --- Ciclo de vida ------------------------------------------------------

    def close(self) -> None:
        """Cierra la conexion con la base de datos."""
        self._conn.close()
