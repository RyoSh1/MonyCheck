from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QListWidget, 
                            QPushButton, QHBoxLayout, QMessageBox, QLineEdit, QLabel)

class TagDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Etiqueta")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Introduce el nombre de la nueva etiqueta:")
        self.input = QLineEdit()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self.accept)
        
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.btn_guardar)
        
        self.setLayout(layout)
    
    def get_tag_name(self):
        return self.input.text().strip()

class TagManagerDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Gestión de Etiquetas")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Lista de etiquetas
        self.list_widget = QListWidget()
        self.actualizar_lista()
        
        # Botones
        btn_layout = QHBoxLayout()
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_tag)
        self.btn_nuevo = QPushButton("Nueva Etiqueta")
        self.btn_nuevo.clicked.connect(self.nueva_tag)
        
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addWidget(self.btn_nuevo)
        
        layout.addWidget(self.list_widget)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def actualizar_lista(self):
        self.list_widget.clear()
        tags = self.db.obtener_tags()
        self.list_widget.addItems(tags)
    
    def eliminar_tag(self):
        item = self.list_widget.currentItem()
        if item:
            tag = item.text()
            if tag == "compra":
                QMessageBox.warning(self, "Error", "No se puede eliminar la etiqueta por defecto")
                return
                
            reply = QMessageBox.question(
                self, "Confirmar", 
                f"¿Eliminar la etiqueta '{tag}'?\nLos gastos asociados se cambiarán a 'compra'",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.db.eliminar_tag(tag):
                    self.actualizar_lista()
    
    def nueva_tag(self):
        dialog = TagDialog(self)
        if dialog.exec_():
            nuevo_tag = dialog.get_tag_name()
            if nuevo_tag:
                if self.db.agregar_tag(nuevo_tag):
                    self.actualizar_lista()
                else:
                    QMessageBox.warning(self, "Error", "No se pudo añadir la etiqueta")