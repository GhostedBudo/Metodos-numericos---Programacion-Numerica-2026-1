"""Aplicación web móvil para Bisección, Newton y Secante sobre f'(x)."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import sympy as sp
from flask import Flask, jsonify, render_template, request

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.bisection_method import BisectionMethod
from lib.newton_raphson import NewtonRoots
from lib.optimization_utils import parse_expression
from lib.secante import SecantRoots

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)


def _safe_float(value):
    """Convierte a float JSON-safe. Devuelve None si no es real/finito."""
    try:
        complex_value = complex(value)
    except Exception:
        return None
    if abs(complex_value.imag) > 1e-9:
        return None
    result = complex_value.real
    if not math.isfinite(result):
        return None
    return float(result)


def _fmt(value, digits=10):
    number = _safe_float(value)
    if number is None:
        return "---"
    return f"{number:.{digits}g}"


def _make_second_derivative(expr_str):
    """Devuelve una función numérica f''(x) a partir de f'(x)."""
    x_sym = sp.Symbol("x")
    try:
        expr = parse_expression(expr_str)
        second = sp.diff(expr, x_sym)
        second_fn = sp.lambdify(x_sym, second, "numpy")

        def evaluate(value):
            try:
                return _safe_float(second_fn(value))
            except Exception:
                return None

        return evaluate
    except Exception:
        return lambda _value: None


def _curve_data(expr_str, lo, hi, points=320):
    """Genera puntos (x, f'(x)) para la gráfica."""
    x_sym = sp.Symbol("x")
    try:
        expr = parse_expression(expr_str)
        fn = sp.lambdify(x_sym, expr, "numpy")
        xs = np.linspace(lo, hi, points)
        with np.errstate(all="ignore"):
            ys = fn(xs)
        if np.isscalar(ys):
            ys = np.full(xs.shape, ys)
        ys = np.asarray(ys).ravel()
        if ys.size != xs.size:
            ys = np.full(xs.shape, _safe_float(ys))
        return {
            "x": [_safe_float(value) for value in xs],
            "y": [_safe_float(value) for value in ys],
        }
    except Exception:
        return {"x": [], "y": []}


def _bisection_table(steps):
    rows = []
    for step in steps:
        if step.get("type") != "iteration":
            continue
        rows.append({
            "iter": step["iter"],
            "xl": _safe_float(step["xl"]),
            "xu": _safe_float(step["xu"]),
            "xr": _safe_float(step["xr"]),
            "fp_xl": _safe_float(step["f_xl"]),
            "fp_xr": _safe_float(step["f_xr"]),
            "test": _safe_float(step["test"]),
            "ea": _safe_float(step["ea"]),
        })
    return rows


def _newton_table(history, second_fn):
    rows = []
    for point in history:
        rows.append({
            "iter": point["iter"],
            "x": _safe_float(point["x"]),
            "fp": _safe_float(point["fx"]),
            "fpp": second_fn(point["x"]),
            "ea": _safe_float(point["error"]),
        })
    return rows


def _secant_table(history):
    rows = []
    for point in history:
        rows.append({
            "iter": point["iter"],
            "x": _safe_float(point["x"]),
            "fp": _safe_float(point["fx"]),
            "ea": _safe_float(point["error"]),
        })
    return rows


