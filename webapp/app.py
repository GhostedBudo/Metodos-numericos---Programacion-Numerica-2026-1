"""Aplicación web móvil para optimizar f(x) con Bisección, Newton y Secante."""
from __future__ import annotations

import math
import pathlib
import re
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


def _spec_latex(spec):
    original = spec.get("original")
    return {
        "original_label": "F(x)" if spec["original_is_antiderivative"] else "f(x)",
        "original": sp.latex(original) if original is not None else None,
        "derivative": sp.latex(spec["derivative"]),
        "second_derivative": sp.latex(spec["second_derivative"]),
    }


def _math(text):
    return f"\\({text}\\)"


def _math_fmt(value, digits=10):
    text = _fmt(value, digits)
    return text if text != "---" else r"\text{---}"


def _math_domain(expr):
    text = _safe_domain(expr)
    if text in {
        "todos los reales",
        "ningún número real",
        "no se pudo determinar simbólicamente",
        "no disponible",
    }:
        return text
    return _math(text.replace("∞", r"\infty").replace("∪", r"\cup"))


def _math_value(label, value, digits=10):
    return _math(f"{label} = {_math_fmt(value, digits)}")


def _math_interval(left, right):
    return _math(f"[{left}, {right}]")


def _math_percent(value, digits=10):
    return f"{_math_fmt(value, digits)}\\%"


def _latex_prose(text):
    if not text:
        return ""
    pattern = re.compile(
        r"f''\(x\*\)|f'\(x\*\)|f'\(x\)\s*=\s*[-+]?[\d.eE+-]+|f'\(x\)|f'"
    )
    return pattern.sub(lambda match: _math(match.group().strip()), text)


LABEL_FP = "f'(x)"
LABEL_FPP = "f''(x)"
LABEL_FP_STAR = "f'(x^*)"
LABEL_FPP_STAR = "f''(x^*)"


def _describe_function(expr_str, input_type, points, require_second):
    try:
        spec = build_function_spec(expr_str, input_type=input_type)
    except Exception as exc:
        return {
            "processable": False,
            "text": (
                "ANÁLISIS DE LA FUNCIÓN\n"
                "Veredicto: NO PROCESABLE\n"
                f"  - No se pudo interpretar la entrada: {exc}"
            ),
        }

    latex = _spec_latex(spec)
    label_f_raw = "f(x)"
    label_fp_raw = "f'(x)"
    label_fpp_raw = "f''(x)"
    label_f = _math(label_f_raw)
    label_fp = _math(label_fp_raw)
    label_fpp = _math(label_fpp_raw)
    function_input = spec["input_type"] == "function"
    entry_expr = spec["original"] if function_input else spec["derivative"]
    entry_label_raw = label_f_raw if function_input else label_fp_raw
    entry_label = _math(entry_label_raw)
    lines = ["ANÁLISIS DE LA FUNCIÓN", ""]

    if function_input:
        lines += [
            _math(f"f(x) = {latex['original']}"),
            _math(f"f'(x) = {latex['derivative']}"),
            _math(f"f''(x) = {latex['second_derivative']}"),
        ]
    else:
        lines += [
            _math(f"f'(x) = {latex['derivative']}"),
            _math(f"f''(x) = {latex['second_derivative']}"),
            f"{_math('F(x)')} integrada con {_math('C = 0')} (solo gráfica) = "
            f"{_math(latex['original'])}",
        ]

    lines += [
        "",
        f"Dominio real de {entry_label}: {_math_domain(entry_expr)}",
    ]
    if function_input:
        lines.append(f"Dominio real de {label_fp}: {_math_domain(spec['derivative'])}")
    lines += [
        f"Dominio real de {label_fpp}: {_math_domain(spec['second_derivative'])}",
        "Continuidad y diferenciabilidad:",
    ]
    if function_input:
        lines.append(f"  {label_f} está definida y es continua en su dominio real.")
    lines += [
        f"  {label_fp} está definida y es continua en su dominio real.",
        f"  {label_fpp} está definida y es continua en su dominio real.",
    ]

    reasons = []
    if points:
        lines += ["", "Puntos evaluados por el método:"]
        for point in points:
            entry_value = evaluate_expression(entry_expr, point)
            derivative_value = evaluate_expression(spec["derivative"], point)
            second_value = evaluate_expression(spec["second_derivative"], point)
            lines.append(
                f"  {_math('x = ' + _fmt(point))}: "
                f"{_math(entry_label_raw + ' = ' + _math_fmt(entry_value))}, "
                f"{_math(label_fp_raw + ' = ' + _math_fmt(derivative_value))}, "
                f"{_math(label_fpp_raw + ' = ' + _math_fmt(second_value))}"
            )
            if entry_value is None or derivative_value is None:
                reasons.append(
                    f"la función o f'(x) no están definidas en x = {_fmt(point)}"
                )
            if require_second and second_value is None:
                reasons.append(f"f''(x) no está definida en x = {_fmt(point)}")

    processable = not reasons
    verdict = "PROCESABLE" if processable else "NO PROCESABLE"
    header = ["ANÁLISIS DE LA FUNCIÓN", f"Veredicto: {verdict}"]
    for reason in dict.fromkeys(reasons):
        header.append(f"  - {reason}")
    return {
        "processable": processable,
        "text": "\n".join(header + [""] + lines[2:]),
    }


