"""Newton-Raphson aplicado a optimización. Ver docs/metodos/newton_raphson.md.

La entrada es la función original f(x). El método calcula f'(x) y f''(x)
y resuelve f'(x) = 0 usando:
    x_{k+1} = x_k - f'(x_k) / f''(x_k)
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


class NewtonRoots:
    """Búsqueda de puntos críticos (f'(x)=0) mediante Newton-Raphson."""
    def __init__(self, func_str, x0, tol=1e-5, max_iter=150):
        self.func_str = func_str
        self.x0 = float(x0)
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
            ddf = sp.lambdify(x, ddf_expr, "numpy")
        except Exception as e:
            return {
                "success": False,
                "solution": None,
                "steps": [],
                "error_message": f"Error de sintaxis en la función original f(x): {str(e)}"
            }

        expr_info = {
            "original_expr": str(original_expr),
            "derivative_expr": str(df_expr),
            "second_derivative_expr": str(ddf_expr),
        }

        x_current = self.x0
        iter_count = 0
        error = float("inf")

        try:
            while iter_count < self.max_iter:
                fp_val = df(x_current)
                fpp_val = ddf(x_current)

                # BLINDAJE CONTRA INDETERMINACIONES (NaN, Inf, Complejos)
                if (np.isnan(fp_val) or np.isnan(fpp_val)
                        or np.isinf(fp_val) or np.isinf(fpp_val)
                        or isinstance(fp_val, complex)
                        or isinstance(fpp_val, complex)):
                    raise TypeError(
                        "La primera o la segunda derivada no están definidas "
                        "matemáticamente en este punto (resultado no real, "
                        "NaN o infinito)."
                    )

                fp = float(fp_val)
                fpp = float(fpp_val)

                self.history.append({
                    "iter": iter_count,
                    "x": x_current,
                    "fx": fp,
                    "error": error if iter_count > 0 else None
                })

                if abs(fp) <= self.tol:
                    break

                if fpp == 0:
                    return {
                        "success": False,
                        "solution": None,
                        "steps": self.history,
                        "error_message": (
                            f"La segunda derivada f''(x) se hizo cero en "
                            f"x = {x_current:.6f}. El método falla "
                            f"(división por cero)."
                        )
                    }

                x_new = x_current - (fp / fpp)

                if x_new != 0:
                    error = abs((x_new - x_current) / x_new) * 100
                else:
                    error = abs(x_new - x_current)

                x_current = x_new
                iter_count += 1

                if error <= self.tol:
                    fp_final = evaluate_expression(df_expr, x_current)
                    if fp_final is None:
                        raise TypeError(
                            "El punto de convergencia final cayó en una zona "
                            "indefinida de la primera derivada."
                        )

                    self.history.append({
                        "iter": iter_count,
                        "x": x_current,
                        "fx": fp_final,
                        "error": error
                    })
                    break

            derivative_value = evaluate_expression(df_expr, x_current)
            original_value = evaluate_expression(original_expr, x_current)
            if iter_count < self.max_iter or error <= self.tol:
                msg = (
                    f"Converge por error aceptable. Punto crítico: "
                    f"{x_current:.6f} (f'(x) = {derivative_value:.2e})"
                )
            else:
                msg = (
                    f"Alcanzó el máximo de {self.max_iter} iteraciones sin "
                    f"converger. Mejor aproximación: {x_current:.6f}"
                )

            classification = classify_critical_point(
                df_expr, x_current, second_expr=ddf_expr)
            return {
                "success": True,
                "solution": x_current,
                "steps": self.history,
                "message": msg,
                "error_message": None,
                "original_value": original_value,
                "derivative_value": derivative_value,
                **expr_info,
                **classification,
            }

        except OverflowError:
            return {
                "success": False,
                "solution": None,
                "steps": self.history,
                "error_message": (
                    f"Desbordamiento matemático en iteración {iter_count}.\n"
                    f"Los valores crecieron al infinito (divergencia)."
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
                    f"Error matemático inesperado en iteración "
                    f"{iter_count}:\n{str(e)}"
                )
            }
