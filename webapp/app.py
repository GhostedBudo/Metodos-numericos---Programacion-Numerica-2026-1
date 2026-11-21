"""Aplicación web móvil para optimizar f(x) con Bisección, Newton y Secante."""
from __future__ import annotations

import math
import pathlib
import sys

import sympy as sp
from flask import Flask, jsonify, render_template, request
from sympy.calculus.util import continuous_domain

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.bisection_method import BisectionMethod
from lib.newton_raphson import NewtonRoots
from lib.optimization_utils import (
    build_function_spec,
    clipped_segment,
    evaluate_curve,
    evaluate_expression,
    visible_y_range,
)
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


def _format_endpoint(value):
    if value == -sp.oo:
        return "-∞"
    if value == sp.oo:
        return "∞"
    return str(value)


def _format_domain(domain):
    if domain == sp.S.Reals:
        return "todos los reales"
    if domain == sp.S.EmptySet:
        return "ningún número real"
    if isinstance(domain, sp.Union):
        return " ∪ ".join(_format_domain(arg) for arg in domain.args)
    if isinstance(domain, sp.Interval):
        left = "(" if domain.left_open else "["
        right = ")" if domain.right_open else "]"
        return (
            f"{left}{_format_endpoint(domain.start)}, "
            f"{_format_endpoint(domain.end)}{right}"
        )
    if isinstance(domain, sp.FiniteSet):
        return "{" + ", ".join(_format_endpoint(v) for v in domain.args) + "}"
    return str(domain).replace("oo", "∞")


def _safe_domain(expr):
    if expr is None:
        return "no disponible"
    try:
        domain = continuous_domain(expr, sp.Symbol("x"), sp.S.Reals)
    except Exception:
        return "no se pudo determinar simbólicamente"
    return _format_domain(domain)


def _describe_function(expr_str, input_type, points, require_second):
    try:
        spec = build_function_spec(expr_str, input_type=input_type)
    except Exception as exc:
        return {
            "processable": False,
            "text": (
                "ANÁLISIS DE LA FUNCIÓN\n\n"
                f"No se pudo interpretar la entrada: {exc}"
            ),
        }

    function_input = spec["input_type"] == "function"
    entry_expr = spec["original"] if function_input else spec["derivative"]
    entry_label = "f(x)" if function_input else "f'(x)"
    lines = ["ANÁLISIS DE LA FUNCIÓN", ""]

    if function_input:
        lines += [
            f"f(x) = {spec['original_str']}",
            f"f'(x) = {spec['derivative_str']}",
            f"f''(x) = {spec['second_derivative_str']}",
        ]
    else:
        lines += [
            f"f'(x) = {spec['derivative_str']}",
            f"f''(x) = {spec['second_derivative_str']}",
            f"F(x) integrada con C = 0 (solo gráfica) = {spec['original_str']}",
        ]

    lines += [
        "",
        f"Dominio real de {entry_label}: {_safe_domain(entry_expr)}",
    ]
    if function_input:
        lines.append(f"Dominio real de f'(x): {_safe_domain(spec['derivative'])}")
    lines += [
        f"Dominio real de f''(x): {_safe_domain(spec['second_derivative'])}",
        "Continuidad y diferenciabilidad:",
    ]
    if function_input:
        lines.append("  f(x) está definida y es continua en su dominio real.")
    lines += [
        "  f'(x) está definida y es continua en su dominio real.",
        "  f''(x) está definida y es continua en su dominio real.",
    ]

    reasons = []
    if points:
        lines += ["", "Puntos evaluados por el método:"]
        for point in points:
            entry_value = evaluate_expression(entry_expr, point)
            derivative_value = evaluate_expression(spec["derivative"], point)
            second_value = evaluate_expression(spec["second_derivative"], point)
            lines.append(
                f"  x = {_fmt(point)}: {entry_label} = {_fmt(entry_value)}, "
                f"f'(x) = {_fmt(derivative_value)}, f''(x) = {_fmt(second_value)}"
            )
            if entry_value is None or derivative_value is None:
                reasons.append(
                    f"la función o f'(x) no están definidas en x = {_fmt(point)}"
                )
            if require_second and second_value is None:
                reasons.append(f"f''(x) no está definida en x = {_fmt(point)}")

    processable = not reasons
    lines.append("")
    if processable:
        lines.append("Verificación inicial: PROCESABLE.")
    else:
        lines.append("Verificación inicial: NO PROCESABLE.")
        for reason in dict.fromkeys(reasons):
            lines.append(f"  - {reason}")

    return {"processable": processable, "text": "\n".join(lines)}


