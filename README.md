# GastoCheck


## Run and build

Run commands from the repository root because the application uses relative
paths for database discovery and CSS loading.

```bash
python -m pip install -r requirements.txt
python main.py
```

The dependencies are pinned in `requirements.txt`: PyQt5 5.15.7 and
PyInstaller 5.6.2. Build a windowed one-file executable with:

```bash
python build.py
```

`build.py` removes `build/` and `dist/` before invoking PyInstaller. The
executable is inside `dist/` directory.
