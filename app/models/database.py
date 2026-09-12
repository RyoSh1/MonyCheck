from sqlcipher3 import dbapi2 as sqlite3
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox
from ..utils.db_security import pragma_key_sql

class DatabaseManager:
    def __init__(self, db_path, password=""):
        self.db_path = db_path
        self.password = password
        self._initialize_db()

    def _initialize_db(self):
        """Crea la base de datos y tablas si no existen"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS gastos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag TEXT NOT NULL,
                        gasto REAL NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """)
                # Tabla para tags disponibles
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT UNIQUE NOT NULL
                    )
                """)
                # Insertar tag por defecto si no existe
                cursor.execute("""
                    INSERT OR IGNORE INTO tags (nombre) VALUES ('compra')
                """)
                # Migración: añadir columna de comentario a BDs creadas antes de esta versión
                columnas = [fila[1] for fila in cursor.execute("PRAGMA table_info(gastos)")]
                if "comentario" not in columnas:
                    cursor.execute("ALTER TABLE gastos ADD COLUMN comentario TEXT NOT NULL DEFAULT ''")
        except Exception as e:
            QMessageBox.critical(None, "Error de BD", f"No se pudo inicializar la BD: {str(e)}")

    def _get_connection(self):
        """Retorna una conexión a la base de datos, cifrada si hay contraseña"""
        conn = sqlite3.connect(self.db_path)
        if self.password:
            conn.execute(pragma_key_sql(self.password))
        return conn

    def agregar_gasto(self, tag, gasto, comentario=""):
        """Añade un nuevo gasto a la base de datos"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO gastos (tag, gasto, timestamp, comentario)
                    VALUES (? , ?, ?, ?)
                """, (tag, gasto, datetime.now().isoformat(), comentario)) # Maybe aquí se puede añadir en tag o comentario algo ejecutable
                conn.commit()
            return True
        except Exception as e:
            QMessageBox.critical(None, "Error", f"No se pudo guardar el gasto: {str(e)}")
            return False

    def actualizar_gasto(self, id_gasto, tag, gasto, comentario=""):
        """Actualiza un gasto existente"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE gastos SET tag = ?, gasto = ?, comentario = ?
                    WHERE id = ?
                """, (tag, gasto, comentario, id_gasto))
                conn.commit()
            return True
        except Exception as e:
            QMessageBox.critical(None, "Error", f"No se pudo actualizar el gasto: {str(e)}")
            return False

    def obtener_gastos(self, limit=100):
        """Obtiene los últimos gastos registrados"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, tag, gasto, timestamp, comentario
                    FROM gastos
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except Exception as e:
            QMessageBox.critical(None, "Error", f"No se pudieron obtener gastos: {str(e)}")
            return []

    def obtener_tags(self):
        """Obtiene todos los tags disponibles"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nombre FROM tags")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            QMessageBox.critical(None, "Error", f"No se pudieron obtener tags: {str(e)}")
            return ["compra"]  # Valor por defecto si hay error

    def obtener_gastos_por_periodo(self, dias=None, mes_actual=False):
        """Obtiene gastos por periodo especificado"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if dias:
                    query = """
                        SELECT id, tag, gasto, timestamp, comentario
                        FROM gastos
                        WHERE date(timestamp) >= date('now', ?)
                        ORDER BY timestamp DESC
                    """
                    cursor.execute(query, (f"-{dias} days",))
                elif mes_actual:
                    query = """
                        SELECT id, tag, gasto, timestamp, comentario
                        FROM gastos
                        WHERE strftime('%m', timestamp) = strftime('%m', 'now')
                        AND strftime('%Y', timestamp) = strftime('%Y', 'now')
                        ORDER BY timestamp DESC
                    """
                    cursor.execute(query)
                
                return cursor.fetchall()  # Retorna lista de tuplas (id, tag, gasto, timestamp)
        except Exception as e:
            print(f"Error obteniendo gastos por periodo: {str(e)}")
            return []
    def agregar_tag(self, nombre_tag):
        """Añade un nuevo tag a la base de datos"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO tags (nombre) VALUES (?)", (nombre_tag,))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "Tag existente", "Esta etiqueta ya existe")
            return False
        except Exception as e:
            QMessageBox.critical(None, "Error", f"No se pudo añadir tag: {str(e)}")
            return False

    def eliminar_tag(self, nombre_tag):
        """Elimina un tag de la base de datos"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Actualizar gastos con este tag a 'compra' (tag por defecto)
                cursor.execute("""
                    UPDATE gastos SET tag = 'compra' 
                    WHERE tag = ?
                """, (nombre_tag,))
                # Eliminar el tag
                cursor.execute("DELETE FROM tags WHERE nombre = ?", (nombre_tag,))
                conn.commit()
            return True
        except Exception as e:
            QMessageBox.critical(None, "Error", f"No se pudo eliminar tag: {str(e)}")
            return False