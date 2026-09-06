from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
                            QLineEdit, QComboBox, QRadioButton, QPushButton,
                            QMessageBox, QButtonGroup)

from ..utils.validators import DecimalValidator, parse_monto


class EditarGastoDialog(QDialog):
    """Diálogo para modificar un registro existente: etiqueta, importe y comentario"""
    def __init__(self, db, gasto, parent=None):
        super().__init__(parent)
        self.db = db
        self.id_gasto, _, self.cantidad_original, _, self.comentario_original = gasto

        self.setWindowTitle("Editar registro")
        self.setFixedSize(320, 220)

        layout = QVBoxLayout()
        form = QFormLayout()

        tipo_row = QHBoxLayout()
        self.radio_ingreso = QRadioButton("Ingreso")
        self.radio_gasto = QRadioButton("Gasto")
        grupo_tipo = QButtonGroup(self)
        grupo_tipo.addButton(self.radio_ingreso)
        grupo_tipo.addButton(self.radio_gasto)
        tipo_row.addWidget(self.radio_ingreso)
        tipo_row.addWidget(self.radio_gasto)
        form.addRow("Tipo:", tipo_row)

        self.input_importe = QLineEdit()
        validator = DecimalValidator(0, 999999, 2, self)
        self.input_importe.setValidator(validator)
        form.addRow("Importe:", self.input_importe)

        self.combo_etiqueta = QComboBox()
        self.combo_etiqueta.addItems(self.db.obtener_tags())
        form.addRow("Etiqueta:", self.combo_etiqueta)

        self.input_comentario = QLineEdit()
        self.input_comentario.setPlaceholderText("Comentario (opcional)")
        form.addRow("Comentario:", self.input_comentario)

        layout.addLayout(form)

        botones = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar.clicked.connect(self._guardar)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_guardar)
        botones.addWidget(btn_cancelar)
        layout.addLayout(botones)

        self.setLayout(layout)
        self._precargar_valores(gasto)

    def _precargar_valores(self, gasto):
        _, tag, cantidad, _, comentario = gasto
        if cantidad >= 0:
            self.radio_ingreso.setChecked(True)
        else:
            self.radio_gasto.setChecked(True)
        self.input_importe.setText(f"{abs(cantidad):.2f}")

        indice = self.combo_etiqueta.findText(tag)
        if indice == -1:
            self.combo_etiqueta.addItem(tag)
            indice = self.combo_etiqueta.findText(tag)
        self.combo_etiqueta.setCurrentIndex(indice)

        self.input_comentario.setText(comentario or "")

    def _guardar(self):
        texto_importe = self.input_importe.text().strip()
        if not texto_importe:
            QMessageBox.warning(self, "Campo vacío", "Introduce un importe")
            return
        try:
            importe = parse_monto(texto_importe)
        except ValueError:
            QMessageBox.warning(self, "Valor inválido", "Formato: 25,99 o 25.99")
            return

        if self.radio_gasto.isChecked():
            importe = -abs(importe)
        else:
            importe = abs(importe)

        tag = self.combo_etiqueta.currentText()
        comentario = self.input_comentario.text().strip()

        if self.db.actualizar_gasto(self.id_gasto, tag, importe, comentario):
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "No se pudo actualizar el registro")
