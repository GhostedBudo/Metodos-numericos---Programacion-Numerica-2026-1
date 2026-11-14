"""Método de la Secante aplicado a optimización. Ver docs/metodos/secante.md.

La entrada es la función original f(x). El método calcula f'(x) y resuelve
f'(x) = 0 sin calcular f''(x) en las iteraciones:
    x_{k+1} = x_k - f'(x_k) * (x_k - x_{k-1}) / (f'(x_k) - f'(x_{k-1}))
"""
import numpy as np
import sympy as sp

from lib.optimization_utils import (
    classify_critical_point,
    evaluate_expression,
    parse_expression,
)


def _parse_expression(func_str):
    """Compatibilidad: usa el parser común de optimización."""
    return parse_expression(func_str)


class SecantRoots:
    """Búsqueda de puntos críticos (f'(x)=0) mediante la Secante."""
    def __init__(self, func_str, x0, x1, tol=1e-5, max_iter=150):
        self.func_str = func_str
        self.x0 = float(x0)
        self.x1 = float(x1)
        self.tol = float(tol)
        self.max_iter = int(max_iter)
        self.history = []

    def solve(self):
        self.history = []
        x = sp.Symbol("x")

        try:
            original_expr = _parse_expression(self.func_str)
            df_expr = sp.diff(original_expr, x)
            ddf_expr = sp.diff(df_expr, x)
            df = sp.lambdify(x, df_expr, "numpy")
        except Exception as e:
            err_msg = str(e)
            if "could not parse" in err_msg:
                msg = (
                    "Error de sintaxis en la función original. Asegúrese de "
                    "usar '*' para multiplicaciones (ej. '2*x' en lugar de '2x')."
                )
            else:
                msg = f"Error al procesar la función original f(x): {err_msg}"
            return {
                "success": False,
                "solution": None,
                "steps": [],
                "error_message": msg,
            }

        expr_info = {
            "original_expr": str(original_expr),
            "derivative_expr": str(df_expr),
            "second_derivative_expr": str(ddf_expr),
        }

        x_prev = self.x0
        x_curr = self.x1
        iter_count = 0
        error = float("inf")

        try:
            fx_prev_val = df(x_prev)
            fx_curr_val = df(x_curr)

            # VALIDACIÓN DE INDETERMINACIONES EN PUNTOS INICIALES
            if (np.isnan(fx_prev_val) or np.isnan(fx_curr_val)
                    or np.isinf(fx_prev_val) or np.isinf(fx_curr_val)
                    or isinstance(fx_prev_val, complex)
                    or isinstance(fx_curr_val, complex)):
                raise TypeError(
                    "Uno o ambos puntos iniciales (x0 o x1) no pertenecen "
                    "al dominio real de la primera derivada."
                )

            fx_prev = float(fx_prev_val)
            fx_curr = float(fx_curr_val)

            self.history.append({
                "iter": 0,
                "x": x_prev,
                "fx": fx_prev,
                "error": None
            })

            while iter_count < self.max_iter:
                iter_count += 1

                self.history.append({
                    "iter": iter_count,
                    "x": x_curr,
                    "fx": fx_curr,
                    "error": error if iter_count > 1 else None
                })

                if abs(fx_curr) <= self.tol:
                    break

                if (fx_curr - fx_prev) == 0:
                    return {
                        "success": False,
                        "solution": None,
                        "steps": self.history,
                        "error_message": (
                            f"División por cero en iteración {iter_count}. "
                            f"f'(x_curr) y f'(x_prev) son idénticos."
                        )
                    }

                x_next = (
                    x_curr
                    - (fx_curr * (x_curr - x_prev)) / (fx_curr - fx_prev)
                )

                if x_next != 0:
                    error = abs((x_next - x_curr) / x_next) * 100
                else:
                    error = abs(x_next - x_curr)

                x_prev = x_curr
                fx_prev = fx_curr
                x_curr = x_next

                fx_curr_val = df(x_curr)

                # VALIDACIÓN CONTINUA DE INDETERMINACIONES
                if (np.isnan(fx_curr_val) or np.isinf(fx_curr_val)
                        or isinstance(fx_curr_val, complex)):
                    raise TypeError(
                        "El método divergió o saltó hacia un punto fuera del "
                        "dominio real de la primera derivada."
                    )

                fx_curr = float(fx_curr_val)

                if error <= self.tol:
                    iter_count += 1
                    self.history.append({
                        "iter": iter_count,
                        "x": x_curr,
                        "fx": fx_curr,
                        "error": error
                    })
                    break

            derivative_value = evaluate_expression(df_expr, x_curr)
            original_value = evaluate_expression(original_expr, x_curr)
            if iter_count < self.max_iter or error <= self.tol:
                msg = (
                    f"Converge por error aceptable. Punto crítico: "
                    f"{x_curr:.6f} (f'(x) = {fx_curr:.2e})"
                )
            else:
                msg = (
                    f"Alcanzó el máximo de {self.max_iter} iteraciones sin "
                    f"converger. Mejor aproximación: {x_curr:.6f}"
                )

            classification = classify_critical_point(
                df_expr, x_curr, second_expr=ddf_expr)
            return {
                "success": True,
                "solution": x_curr,
                "steps": self.history,
                "message": msg,
                "error_message": None,
                "original_value": original_value,
                "derivative_value": derivative_value,
                **expr_info,
                **classification,
            }

        except NameError:
            return {
                "success": False,
                "solution": None,
                "steps": self.history,
                "error_message": (
                    "Función no reconocida o mal declarada.\nRecuerde usar "
                    "la sintaxis matemática internacional estándar:\n"
                    "sin(x), cos(x), tan(x), exp(x), log(x)."
                )
            }
        except OverflowError:
            return {
                "success": False,
                "solution": None,
                "steps": self.history,
                "error_message": (
                    f"Desbordamiento matemático en iteración {iter_count}.\n"
                    f"Los puntos divergieron con valores que tienden al infinito."
                )
            }
        except TypeError as e:
            return {
                "success": False,
                "solution": None,
                "steps": self.history,
                "error_message": f"Error de dominio en iteración {iter_count}.\n{str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "solution": None,
                "steps": self.history,
                "error_message": (
                    f"Error imprevisto en la ejecución (iteración "
                    f"{iter_count}):\n{str(e)}"
                )
            }
