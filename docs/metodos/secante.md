# Método de la Secante aplicado a optimización

## Descripción
En optimización se resuelve f'(x) = 0. La secante es similar a
Newton, pero aproxima f''(x) con una diferencia dividida, evitando
calcular la segunda derivada.

## Fórmula
x_{k+1} = x_k - f'(x_k)·(x_k - x_{k-1}) / (f'(x_k) - f'(x_{k-1}))

Requiere dos puntos iniciales x₀ y x₁.

## Parámetros
- `func_str`: str — expresión sympy de f'(x) (ej. "3*x**2 - 3")
- `x0`: float — primera aproximación inicial
- `x1`: float — segunda aproximación inicial
- `tol`: float — tolerancia error relativo % (default 1e-5)
- `max_iter`: int — máximo de iteraciones (default 150)

## Retorno (solve)
```python
{
    "success": bool,
    "solution": float | None,
    "steps": list[dict],
    "message": str,
    "error_message": str | None
}
```

## Ejemplo
Para f(x) = x³ - 3x, la derivada es f'(x) = 3x² - 3.
```python
solver = SecantRoots("3*x**2 - 3", 0.5, 1.5)
result = solver.solve()  # x* ≈ 1, f''(1)=6 > 0 → mínimo
```

## Limitaciones
- Fallo si f'(x_k) - f'(x_{k-1}) = 0 (división por cero)
- Convergencia superlineal (orden ≈ 1.618), no cuadrática como Newton
- Sensible a mala elección de x₀ y x₁