def _bisection_steps_text(steps, solution):
    lines = [
        "PROCEDIMIENTO — BISECCIÓN SOBRE f'(x)",
        "Objetivo: hallar x* donde f'(x*) = 0.",
        "",
        "Fórmulas:",
        "  xr = (xl + xu) / 2",
        "  test = f'(xl) * f'(xr)",
        "  ea = |(xr - xr_anterior) / xr| * 100%",
        "",
        "Decisión:",
        "  test < 0  →  xu = xr  (el punto crítico está a la izquierda)",
        "  test > 0  →  xl = xr  (el punto crítico está a la derecha)",
        "  test = 0  →  x* exacto",
        "",
    ]
    for step in steps:
        if step.get("type") == "initial":
            lines.extend([
                "DATOS INICIALES",
                f"  f'(x) = {step['f_expr']}",
                f"  Intervalo = [{_fmt(step['xl'])}, {_fmt(step['xu'])}]",
                f"  f'(xl) = {_fmt(step['f_xl'])}",
                f"  f'(xu) = {_fmt(step['f_xu'])}",
                f"  f'(xl)*f'(xu) = {_fmt(step['f_xl'] * step['f_xu'])}",
                f"  es = {step['es']}%   imax = {step['imax']}",
                "",
            ])
        elif step.get("type") == "iteration":
            decision = "x* exacto" if step["action"] == "raiz_exacta" else step["action"]
            xl_new = step.get("xl_new", step["xl"])
            xu_new = step.get("xu_new", step["xu"])
            lines.extend([
                "─" * 60,
                f"ITERACIÓN {step['iter']}",
                f"  xr = (xl + xu)/2 = ({_fmt(step['xl'])} + {_fmt(step['xu'])})/2 = {_fmt(step['xr'])}",
                f"  xr_anterior = {_fmt(step['xrold'])}",
                f"  f'(xl) = {_fmt(step['f_xl'])}",
                f"  f'(xr) = {_fmt(step['f_xr'])}",
                f"  test = f'(xl)*f'(xr) = ({_fmt(step['f_xl'])})*({_fmt(step['f_xr'])}) = {_fmt(step['test'])}",
                f"  Decisión: {decision}",
                f"  Nuevo intervalo: [{_fmt(xl_new)}, {_fmt(xu_new)}]",
                f"  ea = |({_fmt(step['xr'])} - {_fmt(step['xrold'])})/{_fmt(step['xr'])}|*100 = {_fmt(step['ea'])}%",
                "",
            ])
        elif step.get("type") == "final":
            lines.extend([
                "═" * 60,
                "RESULTADO FINAL",
                f"  x* ≈ {_fmt(step['root'])}",
                f"  Iteraciones = {step['iterations']}",
                f"  ea final = {_fmt(step['error'])}%",
                f"  f'(x*) = {_fmt(solution['f_value'])}",
                f"  f''(x*) = {_fmt(solution.get('second_derivative'))}",
                f"  Clasificación: {solution.get('critical_type', 'inconcluso')}",
                f"  {solution.get('classification', '')}",
            ])
    return "\n".join(lines)


def _newton_steps_text(history, second_fn, result):
    lines = [
        "PROCEDIMIENTO — NEWTON SOBRE f'(x)",
        "Objetivo: resolver f'(x) = 0.",
        "",
        "Fórmula:",
        "  x(k+1) = x(k) - f'(x(k)) / f''(x(k))",
        "",
        "Error relativo:",
        "  ea = |(x(k+1) - x(k)) / x(k+1)| * 100%",
        "",
    ]
    for index in range(len(history) - 1):
        actual = history[index]
        siguiente = history[index + 1]
        xk = actual["x"]
        fpk = actual["fx"]
        xnext = siguiente["x"]
        second = second_fn(xk)
        lines.extend([
            "─" * 60,
            f"ITERACIÓN {index + 1}",
            f"  x({index}) = {_fmt(xk)}",
            f"  f'(x({index})) = {_fmt(fpk)}",
        ])
        if second is not None:
            lines.extend([
                f"  f''(x({index})) = {_fmt(second)}",
                f"  x({index + 1}) = x({index}) - f'(x({index})) / f''(x({index}))",
                f"           = {_fmt(xk)} - ({_fmt(fpk)}) / ({_fmt(second)})",
                f"           = {_fmt(xnext)}",
            ])
        else:
            lines.append(f"  x({index + 1}) = {_fmt(xnext)}")
        if siguiente["error"] is not None:
            lines.append(f"  ea = {_fmt(siguiente['error'])}%")
        lines.append("")

    final = history[-1]
    lines.extend([
        "═" * 60,
        "RESULTADO FINAL",
        f"  x* ≈ {_fmt(final['x'])}",
        f"  f'(x*) = {_fmt(final['fx'])}",
        f"  f''(x*) = {_fmt(result.get('second_derivative'))}",
        f"  Clasificación: {result.get('critical_type', 'inconcluso')}",
        f"  {result.get('classification', '')}",
    ])
    return "\n".join(lines)


