"""Newton-Raphson aplicado a optimización. Ver docs/metodos/newton_raphson.md.

La entrada es f(x) o f'(x), según ``input_type``. Si se recibe f(x), el
método calcula f'(x) y f''(x); si se recibe f'(x), calcula f''(x). Resuelve
f'(x) = 0 usando:
    x_{k+1} = x_k - f'(x_k) / f''(x_k)
"""
import numpy as np
import sympy as sp

from lib.optimization_utils import (
    build_function_spec,
    classify_critical_point,
    evaluate_expression,
)


def _parse_expression(func_str):
    """Compatibilidad: usa el parser común de optimización."""
    return parse_expression(func_str)


class NewtonRoots:
    """Búsqueda de puntos críticos (f'(x)=0) mediante Newton-Raphson."""
    def __init__(self, func_str, x0, tol=1e-5, max_iter=150,
                 input_type="function"):
        self.func_str = func_str
        self.x0 = float(x0)
        self.tol = float(tol)
        self.max_iter = int(max_iter)
        self.input_type = input_type
        self.history = []

    def solve(self):
        self.history = []
        x = sp.Symbol("x")

        try:
            spec = build_function_spec(
                self.func_str, input_type=self.input_type)
            original_expr = spec["original"]
            df_expr = spec["derivative"]
            ddf_expr = spec["second_derivative"]
            df = sp.lambdify(x, df_expr, "numpy")
            ddf = sp.lambdify(x, ddf_expr, "numpy")
        except Exception as e:
            return {
                "success": False,
                "solution": None,
                "steps": [],
                "error_message": (
                    "Error de sintaxis en la entrada. Use '*' para "
                    f"multiplicar y revise el tipo seleccionado: {str(e)}"
                )
            }

        expr_info = {
            "original_expr": spec["original_str"],
            "derivative_expr": spec["derivative_str"],
            "second_derivative_expr": spec["second_derivative_str"],
            "input_type": spec["input_type"],
            "original_is_antiderivative": spec["original_is_antiderivative"],
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
