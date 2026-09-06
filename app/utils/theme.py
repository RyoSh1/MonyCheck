import os

_STYLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles")


def cargar_hoja_estilos(oscuro):
    """Combina las reglas estructurales comunes con los colores del tema activo"""
    archivos = ["base.css", "dark.css" if oscuro else "light.css"]
    hojas = []
    for nombre in archivos:
        try:
            with open(os.path.join(_STYLES_DIR, nombre), "r") as f:
                hojas.append(f.read())
        except OSError:
            print(f"No se pudo cargar el archivo CSS: {nombre}")
    return "\n".join(hojas)
