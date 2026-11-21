import os
import json
import sqlite3

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # carpeta del proyecto
DB_PATH = os.path.join(RAIZ, "datos", "parley.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                user_id INTEGER PRIMARY KEY,
                perfil TEXT DEFAULT 'adulto',
                consentimiento INTEGER DEFAULT 0,
                frase_objetivo TEXT DEFAULT NULL,
                fonemas_objetivo TEXT DEFAULT NULL,
                errores_frecuentes TEXT DEFAULT ''
            )
        """)
        # Nivel por usuario y por idioma. ultimo_cambio_id = último intento que se usó para cambiarlo.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progreso (
                user_id INTEGER,
                idioma TEXT,
                nivel TEXT DEFAULT 'A1',
                ubicado INTEGER DEFAULT 0,
                ultimo_cambio_id INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, idioma)
            )
        """)
        # Cada frase corregida o ejercicio de pronunciación es un intento.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS intentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                idioma TEXT,
                tipo TEXT,                       -- 'frase', 'ejercicio' o 'pronunciacion'
                correcto INTEGER,
                errores_importantes INTEGER DEFAULT 0,
                errores_leves INTEGER DEFAULT 0,
                tipos_error TEXT DEFAULT '',     -- p. ej. 'gramática,ortografía'
                nivel_frase TEXT DEFAULT NULL,   -- nivel MCER que muestra la frase
                puntaje REAL DEFAULT NULL,       -- solo pronunciación (0 a 10)
                fecha TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_intentos ON intentos (user_id, idioma, tipo, id)")
        # Columnas agregadas después (las bases de datos creadas antes no las tienen).
        columnas = [c[1] for c in conn.execute("PRAGMA table_info(usuarios)")]
        if "ejercicio_texto" not in columnas:   # etapa 4: JSON del ejercicio de texto activo
            conn.execute("ALTER TABLE usuarios ADD COLUMN ejercicio_texto TEXT DEFAULT NULL")
        if "idioma" not in columnas:            # etapa 5: idioma que practica (botón "Cambiar idioma")
            conn.execute("ALTER TABLE usuarios ADD COLUMN idioma TEXT DEFAULT 'inglés'")
        # Las versiones anteriores creaban la fila apenas alguien escribía, aunque no hubiera aceptado
        # el aviso de privacidad. Esas filas sin consentimiento se borran (no tienen datos útiles).
        conn.execute("DELETE FROM usuarios WHERE consentimiento = 0")
        # Etapa 7: nivel más alto alcanzado (la mascota del modo niños nunca se encoge).
        columnas = [c[1] for c in conn.execute("PRAGMA table_info(progreso)")]
        if "nivel_max" not in columnas:
            conn.execute("ALTER TABLE progreso ADD COLUMN nivel_max TEXT DEFAULT 'A1'")
            conn.execute("UPDATE progreso SET nivel_max = nivel")


USUARIO_NUEVO = {
    "perfil": "adulto",
    "consentimiento": 0,
    "frase_objetivo": None,
    "fonemas_objetivo": None,
    "errores_frecuentes": "",
    "ejercicio_texto": None,
    "idioma": "inglés",
}


