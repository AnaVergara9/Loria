import sqlite3

DB_PATH = "parley.db"

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

def obtener_usuario(user_id: int) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM usuarios WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            conn.execute("INSERT INTO usuarios (user_id) VALUES (?)", (user_id,))
            return {
                "user_id": user_id,
                "perfil": "adulto",
                "consentimiento": 0,
                "frase_objetivo": None,
                "fonemas_objetivo": None,
                "errores_frecuentes": ""
            }
        return dict(row)

def guardar_perfil(user_id: int, perfil: str):
    obtener_usuario(user_id)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE usuarios SET perfil = ?, consentimiento = 1 WHERE user_id = ?",
            (perfil, user_id)
        )

def guardar_ejercicio(user_id: int, frase: str | None, fonemas: str | None):
    obtener_usuario(user_id)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE usuarios SET frase_objetivo = ?, fonemas_objetivo = ? WHERE user_id = ?",
            (frase, fonemas, user_id)
        )

def registrar_error(user_id: int, nuevo_error: str):
    u = obtener_usuario(user_id)
    historial = [e for e in u["errores_frecuentes"].split(" | ") if e]
    historial.append(nuevo_error)
    # Conserva los últimos 10 errores
    resumen = " | ".join(historial[-10:])
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE usuarios SET errores_frecuentes = ? WHERE user_id = ?", (resumen, user_id))

def eliminar_usuario(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM usuarios WHERE user_id = ?", (user_id,))