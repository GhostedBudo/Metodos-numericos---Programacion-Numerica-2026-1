# EJECUTAR desde la raíz: python -m lib.secante_test

from lib.secante import SecantRoots


def aproxima(a, b, tol=1e-5):
    return abs(a - b) < tol


def run_case(func_str, x0, x1, label, root_esperada):
    print("=" * 70)
    print(f"Prueba Secante: {label}")
    print(f"f(x) = {func_str}")
    print(f"x0 = {x0}, x1 = {x1}")

    solver = SecantRoots(func_str, x0, x1, tol=1e-8, max_iter=100)
    result = solver.solve()

    if not result["success"]:
        print(f"ERROR: {result['error_message']}")
        raise AssertionError(f"Secante falló en {label}")

    print(f"Resultado: {result['solution']:.10f}")
    print(f"Mensaje: {result['message']}")
    assert aproxima(result["solution"], root_esperada), (
        f"{label}: esperado ≈ {root_esperada}, got {result['solution']}"
    )
    assert result["original_expr"], "Falta original_expr"
    assert result["derivative_expr"], "Falta derivative_expr"
    assert result["second_derivative_expr"], "Falta second_derivative_expr"
    assert result["derivative_value"] is not None
    assert result["original_value"] is not None
    assert result["critical_type"] in {"mínimo", "máximo", "inconcluso"}
    return result


def test_secant():
    cases = [
        ("x**2 - 4*x + 1", 0.5, 1.5, "Cuadrática", 2.0),
        ("x**3 - 3*x", 0.5, 1.5, "Cúbica", 1.0),
        ("sin(x) + 0.5*x", 1.5, 2.5, "Trigonométrica", 2.0943951023931953),
        ("(x - 2)**2 - ln(x)", 1.5, 3.0, "Con logaritmo", 2.224744871391589),
    ]

    for func_str, x0, x1, label, root_esperada in cases:
        run_case(func_str, x0, x1, label, root_esperada)

    print("\nTodas las pruebas de Secante completaron correctamente.")


def test_error_sintaxis():
    result = SecantRoots("2*x +", 1.0, 2.0).solve()
    assert result["success"] is False
    assert "sintaxis" in result["error_message"].lower() or "parse" in result["error_message"].lower()
    print("OK test_error_sintaxis")


def test_error_puntos_iguales():
    result = SecantRoots("x**2 - 4*x + 1", 1.0, 1.0).solve()
    assert result["success"] is False
    assert "división por cero" in result["error_message"].lower()
    print("OK test_error_puntos_iguales")


def test_error_funcion_vacia():
    result = SecantRoots("", 1.0, 2.0).solve()
    assert result["success"] is False
    print("OK test_error_funcion_vacia")


if __name__ == "__main__":
    test_secant()
    test_error_sintaxis()
    test_error_puntos_iguales()
    test_error_funcion_vacia()
    print("\nTodas las pruebas de Secante completaron correctamente.")
