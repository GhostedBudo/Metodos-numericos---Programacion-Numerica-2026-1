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


def build_function_spec(func_str):
    """Calcula f(x), f'(x) y f''(x) a partir de la función original.

    Devuelve un diccionario con las expresiones simbólicas y sus textos.
    """
    x = sp.Symbol("x")
    original = parse_expression(func_str)
    derivative = sp.diff(original, x)
    second_derivative = sp.diff(derivative, x)
    return {
        "original": original,
        "derivative": derivative,
        "second_derivative": second_derivative,
        "original_str": str(original),
        "derivative_str": str(derivative),
        "second_derivative_str": str(second_derivative),
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
