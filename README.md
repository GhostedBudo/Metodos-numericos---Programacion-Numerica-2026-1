# Métodos Numéricos — Programación Numérica 2026-1

Implementación de métodos numéricos con interfaz gráfica moderna en Python
usando **CustomTkinter** (modos Claro/Oscuro) y **Matplotlib** para gráficas.

## Instalación y ejecución

### Windows (PowerShell)

```powershell
# 1. Entrar a la carpeta del proyecto
cd "D:\BACKUP\UCLA UNIVERSIDAD\10MO SEMESTRE\Optimización\I\Metodos-numericos---Programacion-Numerica-2026-1"

# 2. Entorno virtual + dependencias
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Ejecutar la aplicación
.\.venv\Scripts\python.exe main.py
```

> En Windows el intérprete está en `.venv\Scripts\python.exe`.
> La ruta `.venv/bin/python` es de Linux/macOS y por eso PowerShell
> respondía "no se reconoce como nombre de un cmdlet".

### Linux / macOS / Git Bash

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

## Versión web móvil

La carpeta `webapp/` contiene una versión web responsive para usar desde
el navegador del celular. Incluye glosario, tabla de iteraciones y
alternancia de gráfica **2D / 3D**. Plotly se sirve localmente, así que
las gráficas funcionan sin conexión a internet.

```powershell
# En la PC, desde la raíz del proyecto
.\.venv\Scripts\python.exe -m webapp.app
```

Abrir en la PC: `http://localhost:5000`

Desde el celular, conectado a la misma red Wi-Fi:

1. Obtener la IP local de la PC con `ipconfig` (buscar IPv4).
2. Abrir `http://IP_DE_LA_PC:5000` en el navegador del celular.
3. Si Windows pregunta, permitir el acceso a la red privada.

## Deploy en VPS con Coolify

El proyecto ya incluye `Dockerfile` y `.dockerignore`. La imagen usa
Gunicorn y expone el puerto `8000`.

1. Hacer commit y push de los cambios a `origin/main`.
2. Entrar a Coolify: `http://IP_DEL_VPS:8000` (en este VPS ya está
   corriendo Coolify 4.6.0).
3. Crear un proyecto y agregar un recurso desde el repositorio de GitHub.
4. Configurar:
   - Branch: `main`
   - Build Pack: `Dockerfile`
   - Base Directory: `/`
   - Dockerfile: `/Dockerfile`
   - Puerto expuesto: `8000`
5. Asignar un dominio, por ejemplo `optimizacion.amoreno.online`, y
   crear el registro DNS tipo `A` apuntando a la IP del VPS.
6. Activar HTTPS con Let's Encrypt y desplegar.

No se necesitan variables de entorno ni base de datos. El contenedor
sirve la versión web móvil en `/` y la API en `/api/solve`.

## Optimización univariada (f'(x) = 0)

Las vistas de **Bisección**, **Newton** y **Secante** trabajan ahora en
modo optimización: en vez de pedir `f(x)`, piden la **primera derivada
`f'(x)`**. El programa resuelve `f'(x) = 0` para encontrar puntos
críticos `x*` y usa `f''(x*)` para clasificarlos:

- `f''(x*) > 0` → mínimo local.
- `f''(x*) < 0` → máximo local.
- `f''(x*) ≈ 0` → criterio inconcluso.

