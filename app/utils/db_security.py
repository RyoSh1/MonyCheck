import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

LONGITUD_MINIMA_PASSWORD = 4

# Marca el fichero como "nuestro formato cifrado" para no depender de que no
# empiece por la cabecera de SQLite. Cambiar MAGIC invalida los ficheros ya
# cifrados con la versión anterior (no es el caso aquí, es la primera).
MAGIC = b"MCDB1"
TAMANO_SALT = 16
ITERACIONES_KDF = 480_000  # PBKDF2-HMAC-SHA256, recomendación OWASP 2023


def password_valida(password):
    """Vacía = sin cifrar (permitido, para quien no quiera contraseña). Si no
    está vacía, exige una longitud mínima para que no sea trivial de adivinar."""
    texto = password.strip()
    if texto == "":
        return True
    return len(texto) >= LONGITUD_MINIMA_PASSWORD


def generar_clave(password, salt=None):
    """Deriva una clave Fernet a partir de la contraseña. Sin `salt` genera
    una nueva aleatoria (BD nueva); pasándole la existente se reproduce la
    misma clave para descifrar o para reutilizarla dentro de la sesión."""
    if salt is None:
        salt = os.urandom(TAMANO_SALT)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERACIONES_KDF)
    clave = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return salt, clave


def es_archivo_cifrado(path):
    """Comprueba si el fichero está en nuestro formato cifrado (por la marca)"""
    try:
        with open(path, "rb") as f:
            return f.read(len(MAGIC)) == MAGIC
    except OSError:
        return False


def cifrar_archivo(path_origen, path_destino, salt, clave):
    """Cifra el contenido de path_origen y lo escribe en path_destino"""
    with open(path_origen, "rb") as f:
        datos = f.read()
    token = Fernet(clave).encrypt(datos)
    with open(path_destino, "wb") as f:
        f.write(MAGIC + salt + token)


def descifrar_archivo(path_cifrado, path_destino, password):
    """Descifra path_cifrado con la contraseña dada y escribe el resultado en
    path_destino. Devuelve (salt, clave) para reutilizarlos en la sesión.
    Lanza InvalidToken si la contraseña es incorrecta."""
    with open(path_cifrado, "rb") as f:
        contenido = f.read()
    resto = contenido[len(MAGIC):]
    salt, token = resto[:TAMANO_SALT], resto[TAMANO_SALT:]
    _, clave = generar_clave(password, salt=salt)
    datos = Fernet(clave).decrypt(token)
    with open(path_destino, "wb") as f:
        f.write(datos)
    return salt, clave


def verificar_password(db_path, password):
    """Comprueba si la contraseña abre la base de datos indicada, sin tocar
    disco salvo para leer el fichero existente. Se usa para validar antes de
    navegar a SecondView, así el usuario puede reintentar sin arrastrar una
    conexión inservible. Contraseña vacía = base de datos sin cifrar."""
    if not os.path.exists(db_path):
        return True  # BD nueva, se creará con esa contraseña
    if not es_archivo_cifrado(db_path):
        return password == ""
    try:
        with open(db_path, "rb") as f:
            contenido = f.read()
        resto = contenido[len(MAGIC):]
        salt, token = resto[:TAMANO_SALT], resto[TAMANO_SALT:]
        _, clave = generar_clave(password, salt=salt)
        Fernet(clave).decrypt(token)
        return True
    except Exception:
        return False
