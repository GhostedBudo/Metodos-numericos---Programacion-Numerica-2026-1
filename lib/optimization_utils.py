"""Utilidades para optimización univariada.

La entrada del usuario es la función original f(x). A partir de ella se
calculan simbólicamente la primera derivada f'(x) y la segunda derivada
f''(x). Los métodos de bisección, Newton y secante resuelven f'(x) = 0
para encontrar puntos críticos. La segunda derivada sirve para clasificar
el punto crítico como mínimo o máximo.
"""
import math
import re

import numpy as np
import sympy as sp


def parse_expression(expr_str):
    """Convierte un texto matemático en una expresión simbólica de sympy.

    Acepta notación común en español: sen(x), ln(x), e, ^ para potencias.
    """
    if expr_str is None:
        raise ValueError("La expresión está vacía.")

    cleaned = str(expr_str).strip()
    if cleaned == "":
        raise ValueError("La expresión está vacía.")

    cleaned = cleaned.replace("sen(", "sin(")
    cleaned = cleaned.replace("ln(", "log(")
    cleaned = re.sub(r"(?<![A-Za-z0-9_])e(?![A-Za-z0-9_])", "E", cleaned)
    cleaned = cleaned.replace("^", "**")

    return sp.sympify(
        cleaned,
        locals={
            "E": sp.E,
            "pi": sp.pi,
            "sin": sp.sin,
            "cos": sp.cos,
            "tan": sp.tan,
            "exp": sp.exp,
            "log": sp.log,
            "sqrt": sp.sqrt,
            "Abs": sp.Abs,
        },
    )


def normalize_input_type(input_type):
    """Normaliza el tipo de entrada: ``function`` o ``derivative``."""
    value = str(input_type or "function").strip().lower()
    if value in {"function", "f", "fx", "f(x)", "original", "funcion", "función"}:
        return "function"
    if value in {
        "derivative", "f'", "f'(x)", "fprime", "f_prima", "derivada",
    }:
        return "derivative"
    raise ValueError(
        "Tipo de entrada inválido. Use 'function' (f(x)) o "
        "'derivative' (f'(x))."
    )


def build_function_spec(func_str, input_type="function"):
    """Construye f(x), f'(x) y f''(x) según el tipo de entrada.

    Si ``input_type`` es ``function``, el usuario escribe f(x) y las
    derivadas se calculan simbólicamente. Si es ``derivative``, el usuario
    escribe f'(x); la segunda derivada se calcula y f(x) se reconstruye
    integrando con constante de integración 0 (solo para visualización).
    """
    x = sp.Symbol("x")
    kind = normalize_input_type(input_type)
    entry = parse_expression(func_str)

    if kind == "derivative":
        derivative = entry
        second_derivative = sp.diff(derivative, x)
        try:
            original = sp.integrate(derivative, x)
            if original.has(sp.Integral):
                original = None
        except Exception:
            original = None
        original_is_antiderivative = original is not None
    else:
        original = entry
        derivative = sp.diff(original, x)
        second_derivative = sp.diff(derivative, x)
        original_is_antiderivative = False

    return {
        "input_type": kind,
        "original": original,
        "derivative": derivative,
        "second_derivative": second_derivative,
        "original_str": (
            str(original) if original is not None else "no disponible"
        ),
        "derivative_str": str(derivative),
        "second_derivative_str": str(second_derivative),
        "original_is_antiderivative": original_is_antiderivative,
    }


def evaluate_expression(expr, value):
    """Evalúa una expresión simbólica en un punto y devuelve float o None."""
    x = sp.Symbol("x")
    try:
        result = complex(sp.N(expr.subs(x, value)))
    except Exception:
        return None
    if abs(result.imag) > 1e-9 or not math.isfinite(result.real):
        return None
    return float(result.real)


def evaluate_curve(expr, lo, hi, points=320):
    """Genera puntos (x, y) reales para una expresión simbólica.

    Los valores complejos, infinitos o indefinidos se convierten en NaN
    para que matplotlib/Plotly simplemente interrumpan la curva.
    """
    x = sp.Symbol("x")
    try:
        fn = sp.lambdify(x, expr, "numpy")
        xs = np.linspace(float(lo), float(hi), int(points))
        with np.errstate(all="ignore"):
            ys = fn(xs)
        if np.isscalar(ys):
            ys = np.full(xs.shape, ys)
        ys = np.asarray(ys).ravel()
        if ys.size != xs.size:
            value = ys.flat[0] if ys.size else np.nan
            ys = np.full(xs.shape, value)
        if np.iscomplexobj(ys):
            ys = np.where(np.abs(ys.imag) <= 1e-9, ys.real, np.nan)
        return xs, np.asarray(ys, dtype=float)
    except Exception:
        return np.array([]), np.array([])


