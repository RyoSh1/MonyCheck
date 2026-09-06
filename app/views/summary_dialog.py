from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, 
                            QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt

class SummaryDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Resúmenes Mensuales")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Widget de pestañas
        self.tab_widget = QTabWidget()
        
        # Obtener y procesar todos los meses disponibles
        self.cargar_resumenes()
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def cargar_resumenes(self):
        """Carga los resúmenes mensuales en las pestañas"""
        meses = self.obtener_meses_disponibles()
        
        for mes in meses:
            # Crear pestaña para cada mes
            tab = QWidget()
            tab_layout = QVBoxLayout()
            
            # Resumen estadístico
            resumen = self.obtener_resumen_mes(mes)
            lbl_resumen = QLabel(
                f"Resumen {mes}:   "
                f"Ingresos: +{resumen['ingresos']:.2f}€   "
                f"Gastos: -{resumen['gastos']:.2f}€   "
                f"Balance: ={resumen['balance']:.2f}€"
            )
            lbl_resumen.setStyleSheet("font-weight: bold; font-size: 14px;")
            
            # Tabla de transacciones
            tabla = QTableWidget()
            tabla.setColumnCount(5)
            tabla.setHorizontalHeaderLabels(["Fecha", "Etiqueta", "Cantidad", "Tipo", "Comentario"])
            tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            transacciones = self.obtener_transacciones_mes(mes)
            tabla.setRowCount(len(transacciones))

            for row, (fecha, tag, cantidad, _, comentario) in enumerate(transacciones):
                tabla.setItem(row, 0, QTableWidgetItem(fecha))
                tabla.setItem(row, 1, QTableWidgetItem(tag))

                item_cantidad = QTableWidgetItem(f"{cantidad:.2f}€")
                item_cantidad.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                if cantidad >= 0:
                    item_cantidad.setForeground(Qt.darkGreen)
                    tipo = "Ingreso"
                else:
                    item_cantidad.setForeground(Qt.darkRed)
                    tipo = "Gasto"

                tabla.setItem(row, 2, item_cantidad)
                tabla.setItem(row, 3, QTableWidgetItem(tipo))
                tabla.setItem(row, 4, QTableWidgetItem(comentario or ""))
            
            tab_layout.addWidget(lbl_resumen)
            tab_layout.addWidget(tabla)
            tab.setLayout(tab_layout)
            
            self.tab_widget.addTab(tab, mes)

    def obtener_meses_disponibles(self):
        """Obtiene la lista de meses/años disponibles en la BD"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT strftime('%Y-%m', timestamp) as mes
                    FROM gastos
                    ORDER BY mes DESC
                """)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error obteniendo meses: {str(e)}")
            return []

    def obtener_resumen_mes(self, mes):
        """Calcula el resumen para un mes específico"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN gasto > 0 THEN gasto ELSE 0 END) as ingresos,
                        SUM(CASE WHEN gasto < 0 THEN ABS(gasto) ELSE 0 END) as gastos
                    FROM gastos
                    WHERE strftime('%Y-%m', timestamp) = ?
                """, (mes,))
                
                ingresos, gastos = cursor.fetchone()
                return {
                    'ingresos': ingresos or 0,
                    'gastos': gastos or 0,
                    'balance': (ingresos or 0) - (gastos or 0)
                }
        except Exception as e:
            print(f"Error obteniendo resumen: {str(e)}")
            return {'ingresos': 0, 'gastos': 0, 'balance': 0}

    def obtener_transacciones_mes(self, mes):
        """Obtiene todas las transacciones de un mes"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        strftime('%d/%m/%Y', timestamp) as fecha,
                        tag,
                        gasto,
                        timestamp,
                        comentario
                    FROM gastos
                    WHERE strftime('%Y-%m', timestamp) = ?
                    ORDER BY timestamp DESC
                """, (mes,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error obteniendo transacciones: {str(e)}")
            return []