def _secant_steps_text(history, result):
    lines = [
        "PROCEDIMIENTO — SECANTE SOBRE f'(x)",
        "Objetivo: resolver f'(x) = 0 sin calcular f''(x).",
        "",
        "Fórmula:",
        "  x(k+1) = x(k) - f'(x(k))·(x(k) - x(k-1)) / (f'(x(k)) - f'(x(k-1)))",
        "",
        "Error relativo:",
        "  ea = |(x(k+1) - x(k)) / x(k+1)| * 100%",
        "",
    ]
    if len(history) >= 3:
        for index in range(1, len(history) - 1):
            prev = history[index - 1]
            curr = history[index]
            nxt = history[index + 1]
            x_prev = prev["x"]
            f_prev = prev["fx"]
            x_curr = curr["x"]
            f_curr = curr["fx"]
            x_next = nxt["x"]
            denominator = f_curr - f_prev
            lines.extend([
                "─" * 60,
                f"ITERACIÓN {nxt['iter']}",
                f"  x(k-1) = {_fmt(x_prev)}   f'(x(k-1)) = {_fmt(f_prev)}",
                f"  x(k)   = {_fmt(x_curr)}   f'(x(k))   = {_fmt(f_curr)}",
                "  x(k+1) = x(k) - f'(x(k))·(x(k) - x(k-1)) / (f'(x(k)) - f'(x(k-1)))",
                f"         = {_fmt(x_curr)} - ({_fmt(f_curr)})·({_fmt(x_curr)} - {_fmt(x_prev)}) / ({_fmt(f_curr)} - {_fmt(f_prev)})",
                f"         = {_fmt(x_curr)} - ({_fmt(f_curr)})·({_fmt(x_curr - x_prev)}) / ({_fmt(denominator)})",
                f"         = {_fmt(x_next)}",
            ])
            if nxt["error"] is not None:
                lines.append(f"  ea = {_fmt(nxt['error'])}%")
            lines.append("")

    final = history[-1]
    lines.extend([
        "═" * 60,
        "RESULTADO FINAL",
        f"  x* ≈ {_fmt(final['x'])}",
        f"  f'(x*) = {_fmt(final['fx'])}",
        f"  f''(x*) = {_fmt(result.get('second_derivative'))}",
        f"  Clasificación: {result.get('critical_type', 'inconcluso')}",
        f"  {result.get('classification', '')}",
    ])
    return "\n".join(lines)


