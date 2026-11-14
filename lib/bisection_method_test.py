"""
Pruebas para la clase BisectionMethod.

La clase recibe la función original f(x), calcula f'(x) y resuelve
f'(x) = 0 dentro de [xl, xu]. Se cubren:
  - Casos de éxito: punto crítico de una cuadrática, punto crítico
    exacto en un extremo, convergencia por tolerancia y salida por
    máximo de iteraciones.
  - Casos de error: sin cambio de signo en f'(x), f(x) no parseable,
    xl >= xu y f(x) vacía.
  - Verificación de la estructura de los pasos (steps) registrados
    para la GUI.

Ejecutar desde la raíz del proyecto:
    .venv/Scripts/python.exe -m lib.bisection_method_test
"""
from lib.bisection_method import BisectionMethod


def aprox_igual(a, b, tol=1e-2):
    """Compara dos valores float con una tolerancia absoluta."""
    return abs(a - b) < tol


def test_raiz_cubica_clasica():
    """
    f(x) = x² - 4x + 1. Su derivada es 2x - 4, que se anula en x* = 2.
    El intervalo [0, 3] tiene cambio de signo en f'.
    """
    res = BisectionMethod("x**2 - 4*x + 1", 0.0, 3.0, es=0.01, imax=100).solve()
    assert res["success"] is True, res.get("error_message")
    sol = res["solution"]
    assert aprox_igual(sol["root"], 2.0), f"Esperado ≈ 2.0, got {sol['root']}"
    assert sol["error"] < 0.01 or abs(sol["f_value"]) <= 0.01, (
        f"Debe parar por ea < 0.01% o f'(xr) <= 0.01, "
        f"got ea={sol['error']}, f'(xr)={sol['f_value']}"
    )
    assert sol["converged"] is True
    assert sol["critical_type"] == "mínimo"
    assert sol["original_expr"] == "x**2 - 4*x + 1"
    assert sol["derivative_expr"] == "2*x - 4"
    print("OK test_raiz_cubica_clasica")


def test_raiz_exacta_en_extremo():
    """
    f(x) = (x - 2)². Su derivada es 2x - 4, que se anula en x = 2.
    Con xl = 2, el punto crítico está exactamente en el extremo.
    """
    res = BisectionMethod("(x - 2)**2", 2.0, 3.0).solve()
    assert res["success"] is True, res.get("error_message")
    sol = res["solution"]
    assert aprox_igual(sol["root"], 2.0, tol=1e-9), f"Esperado 2.0, got {sol['root']}"
    assert sol["iterations"] == 0
    assert sol["error"] == 0.0
    assert sol["converged"] is True
    assert aprox_igual(sol["original_value"], 0.0, tol=1e-9)
    print("OK test_raiz_exacta_en_extremo")


def test_sin_cambio_de_signo():
    """
    f(x) = x³ + x. Su derivada es 3x² + 1, siempre positiva.
    No hay cambio de signo en [0, 1], así que bisección debe fallar.
    """
    res = BisectionMethod("x**3 + x", 0.0, 1.0).solve()
    assert res["success"] is False
    assert "signo" in res["error_message"].lower()
    print("OK test_sin_cambio_de_signo")


def test_salida_por_max_iter():
    """
    f(x) = x² - 4x + 1 con imax=3 y tolerancia muy pequeña.
    Debe detenerse por máximo de iteraciones.
    """
    res = BisectionMethod("x**2 - 4*x + 1", 0.0, 3.0, es=1e-10, imax=3).solve()
    assert res["success"] is True, res.get("error_message")
    sol = res["solution"]
    assert sol["converged"] is False
    assert sol["iterations"] == 3
    print("OK test_salida_por_max_iter")


def test_convergencia_por_tolerancia():
    """Verifica que con es=1e-4 la bisección converja con error < 1e-4."""
    res = BisectionMethod("x**2 - 4*x + 1", 0.0, 3.0, es=1e-4, imax=100).solve()
    assert res["success"] is True, res.get("error_message")
    sol = res["solution"]
    assert sol["error"] < 1e-4 or abs(sol["f_value"]) <= 1e-4, (
        f"ea debe ser < 1e-4 o f'(xr) <= 1e-4, "
        f"got ea={sol['error']}, f'(xr)={sol['f_value']}"
    )
    assert sol["converged"] is True
    print("OK test_convergencia_por_tolerancia")