def _set_analysis_verdict(analysis, processable, reason=None):
    analysis["processable"] = processable
    verdict = "PROCESABLE" if processable else "NO PROCESABLE"
    lines = analysis["text"].splitlines()
    verdict_line = f"Veredicto: {verdict}"
    if len(lines) > 1 and lines[1].startswith("Veredicto:"):
        lines[1] = verdict_line
    else:
        lines.insert(1, verdict_line)
    if reason:
        reason_line = f"  - {reason}"
        if reason_line not in lines:
            lines.insert(2, reason_line)
    analysis["text"] = "\n".join(lines)


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


def _bisection_steps_text(steps, solution, latex):
    original_prefix = "F" if solution.get("original_is_antiderivative") else "f"
    original_point = f"{original_prefix}(x^*)"
    original_expr = latex["original"]
    derivative_expr = latex["derivative"]
    label_fp_xl = "f'(x_l)"
    label_fp_xu = "f'(x_u)"
    label_fp_xr = "f'(x_r)"
    formula_xr = r"x_r = \frac{x_l + x_u}{2}"
    formula_test = r"test = f'(x_l) \cdot f'(x_r)"
    formula_ea = r"e_a = \left|\frac{x_r - x_{r,ant}}{x_r}\right| 100\%"
    lines = [
        f"PROCEDIMIENTO — BISECCIÓN SOBRE {_math(LABEL_FP)}",
        _math(f"{original_prefix}(x) = {original_expr}"),
        _math(f"f'(x) = {derivative_expr}"),
        f"Objetivo: hallar {_math('x^*')} donde {_math(LABEL_FP_STAR + ' = 0')}.",
        "",
        "Fórmulas:",
        f"  {_math(formula_xr)}",
        f"  {_math(formula_test)}",
        f"  {_math(formula_ea)}",
        "",
        "Decisión:",
        f"  {_math('test < 0')} → {_math('x_u = x_r')} (el punto crítico está a la izquierda)",
        f"  {_math('test > 0')} → {_math('x_l = x_r')} (el punto crítico está a la derecha)",
        f"  {_math('test = 0')} → {_math('x^*')} exacto",
        "",
    ]
    for step in steps:
        if step.get("type") == "initial":
            lines.extend([
                "DATOS INICIALES",
                f"  {_math(f'{original_prefix}(x) = {original_expr}')}",
                f"  {_math(LABEL_FP + ' = ' + derivative_expr)}",
                f"  Intervalo = {_math_interval(_fmt(step['xl']), _fmt(step['xu']))}",
                f"  {_math_value(label_fp_xl, step['f_xl'])}",
                f"  {_math_value(label_fp_xu, step['f_xu'])}",
                f"  {_math_value(label_fp_xl + ' ' + label_fp_xr, step['f_xl'] * step['f_xu'])}",
                f"  {_math('e_s = ' + str(step['es']) + r'\%')}   "
                f"{_math('i_{max} = ' + str(step['imax']))}",
                "",
            ])
        elif step.get("type") == "iteration":
            decision = "x* exacto" if step["action"] == "raiz_exacta" else step["action"]
            xl_new = step.get("xl_new", step["xl"])
            xu_new = step.get("xu_new", step["xu"])
            xr_formula = (
                r"x_r = \frac{x_l + x_u}{2} = \frac{"
                + f"{_fmt(step['xl'])} + {_fmt(step['xu'])}"
                + r"}{2} = "
                + _fmt(step['xr'])
            )
            test_formula = (
                "test = " + label_fp_xl + " " + label_fp_xr + " = "
                + f"\\left({_fmt(step['f_xl'])}\\right)\\left({_fmt(step['f_xr'])}\\right) = "
                + _fmt(step['test'])
            )
            ea_formula = (
                r"e_a = \left|\frac{" + _fmt(step['xr']) + " - " + _fmt(step['xrold'])
                + "}{" + _fmt(step['xr']) + r"}\right| 100\% = " + _fmt(step['ea']) + r"\%"
            )
            lines.extend([
                "─" * 60,
                f"ITERACIÓN {step['iter']}",
                f"  {_math(xr_formula)}",
                f"  {_math_value('x_{r,ant}', step['xrold'])}",
                f"  {_math_value(label_fp_xl, step['f_xl'])}",
                f"  {_math_value(label_fp_xr, step['f_xr'])}",
                f"  {_math(test_formula)}",
                f"  Decisión: {_math(decision)}",
                f"  Nuevo intervalo: {_math_interval(_fmt(xl_new), _fmt(xu_new))}",
                f"  {_math(ea_formula)}",
                "",
            ])
        elif step.get("type") == "final":
            lines.extend([
                "═" * 60,
                "RESULTADO FINAL",
                f"  {_math('x^* \\approx ' + _fmt(step['root']))}",
                f"  Iteraciones = {_math(str(step['iterations']))}",
                f"  {_math('e_a')} final = {_math(_math_percent(step['error']))}",
                f"  {_math(original_point)} = {_math(_fmt(solution.get('original_value')))}",
                f"  {_math(LABEL_FP_STAR)} = {_math(_fmt(solution['f_value']))}",
                f"  {_math(LABEL_FPP_STAR)} = {_math(_fmt(solution.get('second_derivative')))}",
                f"  Clasificación: {_latex_prose(solution.get('critical_type', 'inconcluso'))}",
                f"  {_latex_prose(solution.get('classification', ''))}",
            ])
    return "\n".join(lines)


