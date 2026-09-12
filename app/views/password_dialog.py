from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
                            QLineEdit, QLabel, QPushButton, QMessageBox)

from ..utils.db_security import password_valida, LONGITUD_MINIMA_PASSWORD


class PasswordDialog(QDialog):
    """Diálogo de contraseña. confirmar=True pide crear una nueva (dos
    campos, para una BD nueva); confirmar=False solo pide abrir (un campo)"""
    def __init__(self, confirmar=False, parent=None):
        super().__init__(parent)
        self.confirmar = confirmar
        self.setWindowTitle("Contraseña de la base de datos" if confirmar else "Introduce la contraseña")
        self.setFixedSize(340, 210 if confirmar else 150)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        if confirmar:
            self.input_password.setPlaceholderText("Déjalo en blanco para no cifrar")
        form.addRow("Contraseña:", self.input_password)

        if confirmar:
            self.input_confirmar = QLineEdit()
            self.input_confirmar.setEchoMode(QLineEdit.Password)
            form.addRow("Repite la contraseña:", self.input_confirmar)

        layout.addLayout(form)

        if confirmar:
            aviso = QLabel(
                "Si defines una contraseña, guárdala bien: no hay forma de "
                "recuperar los datos si la olvidas. Déjala en blanco si no "
                "quieres cifrar esta base de datos."
            )
            aviso.setWordWrap(True)
            aviso.setStyleSheet("color: #e74c3c; font-size: 11px;")
            layout.addWidget(aviso)

        botones = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_cancelar = QPushButton("Cancelar")
        btn_ok.clicked.connect(self._validar)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancelar)
        layout.addLayout(botones)

        self.setLayout(layout)

    def _validar(self):
        password = self.input_password.text()
        if not password_valida(password):
            QMessageBox.warning(self, "Contraseña muy corta",
                f"Usa al menos {LONGITUD_MINIMA_PASSWORD} caracteres, o déjala en blanco para no cifrar.")
            return
        if self.confirmar and password != self.input_confirmar.text():
            QMessageBox.warning(self, "No coincide", "Las dos contraseñas no coinciden.")
            return
        self.accept()

    def get_password(self):
        return self.input_password.text()
