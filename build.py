import PyInstaller.__main__
import platform
import shutil
import os

def build_app():
    system = platform.system().lower()
    
    # Configuración común
    app_name = "MonyCheck"
    entry_point = "main.py"
    additional_files = []
    
    # Configuración específica por sistema operativo
    if system == "windows":
        icon = "app/resources/icon.ico"
    else:  # linux
        icon = "app/resources/icon.png"
    
    # Directorio de construcción
    build_dir = "build"
    dist_dir = "dist"
    
    # Limpiar builds anteriores
    for directory in [build_dir, dist_dir]:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    
    # Argumentos de PyInstaller
    pyinstaller_args = [
        entry_point,
        f"--name={app_name}",
        f"--icon={icon}",
        "--windowed",  # Para aplicación sin consola
        "--noconfirm",
        "--clean",
        "--onefile",  # Para crear un solo ejecutable
        # "--onedir",  # Alternativa: crea una carpeta con todos los archivos
        f"--add-data=app{os.pathsep}app",  # Incluir la carpeta app
        "--exclude-module=tkinter",
        "--exclude-module=test",
        "--exclude-module=unittest"
    ]
    
    # Ejecutar PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)
    
    print(f"\nBuild completado! El ejecutable está en: {dist_dir}")

if __name__ == "__main__":
    build_app()