def classify_critical_point(deriv_expr, x_value, tol=1e-8, second_expr=None):
    """Clasifica x* usando el criterio de la segunda derivada.

    Recibe la primera derivada f'(x) y el punto crítico x*.
    Calcula f''(x*) y devuelve un diccionario con:
      - second_derivative: valor numérico de f''(x*) o None
      - second_derivative_expr: expresión simbólica de f''(x)
      - critical_type: "mínimo", "máximo" o "inconcluso"
      - classification: explicación corta en español
    """
    x = sp.Symbol("x")

    try:
        if second_expr is None:
            second_expr = sp.diff(deriv_expr, x)
        second_val = evaluate_expression(second_expr, x_value)
    except Exception:
        second_val = None

    if second_val is None:
        return {
            "second_derivative": None,
            "second_derivative_expr": None,
            "critical_type": "inconcluso",
            "classification": "No se pudo evaluar f''(x*) para clasificar el punto.",
        }

    if abs(second_val) <= tol:
        critical_type = "inconcluso"
        message = (
            "f''(x*) ≈ 0: el criterio de la segunda derivada no decide. "
            "Hay que usar derivadas de orden superior o analizar el signo de f'."
        )
    elif second_val > 0:
        critical_type = "mínimo"
        message = (
            "f''(x*) > 0: la función es cóncava hacia arriba, "
            "por lo tanto x* es un mínimo local."
        )
    else:
        critical_type = "máximo"
        message = (
            "f''(x*) < 0: la función es cóncava hacia abajo, "
            "por lo tanto x* es un máximo local."
        )

    return {
        "second_derivative": second_val,
        "second_derivative_expr": str(second_expr),
        "critical_type": critical_type,
        "classification": message,
    }


def visible_y_range(values, margin_ratio=0.08):
    """Rango y visible a partir de una lista de valores (ignora None/NaN/inf).

    Devuelve (lo, hi) con un margen relativo, o None si no hay datos útiles.
    Se usa para recortar las rectas auxiliares (tangente/secante) al área
    visible de la gráfica.
    """
    ys = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            ys.append(number)
    if len(ys) < 2:
        return None
    lo, hi = min(ys), max(ys)
    margin = (hi - lo) * margin_ratio
    if margin <= 0:
        margin = max(abs(lo), abs(hi), 1.0) * 0.1
    return lo - margin, hi + margin


def clipped_segment(anchor_x, anchor_y, slope, x_half, y_range):
    """Segmento de la recta y = anchor_y + slope*(x - anchor_x).

    Se extiende ±x_half alrededor de anchor_x y se recorta a y_range para
    que no dispare la escala del eje y. Devuelve [x0, y0, x1, y1] o None.
    """
    try:
        anchor_x = float(anchor_x)
        anchor_y = float(anchor_y)
        slope = float(slope)
        x_half = float(x_half)
    except (TypeError, ValueError):
        return None
    if y_range is None or x_half <= 0:
        return None
    if not all(math.isfinite(v) for v in (anchor_x, anchor_y, slope)):
        return None
    x0, x1 = anchor_x - x_half, anchor_x + x_half
    y0, y1 = anchor_y - slope * x_half, anchor_y + slope * x_half
    dy = y1 - y0
    lo, hi = y_range
    t0, t1 = 0.0, 1.0
    if abs(dy) > 1e-12:
        ta, tb = (lo - y0) / dy, (hi - y0) / dy
        t_in, t_out = (ta, tb) if ta < tb else (tb, ta)
        t0, t1 = max(t0, t_in), min(t1, t_out)
    elif not (lo <= y0 <= hi):
        return None
    if t0 >= t1:
        return None
    return [
        x0 + t0 * (x1 - x0), y0 + t0 * dy,
        x0 + t1 * (x1 - x0), y0 + t1 * dy,
    ]


def reconstruct_function(deriv_expr):
    """Reconstruye f(x) integrando f'(x), tomando la constante de integración 0.

    Se conserva por compatibilidad. La aplicación ya recibe f(x) directamente.
    Devuelve None si sympy no puede integrar la expresión.
    """
    x = sp.Symbol("x")
    try:
        return sp.integrate(deriv_expr, x)
    except Exception:
        return None