def _make_numeric(expr):
    """Convierte una expresión simbólica en una función numérica segura."""
    x_sym = sp.Symbol("x")
    try:
        numeric_fn = sp.lambdify(x_sym, expr, "numpy")
    except Exception:
        return lambda _value: None

    def evaluate(value):
        try:
            return _safe_float(numeric_fn(value))
        except Exception:
            return None

    return evaluate


def _curve_data(expr, lo, hi, points=320):
    """Genera puntos (x, y) reales para una expresión simbólica."""
    xs, ys = evaluate_curve(expr, lo, hi, points)
    return {
        "x": [_safe_float(value) for value in xs],
        "y": [_safe_float(value) for value in ys],
    }


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
    original_name = (
        "F(x)" if solution.get("original_is_antiderivative") else "f(x)"
    )
    lines = [
        "PROCEDIMIENTO — BISECCIÓN SOBRE f'(x)",
        f"{original_name} = {solution.get('original_expr', '---')}",
        f"f'(x) = {solution.get('derivative_expr', '---')}",
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
                f"  {original_name} = {solution.get('original_expr', '---')}",
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
                f"  {original_name}* = {_fmt(solution.get('original_value'))}",
                f"  f'(x*) = {_fmt(solution['f_value'])}",
                f"  f''(x*) = {_fmt(solution.get('second_derivative'))}",
                f"  Clasificación: {solution.get('critical_type', 'inconcluso')}",
                f"  {solution.get('classification', '')}",
            ])
    return "\n".join(lines)


def _newton_steps_text(history, second_fn, result):
    original_name = (
        "F(x)" if result.get("original_is_antiderivative") else "f(x)"
    )
    lines = [
        "PROCEDIMIENTO — NEWTON SOBRE f'(x)",
        f"{original_name} = {result.get('original_expr', '---')}",
        f"f'(x) = {result.get('derivative_expr', '---')}",
        f"f''(x) = {result.get('second_derivative_expr', '---')}",
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
        f"  {original_name}* = {_fmt(result.get('original_value'))}",
        f"  f'(x*) = {_fmt(final['fx'])}",
        f"  f''(x*) = {_fmt(result.get('second_derivative'))}",
        f"  Clasificación: {result.get('critical_type', 'inconcluso')}",
        f"  {result.get('classification', '')}",
    ])
    return "\n".join(lines)


def _secant_steps_text(history, result):
    original_name = (
        "F(x)" if result.get("original_is_antiderivative") else "f(x)"
    )
    lines = [
        "PROCEDIMIENTO — SECANTE SOBRE f'(x)",
        f"{original_name} = {result.get('original_expr', '---')}",
        f"f'(x) = {result.get('derivative_expr', '---')}",
        f"f''(x) = {result.get('second_derivative_expr', '---')}",
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
        f"  {original_name}* = {_fmt(result.get('original_value'))}",
        f"  f'(x*) = {_fmt(final['fx'])}",
        f"  f''(x*) = {_fmt(result.get('second_derivative'))}",
        f"  Clasificación: {result.get('critical_type', 'inconcluso')}",
        f"  {result.get('classification', '')}",
    ])
    return "\n".join(lines)


