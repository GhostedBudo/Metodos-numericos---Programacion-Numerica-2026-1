# Newton-Raphson aplicado a optimización

## Descripción
En optimización se resuelve f'(x) = 0. Newton usa también f''(x)
para converger cuadráticamente cerca del punto crítico.
El programa recibe f'(x) y calcula f''(x) automáticamente con sympy.

## Fórmula
x_{k+1} = x_k - f'(x_k) / f''(x_k)

## Parámetros
- `func_str`: str — expresión sympy de f'(x) (ej. "3*x**2 - 3")
- `x0`: float — aproximación inicial
- `tol`: float — tolerancia error relativo % (default 1e-5)
- `max_iter`: int — máximo de iteraciones (default 150)

## Retorno (solve)
```python
{
    "success": bool,
    "solution": float | None,
    "steps": list[dict],  # historial de iteraciones
    "message": str,
    "error_message": str | None
}
```

## Ejemplo
Para f(x) = x³ - 3x, la derivada es f'(x) = 3x² - 3.
```python
solver = NewtonRoots("3*x**2 - 3", 0.5)
result = solver.solve()  # x* ≈ 1, f''(1)=6 > 0 → mínimo
```

## Limitaciones
- Requiere que f''(x) exista y no sea cero en el iterado
- Fallo si f''(x_k) = 0 (división por cero)
- Puede divergir si x₀ está lejos del punto crítico
- No maneja puntos críticos múltiples (convergencia lineal)
