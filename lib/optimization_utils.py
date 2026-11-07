"""Utilidades para optimización univariada.

En optimización no se buscan raíces de f(x), sino puntos críticos:
valores x* donde la primera derivada se anula, es decir f'(x*) = 0.

Por eso los métodos de bisección, Newton y secante reciben como entrada
la primera derivada g(x) = f'(x). La segunda derivada g'(x) = f''(x)
sirve para clasificar el punto crítico como mínimo o máximo.
"""
import re

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


def classify_critical_point(deriv_expr, x_value, tol=1e-8):
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
        second_expr = sp.diff(deriv_expr, x)
        second_val = float(sp.N(second_expr.subs(x, x_value)))
    except Exception:
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

    La constante no cambia la ubicación de los puntos críticos.
    Devuelve None si sympy no puede integrar la expresión.
    """
    x = sp.Symbol("x")
    try:
        return sp.integrate(deriv_expr, x)
    except Exception:
        return None
