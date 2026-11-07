# Método de Bisección aplicado a optimización

## Descripción
En optimización se busca un punto crítico x* donde f'(x*) = 0.
La bisección divide repetidamente un intervalo [xl, xu] por la mitad,
seleccionando el subintervalo donde f'(x) cambia de signo.

## Algoritmo
1. Verificar f'(xl)·f'(xu) < 0 (cambio de signo)
2. xr = (xl + xu) / 2
3. Evaluar test = f'(xl)·f'(xr)
   - test < 0: punto crítico en [xl, xr] → xu = xr
   - test > 0: punto crítico en [xr, xu] → xl = xr
   - test = 0: punto crítico exacto encontrado
4. Calcular error relativo: ea = |(xr - xrold)/xr|·100%
5. Repetir hasta ea < es o iter ≥ imax
6. Clasificar con f''(x*): >0 mínimo, <0 máximo, ≈0 inconcluso

## Parámetros
- `f_expr`: str — expresión sympy de f'(x) (ej. "3*x**2 - 3")
- `xl`: float — extremo inferior del intervalo
- `xu`: float — extremo superior del intervalo (xl < xu)
- `es`: float — tolerancia error relativo % (default 0.01)
- `imax`: int — máximo de iteraciones (default 100)

## Retorno (solve)
```python
{
    "success": bool,
    "solution": {
        "root": float,
        "iterations": int,
        "error": float,
        "converged": bool,
        "f_value": float,
        "xl_final": float,
        "xu_final": float
    } | None,
    "steps": list[dict],
    "error_message": str | None
}
```

## Ejemplo
Para f(x) = x³ - 3x, la derivada es f'(x) = 3x² - 3.
```python
solver = BisectionMethod("3*x**2 - 3", 0.0, 1.5, es=0.01)
result = solver.solve()  # x* ≈ 1, f''(1)=6 > 0 → mínimo
```

## Limitaciones
- Requiere cambio de signo de f' en el intervalo
- Convergencia lineal (lenta comparada con Newton/Secante)
- No detecta puntos críticos donde f' es tangente al eje x
