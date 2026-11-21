"""Comprobaciones del análisis de función en la API web."""
from webapp.app import app


def _solve(payload):
    with app.test_client() as client:
        return client.post("/api/solve", json=payload).get_json()


def _assert_verdict(data, verdict):
    lines = data["analysis"]["text"].splitlines()
    assert lines[0] == "ANÁLISIS DE LA FUNCIÓN"
    assert lines[1] == f"Veredicto: {verdict}"


def test_funcion_procesable():
    data = _solve({
        "method": "newton",
        "expr": "x**3 - 3*x",
        "input_type": "function",
        "x0": "0.5",
        "tol": "1e-5",
        "max_iter": "150",
        "xmin": "-2",
        "xmax": "2",
    })
    assert data["success"] is True
    assert data["analysis"]["processable"] is True
    _assert_verdict(data, "PROCESABLE")
    assert "Dominio real de f(x)" in data["analysis"]["text"]
    assert "x" in data["analysis"]["latex"]["derivative"]
    assert data["latex"]["derivative"] == data["analysis"]["latex"]["derivative"]


def test_funcion_fuera_de_dominio():
    data = _solve({
        "method": "newton",
        "expr": "log(x)",
        "input_type": "function",
        "x0": "-1",
        "tol": "1e-5",
        "max_iter": "50",
    })
    assert data["success"] is False
    assert data["analysis"]["processable"] is False
    _assert_verdict(data, "NO PROCESABLE")
    assert "NO PROCESABLE" in data["analysis"]["text"]


def test_sin_cambio_de_signo():
    data = _solve({
        "method": "bisection",
        "expr": "x**2",
        "input_type": "function",
        "xl": "1",
        "xu": "2",
        "es": "0.01",
        "imax": "20",
    })
    assert data["success"] is False
    assert data["analysis"]["processable"] is False
    _assert_verdict(data, "NO PROCESABLE")
    assert "NO PROCESABLE" in data["analysis"]["text"]


def test_funcion_no_diferenciable():
    data = _solve({
        "method": "newton",
        "expr": "Abs(x)",
        "input_type": "function",
        "x0": "0.5",
        "tol": "1e-5",
        "max_iter": "50",
    })
    assert data["success"] is False
    assert data["analysis"]["processable"] is False
    assert "NO PROCESABLE" in data["analysis"]["text"]


def test_datos_numericos_invalidos():
    data = _solve({
        "method": "bisection",
        "expr": "x**2",
        "input_type": "function",
        "xl": "abc",
        "xu": "2",
        "es": "0.01",
        "imax": "20",
    })
    assert data["success"] is False
    assert data["analysis"]["processable"] is False
    assert "Datos numéricos inválidos" in data["analysis"]["text"]


def test_pestana_analisis_antes_de_resultado():
    with app.test_client() as client:
        html = client.get("/").get_data(as_text=True)
    assert 'id="analysisText"' in html
    assert html.index('data-tab="analysis"') < html.index('data-tab="summary"')
    assert 'id="b_expr"' in html
    assert "mathlive.min.js" in html


def test_entrada_derivada():
    data = _solve({
        "method": "bisection",
        "expr": "2*x - 4",
        "input_type": "derivative",
        "xl": "1",
        "xu": "3",
        "es": "0.01",
        "imax": "50",
    })
    assert data["success"] is True
    assert data["analysis"]["processable"] is True
    assert "F(x) integrada con C = 0" in data["analysis"]["text"]


if __name__ == "__main__":
    test_funcion_procesable()
    test_funcion_fuera_de_dominio()
    test_sin_cambio_de_signo()
    test_funcion_no_diferenciable()
    test_datos_numericos_invalidos()
    test_pestana_analisis_antes_de_resultado()
    test_entrada_derivada()
    print("Pruebas de análisis web: OK")
