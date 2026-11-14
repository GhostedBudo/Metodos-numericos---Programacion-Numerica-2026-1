"""Glosario compartido por las tres vistas de optimización."""

GLOSSARY_TEXT = """GLOSARIO — OPTIMIZACIÓN CON f(x) Y f'(x)

TIPOS DE ENTRADA
  El selector permite escribir uno de los dos:

  f(x)   = función original. El sistema calcula f'(x) y f''(x).
  f'(x)  = primera derivada. El sistema calcula f''(x) e integra
           F(x) con C=0 para poder mostrarla en la gráfica.
           F(x) es una antiderivada, no la f(x) exacta.

SÍMBOLOS
  xl   = límite inferior del intervalo. Punto izquierdo.
  xu   = límite superior del intervalo. Punto derecho.
  xr   = punto medio (xl + xu)/2. Aproximación del punto crítico.
  x_i  = aproximación actual dentro de Newton o Secante.
  x*   = punto crítico final donde f'(x*) ≈ 0.
  Iter = número de iteración.
  ea   = error relativo porcentual. Más pequeño es mejor.

DERIVADAS
  f'(x)   = primera derivada calculada desde f(x). Al resolver
            f'(x)=0 se buscan mínimos o máximos de f(x).
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
  Curva verde = f(x), la función original.
  Curva azul = f'(x), calculada automáticamente.
  En el selector Ambas se usa doble eje Y:
      eje izquierdo = f(x), eje derecho = f'(x).
  Línea negra o punteada = f'(x) = 0, donde buscamos el corte.
  Puntos naranjas = aproximaciones de cada iteración.
  Estrella verde = x* final sobre la curva seleccionada.
  Zona sombreada = intervalo inicial [xl, xu] (solo Bisección).
  Vista 3D = dos superficies separadas: verde para f(x) y azul
             para f'(x). La superficie transparente representa
             f'(x) = 0 y la línea naranja son las iteraciones.
"""
