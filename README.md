# Calculadora de calefacción

Web hermana de [CalorBrasa](https://calorbrasa.github.io/): calcula cuánto cuesta calentar una casa con estufas de pellets, leña, butano o eléctricas, y cuánto se ahorra dejando el gasóleo.

- Publicada en GitHub Pages: https://calculadora-calefaccion.github.io/
- La calculadora está en `index.html` (HTML, CSS y JS en un solo archivo).
- Lee el catálogo en vivo de https://calorbrasa.github.io/data/products.json (con copia de respaldo dentro de la página).
- Precios de energía por defecto: constante `DEF` en `index.html`. Revisarlos cada mes (el butano cambia cada 2 meses, el tercer martes de los meses impares).
- Enlaces a otras webs hermanas: constante `WEBS` en `index.html`. Mientras valgan `"#"`, esos enlaces se ocultan.

## Páginas «¿Cuánto gasta una estufa de…?» y guías

- `cuanto-gasta-estufa-butano.html`
- `cuanto-gasta-estufa-electrica.html`
- `cuanto-gasta-estufa-pellets.html`
- `cuanto-gasta-estufa-lena.html`

Y tres guías más: `calculadora-potencia-estufa.html`, `que-calefaccion-es-mas-barata.html` y `es-peligrosa-estufa-butano.html` (los precios del gas natural de la TUR están en `GAS_TUR_LOW`/`GAS_TUR_HIGH` del script; revísalos en cada cambio trimestral de la TUR).

Se generan con `python3 _generar_paginas.py` (lee los precios de `DEF` en `index.html` y el catálogo de CalorBrasa) y también reescriben `sitemap.xml`. **Cada vez que cambien los precios en `index.html`, vuelve a ejecutar el script** y sube los archivos generados. Los archivos que empiezan por `_` no se publican en GitHub Pages.
