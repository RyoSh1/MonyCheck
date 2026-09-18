import os
import glob
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QInputDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt
from app.models.database import DatabaseManager
from app.utils.theme import cargar_hoja_estilos
from app.utils.db_security import verificar_password
from app.views.password_dialog import PasswordDialog

class HomeView(QWidget):
    # Siempre emitimos (view_name, db_path_or_None)
    navigate_requested = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        # Sin esto, un QWidget no pinta su fondo de QSS al no ser ventana de nivel superior
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.db_layout = QVBoxLayout(container)
        scroll.setWidget(container)
        self.layout.addWidget(scroll)

        btn_crear = QPushButton("➕ Crear nueva base de datos")
        btn_crear.setObjectName("primaryButton")
        btn_crear.clicked.connect(self.crear_nueva_bd)
        self.layout.addWidget(btn_crear)

        self.refrescar_lista_bd()
        self.aplicar_tema(False)

    def aplicar_tema(self, oscuro):
        """Alterna entre la hoja de estilos clara y la oscura"""
        self.setStyleSheet(cargar_hoja_estilos(oscuro))

    def refrescar_lista_bd(self):
        # limpiar layout
        while self.db_layout.count():
            w = self.db_layout.takeAt(0).widget()
            if w:
                w.setParent(None)

        archivos = sorted(glob.glob("*.db") + glob.glob("*.bd"))
        for filename in archivos:
            btn = QPushButton(f"🗂  {os.path.basename(filename)}")
            btn.setObjectName("dbListButton")
            # enviamos ruta absoluta para evitar problemas con cwd
            btn.clicked.connect(lambda checked, f=os.path.abspath(filename): self.abrir_bd(f))
            self.db_layout.addWidget(btn)

    def abrir_bd(self, path):
        """Pide la contraseña y solo navega si abre correctamente la BD"""
        while True:
            dialogo = PasswordDialog(confirmar=False, parent=self)
            if not dialogo.exec_():
                return
            password = dialogo.get_password()
            if verificar_password(path, password):
                self.navigate_requested.emit("second", (path, password))
                return
            QMessageBox.warning(self, "Contraseña incorrecta",
                "No se ha podido abrir la base de datos con esa contraseña.")

    def crear_nueva_bd(self):
        nombre, ok = QInputDialog.getText(self, "Nueva BD", "Nombre de la base de datos (sin extensión):")
        if not ok:
            return
        nombre = nombre.strip()
        if not nombre:
            QMessageBox.warning(self, "Nombre vacío", "Escribe un nombre válido.")
            return
        # evitar barras, rutas, etc.
        nombre = os.path.basename(nombre)
        if not nombre.lower().endswith(".db"):
            nombre += ".db"
        path = os.path.abspath(nombre)
        if os.path.exists(path):
            QMessageBox.warning(self, "Ya existe", "Ya existe un archivo con ese nombre.")
            return

        dialogo = PasswordDialog(confirmar=True, parent=self)
        if not dialogo.exec_():
            return
        password = dialogo.get_password()

        # inicializamos la BD y cerramos: SecondView abrirá su propia conexión
        DatabaseManager(path, password).cerrar()
        self.refrescar_lista_bd()
        # navegamos a la segunda pantalla con la BD recién creada
        self.navigate_requested.emit("second", (path, password))
