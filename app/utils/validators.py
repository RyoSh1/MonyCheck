from PyQt5.QtGui import QDoubleValidator


class DecimalValidator(QDoubleValidator):
    """Valida importes aceptando tanto coma como punto decimal"""
    def validate(self, input_str, pos):
        normalized = input_str.replace(',', '.')
        state, _, _ = super().validate(normalized, pos)
        return (state, input_str, pos)


def parse_monto(texto):
    """Convierte un importe introducido por el usuario (25,99 o 25.99) a float"""
    return float(texto.strip().replace(',', '.'))
