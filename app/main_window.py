from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from app.views.home_view import HomeView
from app.views.second_view import SecondView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MonyCheck")
        self.setGeometry(100, 100, 1100, 700)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # vistas
        self.home_view = HomeView()
        self.stacked_widget.addWidget(self.home_view)
        self.home_view.navigate_requested.connect(self.navigate_to)

        # mantenemos la second view actual (la recreamos cada vez que se elija BD)
        self.current_second_view = None
        self.dark_mode = False

        # mostrar home
        self.navigate_to("home", None)

    def navigate_to(self, view_name, db_path=None):
        if view_name == "home":
            # refrescar la lista por si crearon una BD mientras tanto
            try:
                self.home_view.refrescar_lista_bd()
            except Exception:
                pass
            self.home_view.aplicar_tema(self.dark_mode)
            self.stacked_widget.setCurrentWidget(self.home_view)

        elif view_name == "second":
            if not db_path:
                QMessageBox.warning(self, "Error", "No se proporcionó la ruta a la BD.")
                return
            path, password = db_path

            # eliminar la segunda vista anterior (si existe) para no acumular widgets
            if self.current_second_view is not None:
                self.stacked_widget.removeWidget(self.current_second_view)
                self.current_second_view.deleteLater()
                self.current_second_view = None

            # crear nueva instancia de SecondView con la BD seleccionada
            self.current_second_view = SecondView(path, password)
            self.current_second_view.navigate_requested.connect(self.navigate_to)
            self.current_second_view.toggle_theme_requested.connect(self.toggle_theme)
            self.current_second_view.aplicar_tema(self.dark_mode)

            self.stacked_widget.addWidget(self.current_second_view)
            self.stacked_widget.setCurrentWidget(self.current_second_view)

    def toggle_theme(self):
        """Alterna entre tema claro y oscuro para la vista activa"""
        self.dark_mode = not self.dark_mode
        if self.current_second_view is not None:
            self.current_second_view.aplicar_tema(self.dark_mode)