def _error_response(message, method, analysis=None):
    return jsonify({
        "success": False,
        "method": method,
        "error_message": message,
        "analysis": analysis or {
            "processable": False,
            "text": f"ANÁLISIS DE LA FUNCIÓN\n\n{message}",
        },
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
    input_type = str(payload.get("input_type", "function")).strip().lower()
    if not expr_str:
        analysis = _describe_function(expr_str, input_type, [], False)
        return _error_response(
            "Escribe f(x) o f'(x), según el tipo de entrada.",
            method,
            analysis,
        )

    try:
        if method == "bisection":
            xl = float(payload.get("xl"))
            xu = float(payload.get("xu"))
            es = float(payload.get("es", 0.01))
            imax = int(payload.get("imax", 100))
            points = [xl, xu]
            solver = BisectionMethod(
                expr_str, xl, xu, es=es, imax=imax,
                input_type=input_type)
        elif method == "newton":
            x0 = float(payload.get("x0"))
            tol = float(payload.get("tol", 1e-5))
            max_iter = int(payload.get("max_iter", 150))
            points = [x0]
            solver = NewtonRoots(
                expr_str, x0, tol, max_iter, input_type=input_type)
        else:
            x0 = float(payload.get("x0"))
            x1 = float(payload.get("x1"))
            tol = float(payload.get("tol", 1e-5))
            max_iter = int(payload.get("max_iter", 150))
            points = [x0, x1]
            solver = SecantRoots(
                expr_str, x0, x1, tol, max_iter, input_type=input_type)
    except (TypeError, ValueError) as exc:
        reason = f"Datos numéricos inválidos: {exc}"
        analysis = _describe_function(expr_str, input_type, [], False)
        analysis["processable"] = False
        analysis["text"] += f"\n\nNO PROCESABLE: {reason}"
        return _error_response(reason, method, analysis)

    analysis = _describe_function(
        expr_str, input_type, points, method == "newton")
    if not analysis["processable"]:
        return _error_response(
            "La función no puede procesarse con este método.",
            method,
            analysis,
        )

    result = solver.solve()
    if not result.get("success"):
        reason = (
            result.get("error_message") or "No se pudo resolver el problema."
        )
        analysis["processable"] = False
        analysis["text"] += f"\n\nNO PROCESABLE: {reason}"
        return _error_response(reason, method, analysis)

    analysis["text"] += "\n\nPROCESABLE: el método pudo ejecutarse."

    try:
        spec = build_function_spec(expr_str, input_type=input_type)
    except Exception as exc:
        reason = f"No se pudieron calcular las derivadas: {exc}"
        analysis["processable"] = False
        analysis["text"] += f"\n\nNO PROCESABLE: {reason}"
        return _error_response(reason, method, analysis)

    original_fn = _make_numeric(spec["original"])
    derivative_fn = _make_numeric(spec["derivative"])
    second_fn = _make_numeric(spec["second_derivative"])

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
                "original_y": original_fn(step["xr"]),
                "iter": step["iter"],
                "bracket": [_safe_float(step["xl"]), _safe_float(step["xu"])],
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
            reason = "No se generaron iteraciones."
            analysis["processable"] = False
            analysis["text"] += f"\n\nNO PROCESABLE: {reason}"
            return _error_response(reason, method, analysis)
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
                "original_y": original_fn(point["x"]),
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
    if final_y is None:
        final_y = derivative_fn(final_x)
    original_value = original_fn(final_x)
    derivative_value = derivative_fn(final_x)
    original_curve = _curve_data(spec["original"], domain[0], domain[1])
    derivative_curve = _curve_data(spec["derivative"], domain[0], domain[1])

    if method == "newton":
        deriv_range = visible_y_range(derivative_curve["y"])
        x_half = 0.35 * (domain[1] - domain[0])
        for point in iter_points:
            point["segment"] = clipped_segment(
                point["x"], point["y"], second_fn(point["x"]),
                x_half, deriv_range)
    elif method == "secant":
        deriv_range = visible_y_range(derivative_curve["y"])
        x_half = 0.35 * (domain[1] - domain[0])
        for index, point in enumerate(iter_points):
            segment = None
            if index > 0:
                previous = iter_points[index - 1]
                slope = None
                if point["x"] != previous["x"]:
                    slope = (point["y"] - previous["y"]) / (
                        point["x"] - previous["x"])
                segment = clipped_segment(
                    previous["x"], previous["y"], slope, x_half, deriv_range)
            point["segment"] = segment
    original_prefix = "F(x)" if spec["original_is_antiderivative"] else "f(x)"
    original_label = (
        f"{original_prefix} = {spec['original_str']}"
        + (" (C=0)" if spec["original_is_antiderivative"] else "")
    )
    return jsonify({
        "success": True,
        "method": method,
        "analysis": analysis,
        "summary": {
            "root": final_x,
            "iterations": iterations,
            "error": error,
            "f_value": final_y,
            "derivative_value": derivative_value,
            "original_value": original_value,
            "second_derivative": second_value,
            "critical_type": critical_type,
            "classification": classification,
            "converged": converged,
            "xl_final": xl_final,
            "xu_final": xu_final,
            "message": message,
            "original_expr": spec["original_str"],
            "derivative_expr": spec["derivative_str"],
            "second_derivative_expr": spec["second_derivative_str"],
            "input_type": spec["input_type"],
            "original_is_antiderivative": spec["original_is_antiderivative"],
        },
        "steps_text": steps_text,
        "table": table,
        "graph": {
            "curve": derivative_curve,
            "original_curve": original_curve,
            "derivative_curve": derivative_curve,
            "original_label": original_label,
            "derivative_label": f"f'(x) = {spec['derivative_str']}",
            "iterations": iter_points,
            "final": {
                "x": final_x,
                "y": final_y,
                "original_y": original_value,
                "iter": final_iter,
            },
            "domain": domain,
            "initial_interval": initial_interval,
            "max_iter": max((point["iter"] for point in iter_points), default=0),
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