def _error_response(message, method):
    return jsonify({
        "success": False,
        "method": method,
        "error_message": message,
    })


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/solve")
def solve():
    payload = request.get_json(silent=True) or {}
    method = str(payload.get("method", "")).strip().lower()

    if method not in {"bisection", "newton", "secant"}:
        return _error_response("Método no válido.", method)

    expr_str = str(payload.get("expr", "")).strip()
    if not expr_str:
        return _error_response("Escribe la primera derivada f'(x).", method)

    try:
        if method == "bisection":
            xl = float(payload.get("xl"))
            xu = float(payload.get("xu"))
            es = float(payload.get("es", 0.01))
            imax = int(payload.get("imax", 100))
            solver = BisectionMethod(expr_str, xl, xu, es=es, imax=imax)
        elif method == "newton":
            x0 = float(payload.get("x0"))
            tol = float(payload.get("tol", 1e-5))
            max_iter = int(payload.get("max_iter", 150))
            solver = NewtonRoots(expr_str, x0, tol, max_iter)
        else:
            x0 = float(payload.get("x0"))
            x1 = float(payload.get("x1"))
            tol = float(payload.get("tol", 1e-5))
            max_iter = int(payload.get("max_iter", 150))
            solver = SecantRoots(expr_str, x0, x1, tol, max_iter)
    except (TypeError, ValueError) as exc:
        return _error_response(f"Datos numéricos inválidos: {exc}", method)

    result = solver.solve()
    if not result.get("success"):
        return _error_response(
            result.get("error_message") or "No se pudo resolver el problema.",
            method,
        )

    second_fn = _make_second_derivative(expr_str)

    if method == "bisection":
        solution = result["solution"]
        root = _safe_float(solution["root"])
        iterations = solution["iterations"]
        error = _safe_float(solution["error"])
        f_value = _safe_float(solution["f_value"])
        second_value = _safe_float(solution.get("second_derivative"))
        critical_type = solution.get("critical_type", "inconcluso")
        classification = solution.get("classification", "")
        converged = bool(solution.get("converged"))
        xl_final = _safe_float(solution.get("xl_final"))
        xu_final = _safe_float(solution.get("xu_final"))
        message = ""
        steps_text = _bisection_steps_text(result["steps"], solution)
        table = _bisection_table(result["steps"])
        iter_points = [
            {
                "x": _safe_float(step["xr"]),
                "y": _safe_float(step["f_xr"]),
                "iter": step["iter"],
            }
            for step in result["steps"]
            if step.get("type") == "iteration"
        ]
        final_iter = iterations
        margin = 0.2 * (xu - xl)
        domain = [xl - margin, xu + margin]
        initial_interval = [xl, xu]
    else:
        history = result["steps"]
        if not history:
            return _error_response("No se generaron iteraciones.", method)
        final_point = history[-1]
        root = _safe_float(final_point["x"])
        iterations = len(history)
        error = _safe_float(final_point["error"])
        f_value = _safe_float(final_point["fx"])
        second_value = _safe_float(result.get("second_derivative"))
        critical_type = result.get("critical_type", "inconcluso")
        classification = result.get("classification", "")
        tol_value = float(payload.get("tol", 1e-5))
        converged = (
            (f_value is not None and abs(f_value) <= tol_value)
            or (error is not None and error <= tol_value)
        )
        xl_final = None
        xu_final = None
        message = result.get("message", "")
        if method == "newton":
            steps_text = _newton_steps_text(history, second_fn, result)
            table = _newton_table(history, second_fn)
        else:
            steps_text = _secant_steps_text(history, result)
            table = _secant_table(history)
        iter_points = [
            {
                "x": _safe_float(point["x"]),
                "y": _safe_float(point["fx"]),
                "iter": point["iter"],
            }
            for point in history
        ]
        final_iter = final_point["iter"]
        xmin = float(payload.get("xmin", min(point["x"] for point in history)))
        xmax = float(payload.get("xmax", max(point["x"] for point in history)))
        domain = [xmin, xmax]
        initial_interval = None

    final_x = _safe_float(root)
    final_y = _safe_float(f_value)
    return jsonify({
        "success": True,
        "method": method,
        "summary": {
            "root": final_x,
            "iterations": iterations,
            "error": error,
            "f_value": final_y,
            "second_derivative": second_value,
            "critical_type": critical_type,
            "classification": classification,
            "converged": converged,
            "xl_final": xl_final,
            "xu_final": xu_final,
            "message": message,
        },
        "steps_text": steps_text,
        "table": table,
        "graph": {
            "curve": _curve_data(expr_str, domain[0], domain[1]),
            "iterations": iter_points,
            "final": {
                "x": final_x,
                "y": final_y,
                "iter": final_iter,
            },
            "domain": domain,
            "initial_interval": initial_interval,
            "max_iter": max((point["iter"] for point in iter_points), default=0),
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