Newton calcula automáticamente `f''(x)` a partir de la `f'(x)` que
escribas, porque su fórmula es
`x(k+1) = x(k) - f'(x(k)) / f''(x(k))`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m lib.bisection_method_test
.\.venv\Scripts\python.exe -m lib.newton_raphson_test
.\.venv\Scripts\python.exe -m lib.secante_test
```

## Estructura relevante

```
main.py                          ← entrypoint
lib/
├── optimization_utils.py        ← parseo + clasificación f''(x*)
├── bisection_method.py
├── newton_raphson.py
└── secante.py
gui/
├── app.py                       ← arranca en Bisección
├── glossary.py                  ← glosario compartido
├── theme.py
├── components/sidebar.py        ← solo 3 botones
├── bisection_method/
├── newton_raphson/
└── secante/
webapp/
├── app.py                       ← Flask + API de cálculo
├── templates/index.html         ← interfaz móvil
└── static/                      ← CSS + JS + Plotly 2D/3D
```

La app solo carga las tres vistas de optimización. Los archivos de
métodos anteriores siguen en disco, pero ya no aparecen en el menú ni
se importan al arrancar.

## Métodos implementados

| Método | Entrada | Autor |
|--------|---------|-------|
| Bisección | `f'(x)` | Raimir Linarez |
| Newton | `f'(x)` | Carlos Paradas |
| Secante | `f'(x)` | Carlos Paradas |

## Cómo agregar un nuevo método numérico

### 1. Crear la clase de lógica (`lib/<metodo>.py`)

El constructor recibe los parámetros del método y `solve()` retorna
un diccionario estándar:

```python
class MiMetodo:
    def __init__(self, parametros...):
        self.steps = []   # paso a paso para la GUI

    def solve(self):
        # Validaciones...
        # Algoritmo...
        return {
            "success": bool,
            "solution": ...,          # resultado (depende del método)
            "steps": self.steps,      # lista de dicts con type + description
            "error_message": str | None
        }
```

Ver `lib/bisection_method.py`, `lib/newton_raphson.py` o
`lib/secante.py` como referencia.

### 2. Crear tests (`lib/<metodo>_test.py`)

Ejecutar con:
```powershell
.\.venv\Scripts\python.exe -m lib.<metodo>_test
```

### 3. Crear la vista GUI (`gui/<metodo>/`)

La vista es un `CTkFrame` que sigue el patrón de las tres vistas actuales:
- `gui/<metodo>/__init__.py` con docstring descriptivo
- `gui/<metodo>/<metodo>_view.py` con:
  - Sidebar (`Sidebar(self, active_method="<metodo>")`)
  - `view_container` con header y dos paneles (inputs izq, resultados der)
  - `CTkTabview` con tabs (Resultado, Paso a Paso, Gráfica si aplica)
  - Método `solve_*()` que instancia la clase de `lib/`, procesa `result["steps"]` y actualiza los textboxes y gráficas
  - En **Paso a Paso** debe mostrarse la fórmula, la sustitución numérica, el error y la decisión de cada iteración

### 4. Registrar la vista

En **`gui/app.py`**:
```python
from gui.<metodo>.<metodo>_view import MiMetodoView

def switch_to_view(self, view_name):
    # ...
    elif view_name == "<metodo>":
        if isinstance(self.current_view, MiMetodoView): return
        self.current_view.destroy()
        self.current_view = MiMetodoView(self.main_container)
        self.current_view.grid(row=0, column=0, sticky="nsew")
```

En **`gui/components/sidebar.py`**:
```python
self.btn_<metodo> = ctk.CTkButton(
    self, text="      📐   Mi Método",
    command=self.on_<metodo>_click, ...
)

def on_<metodo>_click(self):
    if self.active_method == "<metodo>": return
    app = self.winfo_toplevel()
    if hasattr(app, "switch_to_view"):
        app.switch_to_view("<metodo>")
```

### 5. Probar

```powershell
.\.venv\Scripts\python.exe main.py
```

## Dependencias

`requirements.txt`: customtkinter, numpy, pandas, matplotlib, sympy

## Estilo

- UI, comentarios y docstrings en **español**
- Cada directorio (`lib/`, `gui/`, `gui/components/`, `gui/<metodo>/`) tiene `__init__.py`
- Tipografías: Outfit (títulos), Inter (labels), Consolas (código monoespaciado)
- Colores en `gui/theme.py` como tuplas `(claro, oscuro)`
- `#pyright: ignore` en imports de customtkinter (problemas conocidos de type stubs)
