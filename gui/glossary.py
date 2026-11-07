"""Glosario compartido por las tres vistas de optimización."""

GLOSSARY_TEXT = """GLOSARIO — OPTIMIZACIÓN CON f'(x) = 0

SÍMBOLOS
  xl   = límite inferior del intervalo. Punto izquierdo.
  xu   = límite superior del intervalo. Punto derecho.
  xr   = punto medio (xl + xu)/2. Aproximación del punto crítico.
  x_i  = aproximación actual dentro de Newton o Secante.
  x*   = punto crítico final donde f'(x*) ≈ 0.
  Iter = número de iteración.
  ea   = error relativo porcentual. Más pequeño es mejor.

DERIVADAS
  f'(x)   = primera derivada. Al resolver f'(x)=0 se buscan
            mínimos o máximos de la función original f(x).
  f''(x*) = segunda derivada evaluada en x*.
            f''(x*) > 0  → mínimo local.
            f''(x*) < 0  → máximo local.
            f''(x*) ≈ 0  → el criterio no decide.

ABREVIATURAS DE LAS TABLAS
  fp  = f'(x)
  fpp = f''(x)

BISECCIÓN
  test = f'(xl) * f'(xr).
  Si test < 0, el punto crítico está entre xl y xr:
      xu = xr.
  Si test > 0, el punto crítico está entre xr y xu:
      xl = xr.
  Si test = 0, se encontró el punto crítico exacto.

CÓMO LEER LA GRÁFICA
  Eje x = valores de x.
  Eje y = valores de f'(x).
  Curva azul = f'(x).
  Línea negra o punteada = y = 0, donde buscamos el corte.
  Puntos naranjas = aproximaciones de cada iteración.
  Estrella verde = x* final.
  Zona sombreada = intervalo inicial [xl, xu] (solo Bisección).
  Vista 3D = superficie de f'(x) extendida; la curva naranja
             son las iteraciones sobre el centro y la superficie
             transparente representa f'(x) = 0.
"""