def _newton_steps_text(history, second_fn, result, latex):
    original_prefix = "F" if result.get("original_is_antiderivative") else "f"
    original_point = f"{original_prefix}(x^*)"
    original_expr = latex["original"]
    derivative_expr = latex["derivative"]
    second_expr = latex["second_derivative"]
    formula_newton = r"x_{k+1} = x_k - \frac{f'(x_k)}{f''(x_k)}"
    formula_ea = r"e_a = \left|\frac{x_{k+1} - x_k}{x_{k+1}}\right| 100\%"
    lines = [
        f"PROCEDIMIENTO — NEWTON SOBRE {_math(LABEL_FP)}",
        _math(f"{original_prefix}(x) = {original_expr}"),
        _math(f"f'(x) = {derivative_expr}"),
        _math(f"f''(x) = {second_expr}"),
        f"Objetivo: resolver {_math(LABEL_FP + ' = 0')}.",
        "",
        "Fórmula:",
        f"  {_math(formula_newton)}",
        "",
        "Error relativo:",
        f"  {_math(formula_ea)}",
        "",
    ]
    for index in range(len(history) - 1):
        actual = history[index]
        siguiente = history[index + 1]
        xk = actual["x"]
        fpk = actual["fx"]
        xnext = siguiente["x"]
        second = second_fn(xk)
        label_xk = f"x_{{{index}}}"
        label_xnext = f"x_{{{index + 1}}}"
        label_fpk = f"f'({label_xk})"
        label_fppk = f"f''({label_xk})"
        lines.extend([
            "─" * 60,
            f"ITERACIÓN {index + 1}",
            f"  {_math_value(label_xk, xk)}",
            f"  {_math_value(label_fpk, fpk)}",
        ])
        if second is not None:
            iteration_formula = (
                f"{label_xnext} = {label_xk} - "
                + f"\\frac{{f'({label_xk})}}{{f''({label_xk})}}"
            )
            substitution = (
                f"= {_fmt(xk)} - \\frac{{{_fmt(fpk)}}}{{{_fmt(second)}}}"
            )
            lines.extend([
                f"  {_math_value(label_fppk, second)}",
                f"  {_math(iteration_formula)}",
                f"           {_math(substitution)}",
                f"           {_math('= ' + _fmt(xnext))}",
            ])
        else:
            lines.append(f"  {_math_value(label_xnext, xnext)}")
        if siguiente["error"] is not None:
            lines.append(f"  {_math('e_a')} = {_math(_math_percent(siguiente['error']))}")
        lines.append("")

    final = history[-1]
    lines.extend([
        "═" * 60,
        "RESULTADO FINAL",
        f"  {_math('x^* \\approx ' + _fmt(final['x']))}",
        f"  {_math(original_point)} = {_math(_fmt(result.get('original_value')))}",
        f"  {_math(LABEL_FP_STAR)} = {_math(_fmt(final['fx']))}",
        f"  {_math(LABEL_FPP_STAR)} = {_math(_fmt(result.get('second_derivative')))}",
        f"  Clasificación: {_latex_prose(result.get('critical_type', 'inconcluso'))}",
        f"  {_latex_prose(result.get('classification', ''))}",
    ])
    return "\n".join(lines)


