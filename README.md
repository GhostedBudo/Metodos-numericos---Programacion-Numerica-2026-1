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
el navegador del celular. Permite elegir el tipo de entrada **f(x) / f'(x)**,
incluye glosario, tabla de iteraciones, alternancia de gráfica **2D / 3D**
y selector de curva **Ambas / f(x) / f'(x)**. Plotly se sirve localmente,
así que las gráficas funcionan sin conexión a internet.

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

1. Hacer commit y push de los cambios al remoto configurado (`fork/main`
   en este entorno).
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

Las vistas de **Bisección**, **Newton** y **Secante** permiten elegir el
tipo de entrada:

- **f(x)**: el programa calcula automáticamente `f'(x)` y `f''(x)`.
- **f'(x)**: el programa usa la derivada dada, calcula `f''(x)` e integra
  `F(x)` con constante `C=0` para poder graficarla.

En ambos casos se resuelve `f'(x) = 0` para encontrar puntos críticos `x*`
y se usa `f''(x*)` para clasificarlos:

- `f''(x*) > 0` → mínimo local.
- `f''(x*) < 0` → máximo local.
- `f''(x*) ≈ 0` → criterio inconcluso.

Newton usa `x(k+1) = x(k) - f'(x(k)) / f''(x(k))`, donde las derivadas se
obtienen simbólicamente según el tipo de entrada.

En la gráfica se pueden mostrar **ambas curvas** (`f(x)` o `F(x)` en verde
y `f'(x)` en azul) o una sola con el selector **Ambas / f(x) / f'(x)**.
En 2D con Ambas se usa doble eje Y; en 3D se dibujan dos superficies
separadas.

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
├── optimization_utils.py        ← parseo, f'(x), f''(x), clasificación
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
└── static/                      ← CSS + JS + Plotly 2D/3D y curvas duales
```

La app solo carga las tres vistas de optimización. Los archivos de
métodos anteriores siguen en disco, pero ya no aparecen en el menú ni
se importan al arrancar.

## Métodos implementados

| Método | Entrada | Autor |
|--------|---------|-------|
| Bisección | `f(x)` o `f'(x)` | Raimir Linarez |
| Newton | `f(x)` o `f'(x)` | Carlos Paradas |
| Secante | `f(x)` o `f'(x)` | Carlos Paradas |

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
