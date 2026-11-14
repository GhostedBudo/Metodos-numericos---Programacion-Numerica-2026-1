# AGENTS.md

## Setup & Run

Windows PowerShell (this machine):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Versión web móvil (Flask):

```powershell
.\.venv\Scripts\python.exe -m webapp.app
```

Abrir `http://localhost:5000`. Para celular, usar la IP local de la PC
en la misma red Wi-Fi y permitir el firewall de Windows.

Linux/macOS/Git Bash:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Tests:

```powershell
.\.venv\Scripts\python.exe -m lib.bisection_method_test
.\.venv\Scripts\python.exe -m lib.newton_raphson_test
.\.venv\Scripts\python.exe -m lib.secante_test
```

No linter, no type checker, no CI. Verify changes by running those tests
and by launching the GUI.

## Optimización univariada

Las vistas de Bisección, Newton y Secante reciben la función original
`f(x)`. `lib/optimization_utils.py` calcula `f'(x)` y `f''(x)`, centraliza
el parseo y clasifica el punto crítico con `f''(x*)` (mínimo, máximo o
inconcluso). Los solvers resuelven `f'(x)=0`.

Los resultados y la API incluyen `original_expr`, `derivative_expr`,
`second_derivative_expr`, `original_value` y `derivative_value`.
En las gráficas hay selector **Ambas / f(x) / f'(x)**: 2D usa doble eje Y
cuando se muestran ambas curvas; 3D usa dos superficies separadas.

## Architecture

Feature-oriented layout. Each active method is a self-contained folder under `gui/`.

```
main.py                       ← entrypoint (imports GaussSimpleApp)
lib/                          ← pure math implementations (no UI deps)
  optimization_utils.py       ← parseo, f'(x), f''(x), clasificación
  bisection_method.py
  newton_raphson.py
  secante.py
gui/
  app.py                      ← main window + routing de las 3 vistas
  glossary.py                 ← glosario compartido por las 3 vistas
  theme.py                    ← design tokens (light/dark tuples)
  components/
    sidebar.py                ← solo Bisección, Newton, Secante
  bisection_method/
    bisection_method_view.py
  newton_raphson/
    newton_rapshon_view.py
  secante/
    secante_view.py
webapp/
  app.py                      ← Flask + API /api/solve
  templates/index.html        ← interfaz responsive móvil
  static/styles.css
  static/app.js               ← Plotly 2D/3D, curvas duales, tabla, pasos
```

Los archivos de métodos anteriores pueden seguir en disco, pero no se
importan ni aparecen en la interfaz.

## Adding a New Numerical Method

1. Create `lib/<method>.py` with a class matching the existing solvers:
   constructor takes inputs, `solve()` returns
   `{"success": bool, "solution": ..., "steps": [...], "error_message": ...}`
2. Create `gui/<method>/<method>_view.py` as a `CTkFrame` subclass following
   one of the three existing views.
3. Register in `gui/app.py`: import the view, add a case to `switch_to_view()`,
   add a sidebar button in `gui/components/sidebar.py`.
4. Keep the step-by-step tab: show formula, substitutions, error, and decision.
5. Keep a separate **Tabla** tab with a monospace iteration table and a
   legend explaining `xl`, `xu`, `xr`, `fp`, `fpp`, and `ea`.
6. Keep the graph legend and a **Glosario** tab explaining symbols,
   classification, table abbreviations, and how to read the graph.
7. Keep the graph's **2D / 3D** switch in both the desktop and web versions.
8. Keep the **Ambas / f(x) / f'(x)** curve selector. In 2D use a twin Y axis
   for Ambas; in 3D use two separated surfaces.
9. All UI text, comments, and docstrings in Spanish.

## Dependencies

`requirements.txt`: customtkinter, numpy, pandas, matplotlib, sympy, Flask.
Flask is used by `webapp/`. Plotly se sirve localmente desde
`webapp/static/plotly.min.js`, así que la versión web funciona sin internet.

## Style

- Cada directorio (`lib/`, `gui/`, `gui/components/`, `gui/<method>/`) lleva `__init__.py` vacío (solo docstring) para que los imports absolutos `from lib.X import Y` funcionen via `python -m`. En Windows los tests se ejecutan con `.\.venv\Scripts\python.exe -m <modulo>` desde la raíz.
- All UI strings, comments, and docstrings in Spanish
- Colors defined as `(light_hex, dark_hex)` tuples in `theme.py`; use `ctk` appearance mode to switch
- Fonts: Outfit (titles/sections), Inter (labels/UI), Consolas (monospace/code output)
- `#pyright: ignore` on all customtkinter imports (known type stub issues)