def _secant_steps_text(history, result, latex):
    original_prefix = "F" if result.get("original_is_antiderivative") else "f"
    original_point = f"{original_prefix}(x^*)"
    original_expr = latex["original"]
    derivative_expr = latex["derivative"]
    second_expr = latex["second_derivative"]
    label_prev = "x_{k-1}"
    label_curr = "x_k"
    label_next = "x_{k+1}"
    label_fp_prev = "f'(x_{k-1})"
    label_fp_curr = "f'(x_k)"
    formula_secant = (
        r"x_{k+1} = x_k - f'(x_k)"
        r"\frac{x_k - x_{k-1}}{f'(x_k) - f'(x_{k-1})}"
    )
    formula_ea = r"e_a = \left|\frac{x_{k+1} - x_k}{x_{k+1}}\right| 100\%"
    lines = [
        f"PROCEDIMIENTO — SECANTE SOBRE {_math(LABEL_FP)}",
        _math(f"{original_prefix}(x) = {original_expr}"),
        _math(f"f'(x) = {derivative_expr}"),
        _math(f"f''(x) = {second_expr}"),
        f"Objetivo: resolver {_math(LABEL_FP + ' = 0')} sin calcular {_math(LABEL_FPP)}.",
        "",
        "Fórmula:",
        f"  {_math(formula_secant)}",
        "",
        "Error relativo:",
        f"  {_math(formula_ea)}",
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
            iteration_formula = (
                f"{label_next} = {label_curr} - {label_fp_curr}"
                f"\\frac{{{label_curr} - {label_prev}}}{{{label_fp_curr} - {label_fp_prev}}}"
            )
            substitution = (
                f"= {_fmt(x_curr)} - ({_fmt(f_curr)})\\cdot"
                f"\\frac{{{_fmt(x_curr)} - {_fmt(x_prev)}}}{{{_fmt(f_curr)} - {_fmt(f_prev)}}}"
            )
            reduced = (
                f"= {_fmt(x_curr)} - ({_fmt(f_curr)})\\cdot"
                f"\\frac{{{_fmt(x_curr - x_prev)}}}{{{_fmt(denominator)}}}"
            )
            lines.extend([
                "─" * 60,
                f"ITERACIÓN {nxt['iter']}",
                f"  {_math_value(label_prev, x_prev)}   {_math_value(label_fp_prev, f_prev)}",
                f"  {_math_value(label_curr, x_curr)}   {_math_value(label_fp_curr, f_curr)}",
                f"  {_math(iteration_formula)}",
                f"         {_math(substitution)}",
                f"         {_math(reduced)}",
                f"         {_math('= ' + _fmt(x_next))}",
            ])
            if nxt["error"] is not None:
                lines.append(f"  {_math('e_a')} = {_math(_math_percent(nxt['error']))}")
            lines.append("")

    final = history[-1]
    lines.extend([
        "═" * 60,
        "RESULTADO FINAL",
        f"  {_math('x^* \\approx ' + _fmt(final['x']))}",
        f"  {_math(original_point)} = {_math(_fmt(result.get('original_value')))}",
        f"  {_math(LABEL_FP_STAR)} = {_math(_fmt(final['fx']))}",
        f"  {_math(LABEL_FPP_STAR)} = {_math(_fmt(result.get('second_derivative')))}",
        f"  Clasificación: {_latex_prose(result.get('critical_type', 'inconcluso'))}",
        f"  {_latex_prose(result.get('classification', ''))}",
    ])
    return "\n".join(lines)


def _error_response(message, method, analysis=None):
    return jsonify({
        "success": False,
        "method": method,
        "error_message": message,
        "analysis": analysis or {
            "processable": False,
            "text": (
                "ANÁLISIS DE LA FUNCIÓN\n"
                "Veredicto: NO PROCESABLE\n"
                f"  - {message}"
            ),
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
        _set_analysis_verdict(analysis, False, reason)
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
        _set_analysis_verdict(analysis, False, reason)
        return _error_response(reason, method, analysis)

    try:
        spec = build_function_spec(expr_str, input_type=input_type)
    except Exception as exc:
        reason = f"No se pudieron calcular las derivadas: {exc}"
        _set_analysis_verdict(analysis, False, reason)
        return _error_response(reason, method, analysis)

    latex = _spec_latex(spec)
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
        classification = _latex_prose(solution.get("classification", ""))
        converged = bool(solution.get("converged"))
        xl_final = _safe_float(solution.get("xl_final"))
        xu_final = _safe_float(solution.get("xu_final"))
        message = ""
        steps_text = _bisection_steps_text(result["steps"], solution, latex)
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
            _set_analysis_verdict(analysis, False, reason)
            return _error_response(reason, method, analysis)
        final_point = history[-1]
        root = _safe_float(final_point["x"])
        iterations = len(history)
        error = _safe_float(final_point["error"])
        f_value = _safe_float(final_point["fx"])
        second_value = _safe_float(result.get("second_derivative"))
        critical_type = result.get("critical_type", "inconcluso")
        classification = _latex_prose(result.get("classification", ""))
        tol_value = float(payload.get("tol", 1e-5))
        converged = (
            (f_value is not None and abs(f_value) <= tol_value)
            or (error is not None and error <= tol_value)
        )
        xl_final = None
        xu_final = None
        message = _latex_prose(result.get("message", ""))
        if method == "newton":
            steps_text = _newton_steps_text(history, second_fn, result, latex)
            table = _newton_table(history, second_fn)
        else:
            steps_text = _secant_steps_text(history, result, latex)
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
        "latex": latex,
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
