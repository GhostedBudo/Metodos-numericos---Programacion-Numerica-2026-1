# EJECUTAR desde la raíz: python -m lib.newton_raphson_test

from lib.newton_raphson import NewtonRoots


def aproxima(a, b, tol=1e-5):
    return abs(a - b) < tol


def run_case(func_str, x0, label, root_esperada):
    print("=" * 70)
    print(f"Prueba Newton-Raphson: {label}")
    print(f"f(x) = {func_str}")
    print(f"x0 = {x0}")

    solver = NewtonRoots(func_str, x0, tol=1e-8, max_iter=100)
    result = solver.solve()

    if not result["success"]:
        print(f"ERROR: {result['error_message']}")
        raise AssertionError(f"Newton-Raphson falló en {label}")

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


def test_newton():
    cases = [
        ("x**2 - 4*x + 1", 0.5, "Cuadrática", 2.0),
        ("x**3 - 3*x", 0.5, "Cúbica", 1.0),
        ("sin(x) + 0.5*x", 2.0, "Trigonométrica", 2.0943951023931953),
        ("(x - 2)**2 - ln(x)", 1.5, "Con logaritmo", 2.224744871391589),
    ]

    for func_str, x0, label, root_esperada in cases:
        run_case(func_str, x0, label, root_esperada)

    print("\nTodas las pruebas de Newton-Raphson completaron correctamente.")


def test_error_sintaxis():
    result = NewtonRoots("2*x +", 1.0).solve()
    assert result["success"] is False
    assert "sintaxis" in result["error_message"].lower() or "parse" in result["error_message"].lower()
    print("OK test_error_sintaxis")


def test_error_segunda_derivada_cero():
    result = NewtonRoots("x**3 + x + 1", 0.0).solve()
    assert result["success"] is False
    assert "segunda derivada" in result["error_message"].lower()
    print("OK test_error_segunda_derivada_cero")


if __name__ == "__main__":
    test_newton()
    test_error_sintaxis()
    test_error_segunda_derivada_cero()
    print("\nTodas las pruebas de Newton-Raphson completaron correctamente.")