def obtener_usuario(user_id: int) -> dict:
    """Datos del usuario. Si no existe devuelve los valores por defecto SIN guardarlo: así no queda
    ningún registro de quien todavía no aceptó el aviso de privacidad (Ley 1581)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM usuarios WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {"user_id": user_id, **USUARIO_NUEVO}


def _asegurar_usuario(conn, user_id: int):
    """Crea la fila del usuario si no existe. Solo la usan las funciones que guardan datos, y el bot
    solo llega a ellas después del consentimiento."""
    conn.execute("INSERT OR IGNORE INTO usuarios (user_id) VALUES (?)", (user_id,))


def guardar_perfil(user_id: int, perfil: str):
    """Se llama al elegir el perfil en /start, que es cuando el usuario acepta el aviso de privacidad."""
    with sqlite3.connect(DB_PATH) as conn:
        _asegurar_usuario(conn, user_id)
        conn.execute(
            "UPDATE usuarios SET perfil = ?, consentimiento = 1 WHERE user_id = ?",
            (perfil, user_id)
        )


def guardar_idioma(user_id: int, idioma: str):
    with sqlite3.connect(DB_PATH) as conn:
        _asegurar_usuario(conn, user_id)
        conn.execute("UPDATE usuarios SET idioma = ? WHERE user_id = ?", (idioma, user_id))


def guardar_ejercicio(user_id: int, frase: str | None, fonemas: str | None):
    """Ejercicio de pronunciación activo. Solo hay un ejercicio activo a la vez: borra el de texto."""
    with sqlite3.connect(DB_PATH) as conn:
        _asegurar_usuario(conn, user_id)
        conn.execute(
            "UPDATE usuarios SET frase_objetivo = ?, fonemas_objetivo = ?, ejercicio_texto = NULL WHERE user_id = ?",
            (frase, fonemas, user_id)
        )


def guardar_ejercicio_texto(user_id: int, ejercicio: dict | None):
    """Ejercicio de texto activo (completar o traducir). Borra el de pronunciación."""
    valor = json.dumps(ejercicio, ensure_ascii=False) if ejercicio else None
    with sqlite3.connect(DB_PATH) as conn:
        _asegurar_usuario(conn, user_id)
        conn.execute(
            "UPDATE usuarios SET ejercicio_texto = ?, frase_objetivo = NULL, fonemas_objetivo = NULL WHERE user_id = ?",
            (valor, user_id)
        )


def obtener_ejercicio_texto(user_id: int) -> dict | None:
    valor = obtener_usuario(user_id).get("ejercicio_texto")
    return json.loads(valor) if valor else None


def registrar_error(user_id: int, nuevo_error: str):
    u = obtener_usuario(user_id)
    historial = [e for e in u["errores_frecuentes"].split(" | ") if e]
    historial.append(nuevo_error)
    # Conserva los últimos 10 errores
    resumen = " | ".join(historial[-10:])
    with sqlite3.connect(DB_PATH) as conn:
        _asegurar_usuario(conn, user_id)
        conn.execute("UPDATE usuarios SET errores_frecuentes = ? WHERE user_id = ?", (resumen, user_id))


# ---------------------------------------------------------------- progreso
def obtener_progreso(user_id: int, idioma: str) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM progreso WHERE user_id = ? AND idioma = ?", (user_id, idioma)).fetchone()
        if row:
            return dict(row)
        return {"user_id": user_id, "idioma": idioma, "nivel": "A1", "ubicado": 0, "ultimo_cambio_id": 0,
                "nivel_max": "A1"}


def guardar_progreso(user_id: int, idioma: str, nivel: str, ubicado: bool, ultimo_cambio_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            # nivel_max: el más alto alcanzado. Los niveles se ordenan bien como texto (A1 < A2 < B1 < B2 < C1).
            """INSERT INTO progreso (user_id, idioma, nivel, ubicado, ultimo_cambio_id, nivel_max) VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT (user_id, idioma) DO UPDATE SET
                 nivel = excluded.nivel, ubicado = excluded.ubicado, ultimo_cambio_id = excluded.ultimo_cambio_id,
                 nivel_max = MAX(progreso.nivel_max, excluded.nivel)""",
            (user_id, idioma, nivel, int(ubicado), ultimo_cambio_id, nivel),
        )


def registrar_intento(user_id: int, idioma: str, tipo: str, correcto: int, errores_importantes: int = 0,
                      errores_leves: int = 0, tipos_error: str = "", nivel_frase: str | None = None,
                      puntaje: float | None = None) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO intentos (user_id, idioma, tipo, correcto, errores_importantes, errores_leves,
                                     tipos_error, nivel_frase, puntaje)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, idioma, tipo, correcto, errores_importantes, errores_leves, tipos_error, nivel_frase, puntaje),
        )
        return cur.lastrowid


def intentos(user_id: int, idioma: str, tipos: str | tuple, desde_id: int = 0) -> list:
    """Intentos de un usuario, del más viejo al más nuevo, con id mayor que desde_id.
    `tipos` es un tipo ("frase") o varios (("frase", "ejercicio"))."""
    tipos = (tipos,) if isinstance(tipos, str) else tuple(tipos)
    marcas = ",".join("?" * len(tipos))
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        filas = conn.execute(
            f"SELECT * FROM intentos WHERE user_id = ? AND idioma = ? AND tipo IN ({marcas}) AND id > ? ORDER BY id",
            (user_id, idioma, *tipos, desde_id),
        ).fetchall()
        return [dict(f) for f in filas]


def eliminar_usuario(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM usuarios WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM progreso WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM intentos WHERE user_id = ?", (user_id,))
