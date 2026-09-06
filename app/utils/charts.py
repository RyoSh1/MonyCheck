from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter

def crear_grafico_tarta(titulo, datos, parent=None, colores=None):
    """Crea un gráfico de tarta interactivo"""
    series = QPieSeries()

    # Colores predefinidos para los segmentos (o los indicados explícitamente)
    if colores is None:
        colores = [
            QColor('#3498db'), QColor('#e74c3c'), QColor('#2ecc71'),
            QColor('#f39c12'), QColor('#9b59b6'), QColor('#1abc9c')
        ]

    for i, (tag, valor) in enumerate(datos.items()):
        slice_ = series.append(f"{tag} (${valor:.2f})", valor)
        slice_.setColor(colores[i % len(colores)])
        # La etiqueta solo se muestra al pasar el ratón (ver hovered más abajo);
        # si empezara visible duplicaría la leyenda y dejaría muy poco sitio para la tarta
        slice_.setLabelVisible(False)
        slice_.setLabelPosition(QPieSlice.LabelOutside)
        slice_.hovered.connect(lambda state, s=slice_: (
            s.setExploded(state),
            s.setLabelVisible(state)
        ))
    
    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(titulo)
    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.legend().setVisible(True)
    chart.legend().setAlignment(Qt.AlignRight)
    
    chart_view = QChartView(chart)
    chart_view.setRenderHint(QPainter.Antialiasing)
    
    return chart_view