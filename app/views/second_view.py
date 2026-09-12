from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QMenu, QScrollArea, QFormLayout,
                            QMessageBox, QDialog, QFrame)

from PyQt5.QtGui import QDoubleValidator, QColor
from ..utils.charts import crear_grafico_tarta
from ..utils.theme import cargar_hoja_estilos
from ..utils.validators import DecimalValidator, parse_monto
from ..models.database import DatabaseManager
from .tag_dialog import TagDialog, TagManagerDialog
from .entry_dialog import EditarGastoDialog
from datetime import datetime

class SecondView(QWidget):
    navigate_requested = pyqtSignal(str)
    toggle_theme_requested = pyqtSignal()  # Nueva señal para cambiar tema

    def __init__(self, db_path, password=""):
        super().__init__()
        # Sin esto, un QWidget no pinta su fondo de QSS al no ser ventana de nivel superior
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.db = DatabaseManager(db_path, password)
        self.init_ui()
        self.aplicar_tema(False)
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # --- PRIMERA FILA: Barra superior ---
        top_bar = QHBoxLayout()
        
        # Botón Volver
        self.back_btn = QPushButton("← Volver")
        self.back_btn.clicked.connect(lambda: self.navigate_requested.emit("home"))

        # Botón Resúmenes
        self.btn_resumenes = QPushButton("Resúmenes")
        self.btn_resumenes.clicked.connect(self.mostrar_resumenes)

        # Botón Ajustes
        self.settings_btn = QPushButton("⚙ Ajustes")
        self.settings_btn.clicked.connect(self._show_settings_dialog)

        # Añadir al layout de la barra superior
        top_bar.addWidget(self.back_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_resumenes)
        top_bar.addWidget(self.settings_btn)
        main_layout.addLayout(top_bar)
        
        # --- SEGUNDA FILA: Controles grandes ---
        controls_row = QHBoxLayout()
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setSpacing(5)

        # Widget contenedor para etiquetas (para mejor agrupación)
        etiquetas_widget = QWidget()
        etiquetas_layout = QHBoxLayout(etiquetas_widget)
        etiquetas_layout.setContentsMargins(0, 0, 0, 0)
        etiquetas_layout.setSpacing(5)

        # Menú desplegable izquierdo
        self.menu_btn_etiquetas = QPushButton("Etiqueta: compra")  # Texto inicial
        self.menu_btn_etiquetas.setObjectName("tagMenuButton")
        self.tag_actual = "compra"  # Etiqueta por defecto

        # Configurar menú de etiquetas
        self.menu_etiquetas = QMenu()
        self.actualizar_menu_etiquetas()
        self.menu_btn_etiquetas.setMenu(self.menu_etiquetas)

        # Botón para gestión avanzada
        self.btn_gestion_etiquetas = QPushButton("⚙")
        self.btn_gestion_etiquetas.setObjectName("tagsGearButton")
        self.btn_gestion_etiquetas.setToolTip("Gestionar etiquetas")
        self.btn_gestion_etiquetas.clicked.connect(self.mostrar_gestion_etiquetas)

        # Añadir al layout de etiquetas
        etiquetas_layout.addWidget(self.menu_btn_etiquetas)
        etiquetas_layout.addWidget(self.btn_gestion_etiquetas)

        # Añadir al layout (reemplazando el anterior)
        controls_row.addWidget(etiquetas_widget, stretch=1)

        # Input de búsqueda (más grande)
        # Configurar el input con el validador personalizado
        self.search_input = QLineEdit()
        self.search_input.setObjectName("montoInput")
        self.search_input.setPlaceholderText("Ej: 25,99 o -25,99 (+Enter)")
        # Bottom negativo: permite escribir "-24" para registrar directamente un gasto
        validator = DecimalValidator(-999999, 999999, 2, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.search_input.setValidator(validator) # Solo números
        self.search_input.returnPressed.connect(lambda: self._guardar_gasto(positivo=None))

        # Botones +/- fusionados en un único control dividido en dos mitades
        buttons_column = QVBoxLayout()
        self.btn_plus = QPushButton("+")
        self.btn_minus = QPushButton("-")
        self.btn_plus.setObjectName("btnPlus")
        self.btn_minus.setObjectName("btnMinus")
        self.btn_plus.clicked.connect(lambda: self._guardar_gasto(positivo=True))
        self.btn_minus.clicked.connect(lambda: self._guardar_gasto(positivo=False))
        buttons_column.addWidget(self.btn_plus)
        buttons_column.addWidget(self.btn_minus)
        buttons_column.setSpacing(0)
        
        # Layout combinado
        input_buttons_row = QHBoxLayout()
        input_buttons_row.addWidget(self.search_input)
        input_buttons_row.addLayout(buttons_column)
        
        # Añadir a la fila de controles
        controls_row.addLayout(input_buttons_row, stretch=3)
        main_layout.addLayout(controls_row)
        
        # --- TERCERA FILA: Columnas de contenido ---
        content_row = QHBoxLayout()
        
        # Crear las tres columnas con la misma estructura base
        self.col1 = self._create_stats_column("Últimos 30 días")
        self.col2 = self._create_stats_column("Último mes")
        self.col3 = self._create_entries_column("Últimas entradas")

        # Añadir a la fila con el mismo stretch
        content_row.addWidget(self.col1, stretch=1)
        content_row.addWidget(self.col2, stretch=1)
        content_row.addWidget(self.col3, stretch=1)

        main_layout.addLayout(content_row, stretch=1)

        # Configurar menú de etiquetas
        self.tag_actual = "compra"  # Etiqueta por defecto
        self.actualizar_menu_etiquetas()

        self.actualizar_todo()

        self.setLayout(main_layout)

    def _create_stats_column(self, title):
        """Crea una columna de estadísticas con título"""
        card = QFrame()
        card.setObjectName("card")
        card.setAttribute(Qt.WA_StyledBackground, True)
        column = QVBoxLayout(card)
        column.setSpacing(10)

        # Título
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("col_title")
        title_label.setFixedHeight(50)
        column.addWidget(title_label)

        # Labels para los valores (definidos como atributos)
        if "30 días" in title:
            self.label_30d_ingresos = QLabel("+0.00")
            self.label_30d_gastos = QLabel("-0.00")
            self.label_30d_balance = QLabel("0.00")

            stats = QFormLayout()
            stats.setFormAlignment(Qt.AlignHCenter)
            stats.addRow("Ingresos:", self.label_30d_ingresos)
            stats.addRow("Gastos:", self.label_30d_gastos)
            stats.addRow("Resultado:", self.label_30d_balance)
        else:
            self.label_mes_ingresos = QLabel("+0.00")
            self.label_mes_gastos = QLabel("-0.00")
            self.label_mes_balance = QLabel("0.00")

            stats = QFormLayout()
            stats.setFormAlignment(Qt.AlignHCenter)
            stats.addRow("Ingresos:", self.label_mes_ingresos)
            stats.addRow("Gastos:", self.label_mes_gastos)
            stats.addRow("Resultado:", self.label_mes_balance)

        column.addLayout(stats)

        # Gráfico (se sustituye por uno real en cuanto hay datos)
        chart = QLabel("Cargando...")
        chart.setAlignment(Qt.AlignCenter)
        chart.setMinimumHeight(150)
        column.addWidget(chart)

        if "30 días" in title:
            self.chart_30d = chart  # Guardar referencia para actualizaciones
        else:
            self.chart_mes = chart

        return card

    def _create_entries_column(self, title):
        """Crea la columna de entradas con scroll"""
        card = QFrame()
        card.setObjectName("card")
        card.setAttribute(Qt.WA_StyledBackground, True)
        column = QVBoxLayout(card)
        column.setSpacing(10)

        # Título (misma altura que las otras columnas)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("col_title")
        title_label.setFixedHeight(50)
        column.addWidget(title_label)

        # Área de scroll (definida como atributo)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Widget de contenido (definido como atributo)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)  # Definido como atributo

        # Configurar el layout del scroll
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(5)

        # Añadir entradas iniciales
        self._load_initial_entries()

        self.scroll_area.setWidget(self.scroll_content)
        column.addWidget(self.scroll_area)

        return card

    def _load_initial_entries(self):
        """Carga las entradas iniciales desde la base de datos"""
        # Limpiar cualquier entrada existente
        self._clear_entries()
        
        # Obtener gastos de la base de datos
        gastos = self.db.obtener_gastos(limit=20)
        
        # Añadir las entradas al layout
        for gasto in gastos:
            self._add_entry_to_layout(gasto)

    def _clear_entries(self):
        """Elimina todas las entradas del layout"""
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def _add_entry_to_layout(self, gasto):
        """Añade una sola entrada al layout"""
        id_gasto, tag, cantidad, timestamp, comentario = gasto
        signo = "+" if cantidad >= 0 else "-"

        # Formatear la fecha
        fecha = datetime.fromisoformat(timestamp).strftime("%d/%m/%Y %H:%M")

        # Crear el widget de entrada
        entry_widget = QWidget()
        entry_layout = QVBoxLayout(entry_widget)
        entry_layout.setContentsMargins(5, 2, 5, 2)
        entry_layout.setSpacing(2)

        fila_principal = QHBoxLayout()

        # Etiqueta de cantidad
        amount_label = QLabel(f"{signo}${abs(cantidad):.2f}")
        amount_label.setAlignment(Qt.AlignLeft)
        amount_label.setStyleSheet(f"color: {'#27ae60' if cantidad >=0 else '#e74c3c'}; font-weight: bold;")

        # Etiqueta de tag y fecha
        details_label = QLabel(f"{tag} - {fecha}")
        details_label.setAlignment(Qt.AlignRight)
        details_label.setStyleSheet("color: #7f8c8d;")

        # Botón para editar el registro
        btn_editar = QPushButton("✎")
        btn_editar.setObjectName("iconButton")
        btn_editar.setToolTip("Editar registro")
        btn_editar.clicked.connect(lambda checked, g=gasto: self._editar_entrada(g))

        fila_principal.addWidget(amount_label)
        fila_principal.addStretch()
        fila_principal.addWidget(details_label)
        fila_principal.addWidget(btn_editar)
        entry_layout.addLayout(fila_principal)

        # Comentario opcional
        if comentario:
            comentario_label = QLabel(comentario)
            comentario_label.setWordWrap(True)
            comentario_label.setStyleSheet("color: #95a5a6; font-style: italic;")
            entry_layout.addWidget(comentario_label)

        # Añadir al scroll layout
        self.scroll_layout.addWidget(entry_widget)

    def _editar_entrada(self, gasto):
        """Abre el diálogo de edición para un registro existente"""
        dialog = EditarGastoDialog(self.db, gasto, self)
        if dialog.exec_():
            self.actualizar_todo()

    def actualizar_ultimas_entradas(self):
        """Actualiza la lista de entradas"""
        self._load_initial_entries()
    
    def _show_settings_dialog(self):
        """Muestra el diálogo de ajustes"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajustes")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        # Botón para cambiar tema
        theme_btn = QPushButton("Cambiar Tema")
        theme_btn.clicked.connect(self.toggle_theme_requested.emit)
        layout.addWidget(theme_btn)
        
        # Espacio para futuros ajustes
        layout.addStretch()
        layout.addWidget(QLabel("Más opciones próximamente..."))
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def aplicar_tema(self, oscuro):
        """Alterna entre la hoja de estilos clara y la oscura"""
        self.setStyleSheet(cargar_hoja_estilos(oscuro))

    def actualizar_menu_etiquetas(self):
        """Actualiza el menú desplegable con las etiquetas disponibles"""
        self.menu_etiquetas.clear()
        tags = self.db.obtener_tags()
        
        # Añadir etiquetas al menú
        for tag in tags:
            action = self.menu_etiquetas.addAction(tag)
            action.triggered.connect(lambda _, t=tag: self.seleccionar_etiqueta(t))
        
        # Añadir separador y opción de gestión
        self.menu_etiquetas.addSeparator()
        gestion_action = self.menu_etiquetas.addAction("+ Nueva etiqueta")
        gestion_action.triggered.connect(self.mostrar_dialogo_etiqueta)

    def seleccionar_etiqueta(self, tag):
        """Establece la etiqueta seleccionada para nuevos gastos"""
        self.tag_actual = tag
        self.menu_btn_etiquetas.setText(f"Etiqueta: {tag}")

    def mostrar_dialogo_etiqueta(self):
        """Muestra el diálogo para crear nueva etiqueta"""
        dialog = TagDialog(self)
        if dialog.exec_():
            nuevo_tag = dialog.get_tag_name()
            if nuevo_tag:
                if self.db.agregar_tag(nuevo_tag):
                    self.actualizar_menu_etiquetas()
                    self.seleccionar_etiqueta(nuevo_tag)

    def mostrar_gestion_etiquetas(self):
        """Muestra el diálogo completo de gestión de etiquetas"""
        dialog = TagManagerDialog(self.db, self)
        dialog.exec_()
        self.actualizar_menu_etiquetas()

    def _guardar_gasto(self, positivo):
        """Guarda un gasto usando los botones +/- (fuerzan el signo, ignorando el que se haya escrito)"""
        try:
            cantidad_texto = self.search_input.text().strip()
            if not cantidad_texto:
                QMessageBox.warning(self, "Campo vacío", "Introduce una cantidad")
                return

            try:
                cantidad = parse_monto(cantidad_texto)
            except ValueError:
                QMessageBox.warning(self, "Valor inválido", "Formato: 25,99 o 25.99")
                return
            if positivo == True:
                cantidad = abs(cantidad)
            elif positivo == False:
                cantidad = -abs(cantidad)
                
            self._registrar_gasto(cantidad)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")

    def _registrar_gasto(self, cantidad):
        """Guarda el importe (ya con su signo definitivo) y refresca la vista"""
        if self.db.agregar_gasto(self.tag_actual, cantidad):
            self.search_input.clear()
            self.actualizar_todo()
            QMessageBox.information(self, "Éxito", "Gasto registrado correctamente")
        else:
            QMessageBox.warning(self, "Error", "No se pudo guardar el gasto")

    def actualizar_todo(self):
        """Actualiza todas las secciones de la vista"""
        self.actualizar_ultimas_entradas()
        self.actualizar_resumen_30dias()
        self.actualizar_resumen_mes()

    def actualizar_resumen_30dias(self):
        """Calcula y muestra el resumen de últimos 30 días"""
        try:
            # Obtener gastos de los últimos 30 días
            registros = self.db.obtener_gastos_por_periodo(dias=30)

            # Extraer solo los valores numéricos (el índice 2 de cada tupla)
            gastos = [registro[2] for registro in registros]

            # Calcular totales
            ingresos = sum(g for g in gastos if g > 0)
            gastos_totales = sum(abs(g) for g in gastos if g < 0)
            balance = ingresos - gastos_totales

            # Actualizar UI
            self.label_30d_ingresos.setText(f"+{ingresos:.2f}€")
            self.label_30d_gastos.setText(f"-{gastos_totales:.2f}€")
            self.label_30d_balance.setText(f"{balance:.2f}€")

            self.chart_30d = self._reemplazar_grafico(self.chart_30d, ingresos, gastos_totales)

        except Exception as e:
            print(f"Error actualizando 30 días: {str(e)}")

    def actualizar_resumen_mes(self):
        """Calcula y muestra el resumen del mes actual"""
        try:
            # Obtener gastos del mes actual
            registros = self.db.obtener_gastos_por_periodo(mes_actual=True)

            # Extraer solo los valores numéricos
            gastos = [registro[2] for registro in registros]

            # Calcular totales
            ingresos = sum(g for g in gastos if g > 0)
            gastos_totales = sum(abs(g) for g in gastos if g < 0)
            balance = ingresos - gastos_totales

            # Actualizar UI
            self.label_mes_ingresos.setText(f"+{ingresos:.2f}€")
            self.label_mes_gastos.setText(f"-{gastos_totales:.2f}€")
            self.label_mes_balance.setText(f"{balance:.2f}€")

            self.chart_mes = self._reemplazar_grafico(self.chart_mes, ingresos, gastos_totales)

        except Exception as e:
            print(f"Error actualizando mes: {str(e)}")

    def _reemplazar_grafico(self, chart_actual, ingresos, gastos):
        """Sustituye el gráfico de un periodo por uno con los totales actuales"""
        datos = {}
        colores = []
        if ingresos > 0:
            datos["Ingresos"] = ingresos
            colores.append(QColor('#27ae60'))
        if gastos > 0:
            datos["Gastos"] = gastos
            colores.append(QColor('#e74c3c'))

        if datos:
            # Sin título propio (ya está el de la tarjeta) y leyenda abajo para
            # dejarle todo el ancho disponible a la tarta en una tarjeta estrecha
            nuevo = crear_grafico_tarta("", datos, colores=colores)
            nuevo.chart().legend().setAlignment(Qt.AlignBottom)
        else:
            nuevo = QLabel("Sin datos en este periodo")
            nuevo.setAlignment(Qt.AlignCenter)
        nuevo.setMinimumHeight(150)

        layout = chart_actual.parent().layout() if chart_actual.parent() else None
        if layout:
            indice = layout.indexOf(chart_actual)
            layout.removeWidget(chart_actual)
            chart_actual.hide()
            layout.insertWidget(indice, nuevo)
        chart_actual.deleteLater()
        return nuevo

    def mostrar_resumenes(self):
        """Muestra el diálogo de resúmenes mensuales"""
        from .summary_dialog import SummaryDialog  # Importación local para evitar circular
        dialog = SummaryDialog(self.db, self)
        dialog.exec_()