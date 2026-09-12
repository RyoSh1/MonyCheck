from sqlcipher3 import dbapi2 as sqlite3

LONGITUD_MINIMA_PASSWORD = 4


def pragma_key_sql(password): # Dudas con el sistema
    """Construye el PRAGMA key escapando comillas simples.
    SQLCipher no soporta parámetros ligados (?) en PRAGMA key, así que hay
    que escapar a mano (' -> '') como en cualquier literal SQL. execute()
    solo permite una sentencia por llamada, así que no hay forma de colar
    una segunda sentencia aunque la contraseña llevase un ';'."""
    return "PRAGMA key = '" + password.replace("'", "''") + "'"


def password_valida(password):
    """Vacía = sin cifrar (permitido, para quien no quiera contraseña). Si no
    está vacía, exige una longitud mínima para que no sea trivial de adivinar."""
    texto = password.strip()
    if texto == "":
        return True
    return len(texto) >= LONGITUD_MINIMA_PASSWORD


def verificar_password(db_path, password):
    """Comprueba si la contraseña abre la base de datos indicada, sin dejar
    ninguna tabla a medio tocar. Se usa para validar antes de navegar a
    SecondView, así el usuario puede reintentar sin arrastrar una conexión
    inservible. Contraseña vacía = base de datos sin cifrar."""
    try:
        conn = sqlite3.connect(db_path)
        if password:
            conn.execute(pragma_key_sql(password))
        conn.execute("SELECT count(*) FROM sqlite_master")
        conn.close()
        return True
    except Exception:
        return False