def test_defaults():
    """Sin especificar es ni imax, usa es=0.01, imax=100 y converge."""
    res = BisectionMethod("x**2 - 4*x + 1", 0.0, 3.0).solve()
    assert res["success"] is True, res.get("error_message")
    sol = res["solution"]
    assert sol["converged"] is True
    assert sol["iterations"] <= 100
    print("OK test_defaults")


def test_error_f_expr_no_parseable():
    """Caso de error: f(x) no se puede interpretar."""
    res = BisectionMethod("2*x +", 0.0, 1.0).solve()
    assert res["success"] is False
    assert "interpretar" in res["error_message"].lower() or "sintaxis" in res["error_message"].lower()
    print("OK test_error_f_expr_no_parseable")


def test_error_xl_mayor_xu():
    """Caso de error: xl >= xu (intervalo invertido o degenerado)."""
    res = BisectionMethod("x**2 - 4*x + 1", 2.0, 1.0).solve()
    assert res["success"] is False
    assert "menor" in res["error_message"].lower()
    print("OK test_error_xl_mayor_xu")


def test_entrada_derivada():
    """Si el usuario escribe f'(x), se integra para mostrar F(x) (C=0)."""
    res = BisectionMethod(
        "3*x**2 - 3", 0.0, 1.5, input_type="derivative").solve()
    assert res["success"] is True, res.get("error_message")
    sol = res["solution"]
    assert aprox_igual(sol["root"], 1.0)
    assert sol["input_type"] == "derivative"
    assert sol["original_is_antiderivative"] is True
    assert sol["original_expr"] == "x**3 - 3*x"
    assert aprox_igual(sol["original_value"], -2.0)
    print("OK test_entrada_derivada")


def test_error_f_expr_vacia():
    """Caso de error: f(x) vacía o None."""
    res1 = BisectionMethod("", 0.0, 1.0).solve()
    assert res1["success"] is False
    assert "función" in res1["error_message"].lower()
    res2 = BisectionMethod(None, 0.0, 1.0).solve()
    assert res2["success"] is False
    print("OK test_error_f_expr_vacia")


def test_pasos_generados():
    """Verifica los tipos de steps y su número de iteraciones."""
    res = BisectionMethod("x**2 - 4*x + 1", 0.0, 3.0, es=0.01, imax=100).solve()
    assert res["success"] is True
    tipos = {p["type"] for p in res["steps"]}
    esperados = {"initial", "iteration", "final"}
    assert esperados.issubset(tipos), f"Faltan tipos: {esperados - tipos}"
    n_iter_steps = sum(1 for p in res["steps"] if p["type"] == "iteration")
    assert n_iter_steps == res["solution"]["iterations"], (
        f"Esperaba {res['solution']['iterations']} iter steps, got {n_iter_steps}"
    )
    print("OK test_pasos_generados")


def test_contenido_step_iteracion():
    """Verifica las claves requeridas en cada step de iteración."""
    res = BisectionMethod("x**2 - 4*x + 1", 0.0, 3.0, es=0.01, imax=5).solve()
    assert res["success"] is True
    claves_esperadas = {"iter", "xl", "xu", "xr", "xrold", "ea", "test", "action"}
    for p in res["steps"]:
        if p["type"] == "iteration":
            claves = set(p.keys())
            assert claves_esperadas.issubset(claves), (
                f"Step incompleto: faltan {claves_esperadas - claves}"
            )
    print("OK test_contenido_step_iteracion")


if __name__ == "__main__":
    test_raiz_cubica_clasica()
    test_raiz_exacta_en_extremo()
    test_sin_cambio_de_signo()
    test_salida_por_max_iter()
    test_convergencia_por_tolerancia()
    test_defaults()
    test_error_f_expr_no_parseable()
    test_error_xl_mayor_xu()
    test_entrada_derivada()
    test_error_f_expr_vacia()
    test_pasos_generados()
    test_contenido_step_iteracion()
    print("\nTodos los tests pasaron.")
