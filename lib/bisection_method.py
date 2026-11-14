"""Método de Bisección aplicado a optimización. Ver docs/metodos/bisection.md.

La entrada es la función original f(x). El método calcula f'(x) y resuelve
f'(x) = 0. Dado [xl, xu] con f'(xl)*f'(xu) < 0, divide el intervalo por
mitades hasta que ea < es o iter >= imax.
"""
import sympy as sp

from lib.optimization_utils import (
    classify_critical_point,
    evaluate_expression,
    parse_expression,
)


class BisectionMethod:
    """
    Método de bisección para hallar puntos críticos de una función.

    Recibe f(x). Calcula f'(x) y busca x* donde f'(x*) = 0 dentro de
    [xl, xu]. Requiere que f'(xl) y f'(xu) tengan signos opuestos.
    """
    def __init__(self, f_expr, xl, xu, es=0.01, imax=100):
        self.xl = float(xl)
        self.xu = float(xu)
        self.es = float(es)
        self.imax = int(imax)
        self.f_expr = f_expr
        self.steps = []

    def solve(self):
        self.steps = []

        if self.f_expr is None or (isinstance(self.f_expr, str)
                                   and self.f_expr.strip() == ""):
            return {
                "success": False,
                "solution": None,
                "steps": self.steps,
                "error_message": (
                    "Se requiere la función original f(x) para calcular "
                    "f'(x) y aplicar el método de bisección."
                ),
            }

        x_sym = sp.Symbol("x")
        try:
            original_sym = parse_expression(self.f_expr)
            f_sym = sp.diff(original_sym, x_sym)
            second_sym = sp.diff(f_sym, x_sym)
        except Exception:
            return {
                "success": False,
                "solution": None,
                "steps": self.steps,
                "error_message": (
                    f"No se pudo interpretar la función original f(x) = "
                    f"'{self.f_expr}'. Verifique la sintaxis."
                ),
            }

        expr_info = {
            "original_expr": str(original_sym),
            "derivative_expr": str(f_sym),
            "second_derivative_expr": str(second_sym),
        }

        if self.xl >= self.xu:
            return {
                "success": False,
                "solution": None,
                "steps": self.steps,
                "error_message": (
                    f"El extremo inferior xl ({self.xl}) debe ser menor "
                    f"que el extremo superior xu ({self.xu})."
                ),
            }

        f_xl = evaluate_expression(f_sym, self.xl)
        f_xu = evaluate_expression(f_sym, self.xu)
        if f_xl is None or f_xu is None:
            return {
                "success": False,
                "solution": None,
                "steps": self.steps,
                "error_message": (
                    "No se pudo evaluar f'(x) en los extremos del intervalo. "
                    "Verifique que f(x) y su derivada sean válidas en [xl, xu]."
                ),
            }

        if abs(f_xl) < 1e-12:
            root = self.xl
            original_value = evaluate_expression(original_sym, root)
            self.steps.append({
                "type": "initial",
                "xl": self.xl, "xu": self.xu,
                "es": self.es, "imax": self.imax,
                "f_expr": str(f_sym),
                **expr_info,
                "f_xl": f_xl, "f_xu": f_xu,
                "description": (
                    f"Datos de entrada: f(x) = {original_sym}, "
                    f"f'(x) = {f_sym}, intervalo [{self.xl}, {self.xu}], "
                    f"es = {self.es}%, imax = {self.imax}. "
                    f"f'(xl) = {f_xl:.6g} (raíz exacta de f' en xl)."
                ),
            })
            self.steps.append({
                "type": "final",
                "root": root, "iterations": 0, "error": 0.0,
                "converged": True, "reason": "raiz_exacta",
                "description": (
                    f"Punto crítico exacto encontrado en xl = {root:.6g}. "
                    f"iter = 0, ea = 0%."
                ),
            })
            classification = classify_critical_point(
                f_sym, root, second_expr=second_sym)
            return {
                "success": True,
                "solution": {
                    "root": root,
                    "iterations": 0,
                    "error": 0.0,
                    "converged": True,
                    "f_value": f_xl,
                    "derivative_value": f_xl,
                    "original_value": original_value,
                    "xl_final": self.xl,
                    "xu_final": self.xu,
                    **expr_info,
                    **classification,
                },
                "steps": self.steps,
                "error_message": None,
                **expr_info,
            }

        if abs(f_xu) < 1e-12:
            root = self.xu
            original_value = evaluate_expression(original_sym, root)
            self.steps.append({
                "type": "initial",
                "xl": self.xl, "xu": self.xu,
                "es": self.es, "imax": self.imax,
                "f_expr": str(f_sym),
                **expr_info,
                "f_xl": f_xl, "f_xu": f_xu,
                "description": (
                    f"Datos de entrada: f(x) = {original_sym}, "
                    f"f'(x) = {f_sym}, intervalo [{self.xl}, {self.xu}], "
                    f"es = {self.es}%, imax = {self.imax}. "
                    f"f'(xu) = {f_xu:.6g} (raíz exacta de f' en xu)."
                ),
            })
            self.steps.append({
                "type": "final",
                "root": root, "iterations": 0, "error": 0.0,
                "converged": True, "reason": "raiz_exacta",
                "description": (
                    f"Punto crítico exacto encontrado en xu = {root:.6g}. "
                    f"iter = 0, ea = 0%."
                ),
            })
            classification = classify_critical_point(
                f_sym, root, second_expr=second_sym)
            return {
                "success": True,
                "solution": {
                    "root": root,
                    "iterations": 0,
                    "error": 0.0,
                    "converged": True,
                    "f_value": f_xu,
                    "derivative_value": f_xu,
                    "original_value": original_value,
                    "xl_final": self.xl,
                    "xu_final": self.xu,
                    **expr_info,
                    **classification,
                },
                "steps": self.steps,
                "error_message": None,
                **expr_info,
            }

        test_sign = f_xl * f_xu
        if test_sign > 0:
            return {
                "success": False,
                "solution": None,
                "steps": self.steps,
                "error_message": (
                    f"No hay cambio de signo en el intervalo: "
                    f"f'({self.xl}) = {f_xl:.6g} y f'({self.xu}) = "
                    f"{f_xu:.6g} tienen el mismo signo. La bisección "
                    f"requiere f'(xl)*f'(xu) < 0."
                ),
            }

        self.steps.append({
            "type": "initial",
            "xl": self.xl, "xu": self.xu,
            "es": self.es, "imax": self.imax,
            "f_expr": str(f_sym),
            **expr_info,
            "f_xl": f_xl, "f_xu": f_xu,
            "description": (
                f"Datos de entrada: f(x) = {original_sym}, "
                f"f'(x) = {f_sym}, intervalo [{self.xl}, {self.xu}], "
                f"es = {self.es}%, imax = {self.imax}. "
                f"f'(xl) = {f_xl:.6g}, f'(xu) = {f_xu:.6g} "
                f"(cambio de signo verificado)."
            ),
        })

        xl = self.xl
        xu = self.xu
        xr = xl
        iter_count = 0
        ea = 100.0
        converged = False
        reason = "max_iter"

        while True:
            xl_used = xl
            xu_used = xu
            xrold = xr
            xr = (xl_used + xu_used) / 2.0
            iter_count += 1

            if xr != 0:
                ea = abs((xr - xrold) / xr) * 100.0

            f_xl_cur = evaluate_expression(f_sym, xl_used)
            f_xr_cur = evaluate_expression(f_sym, xr)
            if f_xl_cur is None or f_xr_cur is None:
                return {
                    "success": False,
                    "solution": None,
                    "steps": self.steps,
                    "error_message": (
                        f"No se pudo evaluar f'(x) en la iteración "
                        f"{iter_count}. Verifique el dominio de f(x)."
                    ),
                }
            test = f_xl_cur * f_xr_cur

            if test < 0:
                xu = xr
                action = "xu = xr"
            elif test > 0:
                xl = xr
                action = "xl = xr"
            else:
                ea = 0.0
                action = "raiz_exacta"

            self.steps.append({
                "type": "iteration",
                "iter": iter_count,
                "xl": xl_used, "xu": xu_used,
                "xl_new": xl, "xu_new": xu,
                "xr": xr, "xrold": xrold,
                "ea": ea, "test": test,
                "action": action,
                "f_xl": f_xl_cur, "f_xr": f_xr_cur,
                "description": (
                    f"iter {iter_count}: xr = ({xl_used:.6g} + "
                    f"{xu_used:.6g})/2 = {xr:.6g}  |  ea = {ea:.6g}%  "
                    f"|  test = f'({xl_used:.6g})*f'({xr:.6g}) = "
                    f"{test:.6g}  →  {action}"
                ),
            })

            if action == "raiz_exacta":
                converged = True
                reason = "raiz_exacta"
                break
            if ea < self.es or abs(f_xr_cur) <= self.es:
                converged = True
                reason = "tolerancia"
                break
            if iter_count >= self.imax:
                converged = False
                reason = "max_iter"
                break

        f_xr_final = evaluate_expression(f_sym, xr)
        if f_xr_final is None:
            f_xr_final = 0.0
        original_value = evaluate_expression(original_sym, xr)

        self.steps.append({
            "type": "final",
            "root": xr, "iterations": iter_count, "error": ea,
            "converged": converged, "reason": reason,
            "description": (
                f"Resultado: punto crítico x* = {xr:.6g}  |  iter = "
                f"{iter_count}  |  ea = {ea:.6g}%  |  "
                f"converged = {converged}  |  razón = "
                f"{'tolerancia alcanzada' if reason == 'tolerancia' else 'raíz exacta' if reason == 'raiz_exacta' else 'máximo de iteraciones'}"
            ),
        })

        classification = classify_critical_point(
            f_sym, xr, second_expr=second_sym)
        return {
            "success": True,
            "solution": {
                "root": xr,
                "iterations": iter_count,
                "error": ea,
                "converged": converged,
                "f_value": f_xr_final,
                "derivative_value": f_xr_final,
                "original_value": original_value,
                "xl_final": xl,
                "xu_final": xu,
                **expr_info,
                **classification,
            },
            "steps": self.steps,
            "error_message": None,
            **expr_info,
        }
