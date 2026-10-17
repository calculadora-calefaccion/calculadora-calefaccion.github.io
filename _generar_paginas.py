#!/usr/bin/env python3
"""Genera las páginas "¿Cuánto gasta una estufa de ...?" de la calculadora.

Uso:  python3 _generar_paginas.py [ruta/a/products.json]

- Los precios se leen de la constante DEF de index.html (una sola fuente).
- El catálogo se lee de products.json de CalorBrasa (por defecto, desde la web).
- Vuelve a ejecutarlo cada vez que cambien los precios en index.html.
Los archivos que empiezan por "_" no se publican en GitHub Pages.
"""
import html
import math
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://calculadora-calefaccion.github.io/"
CB = "https://calorbrasa.github.io/"
UPDATED_ISO = "2026-10-18"
UPDATED_TXT = "octubre de 2026"
PRICES_TXT = "septiembre de 2026"
BUTANO_NEXT = "17 de noviembre de 2026"
MONTHS = 5  # meses de invierno (noviembre a marzo)

# ---------------------------------------------------------------- datos
index_src = (ROOT / "index.html").read_text(encoding="utf-8")
m = re.search(r"const DEF = \{([^}]*)\}", index_src)
P = {k: float(v) for k, v in re.findall(r"(\w+):\s*([\d.]+)", m.group(1))}
CSS = re.search(r"<style>.*?</style>", index_src, re.S).group(0)

src = sys.argv[1] if len(sys.argv) > 1 else CB + "data/products.json"
if src.startswith("http"):
    with urllib.request.urlopen(src) as r:
        PRODUCTS = json.load(r)
else:
    PRODUCTS = json.loads(Path(src).read_text(encoding="utf-8"))

PCI = {"pellet": 4.8, "lena": 3.8, "butano": 12.7, "gasoleo": 10.0}
EFF = {"pellet": 0.85, "lena": 0.70, "butano": 1.0, "luz": 1.0, "gasoleo": 0.85, "chimenea": 0.20}
LUZ = P["nose"]


def cpk(fuel, luz=LUZ):
    """€ por kWh de calor útil."""
    if fuel == "luz":
        return luz / EFF["luz"]
    if fuel == "pellet":
        return (P["saco"] / 15) / (PCI["pellet"] * EFF["pellet"])
    if fuel == "lena":
        return P["lena"] / (PCI["lena"] * EFF["lena"])
    if fuel == "chimenea":
        return P["lena"] / (PCI["lena"] * EFF["chimenea"])
    if fuel == "butano":
        return (P["bombona"] / 12.5) / (PCI["butano"] * EFF["butano"])
    if fuel == "gasoleo":
        return P["gasoleo"] / (PCI["gasoleo"] * EFF["gasoleo"])


def nf(v, d=0):
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def eur(v, d=None):
    if d is None:
        d = 2 if v < 10 else 0
    return nf(v, d) + " €"


def rnd(v):
    return round(v / 10) * 10 if v >= 100 else round(v) if v >= 10 else round(v, 1)


def esc(s):
    return html.escape(str(s), quote=True)


def score(p):
    r, rc = p.get("valoracion_media") or 0, p.get("resenas_cantidad") or 0
    return (r * rc + 4.3 * 15) / (rc + 15)


def top_products(cats, n=8, exclude=()):
    items = [p for p in PRODUCTS if p["category"] in cats and not any(x in p["id"] for x in exclude)]
    return sorted(items, key=score, reverse=True)[:n]


# kg o kWh por hora para un aparato de potencia nominal kw, a carga load
def kg_h(fuel, kw, load):
    return kw * load / (PCI[fuel] * EFF[fuel])


CAT_URL = {
    "pellets": CB + "categoria/estufas-de-pellets.html",
    "lena-biomasa": CB + "categoria/estufas-de-lena.html",
    "electricos": CB + "categoria/calefactores-electricos.html",
    "gas": CB + "categoria/calefactores-de-gas.html",
    "radiadores": CB + "categoria/radiadores-electricos.html",
}
PROD_URL = lambda i: CB + "producto/" + i + ".html"

# ---------------------------------------------------------------- valores clave
c_pel, c_len, c_but, c_luz, c_gas, c_chi = (cpk(f) for f in ("pellet", "lena", "butano", "luz", "gasoleo", "chimenea"))

# Butano 4,2 kW
B_KW = 4.2
b_h_norm = B_KW * 0.6 * c_but
b_h_full = B_KW * c_but
bomb_kwh = 12.5 * PCI["butano"]
b_dur_full = bomb_kwh / B_KW
b_dur_norm = bomb_kwh / (B_KW * 0.6)
b_dur_soft = bomb_kwh / (B_KW * 0.35)
b_month_h = 5 * 30
b_bomb_month = b_month_h / b_dur_norm
b_month = b_bomb_month * P["bombona"]
b_water = B_KW * 0.6 / PCI["butano"] * 1.55  # litros de agua por hora

# Eléctrica 2.000 W
e_h_full = 2 * LUZ
e_h_norm = 2 * 0.6 * LUZ
e_month = e_h_norm * 5 * 30

# Pellets 8 kW
p_kgh = kg_h("pellet", 8, 0.6)
p_kgh_full = kg_h("pellet", 8, 1)
p_day_kg = p_kgh * 6
p_day = p_day_kg * P["saco"] / 15
p_month_sacos = p_day_kg * 30 / 15
p_month = p_day * 30
p_season_sacos = p_month_sacos * MONTHS

# Leña 8 kW
l_kgh = kg_h("lena", 8, 0.6)
l_h = l_kgh * P["lena"]
l_day_kg = l_kgh * 6
l_day = l_day_kg * P["lena"]
l_month = l_day * 30
l_season_kg = l_day_kg * 30 * MONTHS


def comparison_rows(highlight):
    rows = [
        ("pellet", "Estufa de pellets", "85 %", CAT_URL["pellets"]),
        ("lena", "Estufa de leña", "70 %", CAT_URL["lena-biomasa"]),
        ("butano", "Estufa de butano", "100 %", CAT_URL["gas"]),
        ("gasoleo", "Caldera de gasóleo", "85 %", None),
        ("luz", "Estufa o radiador eléctrico", "100 %", CAT_URL["electricos"]),
        ("chimenea", "Chimenea abierta de leña", "20 %", None),
    ]
    rows = sorted(rows, key=lambda r: cpk(r[0]))
    out = []
    for fuel, name, eff, url in rows:
        c = cpk(fuel)
        cls = ' class="me"' if fuel == highlight else ""
        nm = f'<a href="{url}">{name}</a>' if url else name
        out.append(f"<tr{cls}><td>{nm}</td><td>{eff}</td><td><b>{nf(c * 100, 1)} cts</b></td><td>{eur(c * 1000, 0)}</td></tr>")
    return "\n".join(out)


COMPARISON_NOTE = (f"Precios de {PRICES_TXT}: luz a {nf(LUZ, 2)} €/kWh, bombona de butano a {eur(P['bombona'], 2)}, "
                   f"saco de pellets de 15 kg a {eur(P['saco'], 2)}, leña seca a {nf(P['lena'], 2)} €/kg y gasóleo a {nf(P['gasoleo'], 2)} €/litro. "
                   f"1.000 kWh es más o menos el calor que gasta un piso de 80 m² en un mes de frío.")

# ---------------------------------------------------------------- páginas
PAGES = {}

# ---------- BUTANO
gas_top = top_products({"gas"}, 8, exclude=("outsunny", "evocamp"))
PAGES["butano"] = dict(
    slug="cuanto-gasta-estufa-butano",
    nav="Butano",
    title="¿Cuánto gasta una estufa de butano? Por hora, día y mes (2026)",
    desc=(f"Una estufa de butano de 4,2 kW gasta unos {eur(b_h_norm, 2)} por hora a potencia media y una bombona dura unas "
          f"{nf(b_dur_norm)} horas. Calcula tu gasto con el precio de la bombona de 2026."),
    h1="¿Cuánto gasta una estufa de butano?",
    lead="Por hora, al día y al mes, cuánto dura una bombona y si te sale más barata que una estufa eléctrica, con el precio de la bombona de 2026.",
    answer=(f"Una estufa de butano de <b>4.200 W</b> gasta unos <b>{eur(b_h_norm, 2)} por hora</b> a potencia media "
            f"(unos {eur(b_h_full, 2)} a tope). Una bombona de 12,5 kg ({eur(P['bombona'], 2)}) dura unas <b>{nf(b_dur_norm)} horas</b> "
            f"a potencia media. Si la usas 5 horas al día, son unas {nf(b_bomb_month, 1)} bombonas al mes: <b>≈ {eur(rnd(b_month), 0)} al mes</b>."),
    cat="gas",
    cfg=dict(fuel="butano", unit="kW", opts=[1.7, 3, 3.8, 4.2], def_=4.2, hours=5, priceKey="bombona",
             priceLabel="Precio de la bombona de 12,5 kg", priceUnit="€", priceStep=0.01,
             hint="La mayoría de estufas de butano tienen 4,2 kW (4.200 W)."),
)

# ---------- ELÉCTRICA
el_top = top_products({"electricos"}, 8)
PAGES["electrica"] = dict(
    slug="cuanto-gasta-estufa-electrica",
    nav="Eléctrica",
    title="¿Cuánto gasta una estufa eléctrica? 2.000, 1.500 y 800 W (2026)",
    desc=(f"Una estufa eléctrica de 2.000 W gasta {eur(e_h_full, 2)} por hora a tope y unos {eur(e_h_norm, 2)} con termostato: "
          f"≈ {eur(rnd(e_month), 0)} al mes usándola 5 horas al día. Calcula la tuya con el precio de la luz de 2026."),
    h1="¿Cuánto gasta una estufa eléctrica?",
    lead="Lo que gasta una estufa o un radiador eléctrico de 800, 1.500 o 2.000 W por hora, al día y al mes, y cómo pagar menos con el precio de la luz de 2026.",
    answer=(f"Una estufa eléctrica de <b>2.000 W</b> gasta <b>{eur(e_h_full, 2)} por hora</b> a máxima potencia con la luz a "
            f"{nf(LUZ, 2)} €/kWh, y unos <b>{eur(e_h_norm, 2)} por hora</b> con el termostato puesto (trabaja más o menos el 60 % del tiempo). "
            f"Usándola 5 horas al día son unos <b>{eur(rnd(e_month), 0)} al mes</b>. Una de 800 W gasta {eur(0.8 * LUZ, 2)} por hora a tope."),
    cat="electricos",
    cfg=dict(fuel="luz", unit="W", opts=[800, 1000, 1500, 2000, 2500], def_=2000, hours=5, priceKey="nose",
             priceLabel="Precio de la luz", priceUnit="€/kWh", priceStep=0.01,
             hint="La potencia viene en la etiqueta o en la caja, en vatios (W)."),
)

# ---------- PELLETS
pel_top = top_products({"pellets"}, 8)
PAGES["pellets"] = dict(
    slug="cuanto-gasta-estufa-pellets",
    nav="Pellets",
    title="¿Cuánto gasta una estufa de pellets? Al día, al mes y por invierno",
    desc=(f"Una estufa de pellets de 8 kW quema unos {nf(p_kgh, 1)} kg por hora a potencia media: ≈ {eur(p_day, 2)} al día "
          f"(6 h) y {nf(p_month_sacos)} sacos al mes. Calcula la tuya con el precio del saco de 2026."),
    h1="¿Cuánto gasta una estufa de pellets?",
    lead="Cuántos kilos de pellets quema por hora, cuántos sacos necesitas al mes y en todo el invierno, y cuánta luz gasta, con el precio del saco de 2026.",
    answer=(f"Una estufa de pellets de <b>8 kW</b> quema unos <b>{nf(p_kgh, 1)} kg de pellets por hora</b> a potencia media. "
            f"Encendida 6 horas al día gasta unos {nf(p_day_kg, 1)} kg (medio saco): <b>≈ {eur(p_day, 2)} al día</b> con el saco de 15 kg a "
            f"{eur(P['saco'], 2)}. Al mes son unos <b>{nf(p_month_sacos)} sacos y {eur(rnd(p_month), 0)}</b>."),
    cat="pellets",
    cfg=dict(fuel="pellet", unit="kW", opts=[6, 8, 10, 12, 14], def_=8, hours=6, priceKey="saco",
             priceLabel="Precio del saco de 15 kg", priceUnit="€", priceStep=0.01,
             hint="Potencia nominal de la estufa, en kW (viene en la ficha técnica)."),
)

# ---------- LEÑA
len_top = top_products({"lena-biomasa"}, 8, exclude=("exteriores",))
PAGES["lena"] = dict(
    slug="cuanto-gasta-estufa-lena",
    nav="Leña",
    title="¿Cuánto gasta una estufa de leña? Kilos por hora y coste (2026)",
    desc=(f"Una estufa de leña de 8 kW quema unos {nf(l_kgh, 1)} kg de leña seca por hora: ≈ {eur(l_h, 2)} por hora y "
          f"{eur(rnd(l_month), 0)} al mes usándola 6 horas al día. Calcula la tuya y compárala con pellets o chimenea."),
    h1="¿Cuánto gasta una estufa de leña?",
    lead="Cuántos kilos de leña quema por hora, cuánta leña necesitas para el invierno y cuánto ahorras frente a una chimenea abierta, con precios de 2026.",
    answer=(f"Una estufa de leña de <b>8 kW</b> quema unos <b>{nf(l_kgh, 1)} kg de leña seca por hora</b> a potencia media: "
            f"unos {eur(l_h, 2)} por hora con la leña a {nf(P['lena'], 2)} €/kg. Encendida 6 horas al día son unos {nf(l_day_kg)} kg y "
            f"<b>{eur(l_day, 2)} al día</b>, <b>≈ {eur(rnd(l_month), 0)} al mes</b>. Para todo el invierno ({MONTHS} meses), unos "
            f"{nf(rnd(l_season_kg))} kg de leña."),
    cat="lena-biomasa",
    cfg=dict(fuel="lena", unit="kW", opts=[5, 7, 9, 11, 13], def_=8, hours=6, priceKey="lena",
             priceLabel="Precio de la leña", priceUnit="€/kg", priceStep=0.01,
             hint="Potencia nominal de la estufa, en kW (viene en la ficha técnica)."),
)


# ---------------------------------------------------------------- tablas por potencia
def table_butano():
    rows = []
    for kw in (1.7, 3, 4.2):
        for lvl, lname in ((1, "A tope"), (0.6, "Media"), (0.35, "Suave")):
            h = kw * lvl * c_but
            dur = bomb_kwh / (kw * lvl)
            rows.append(f"<tr><td>{nf(kw * 1000)} W</td><td>{lname}</td><td><b>{eur(h, 2)}</b></td><td>{nf(dur)} h</td>"
                        f"<td>{eur(h * 5, 2)}</td><td>{eur(h * 5 * 30, 0)}</td></tr>")
    head = "<tr><th>Estufa</th><th>Potencia</th><th>Por hora</th><th>Dura una bombona</th><th>Al día (5 h)</th><th>Al mes</th></tr>"
    return head, "\n".join(rows)


def table_electrica():
    rows = []
    for w in (800, 1000, 1200, 1500, 2000, 2500, 3000):
        kw = w / 1000
        rows.append(f"<tr><td>{nf(w)} W</td><td>{eur(kw * LUZ, 2)}</td><td><b>{eur(kw * 0.6 * LUZ, 2)}</b></td>"
                    f"<td>{eur(kw * 0.6 * LUZ * 5, 2)}</td><td>{eur(kw * 0.6 * LUZ * 150, 0)}</td></tr>")
    head = "<tr><th>Potencia</th><th>Por hora a tope</th><th>Por hora con termostato</th><th>Al día (5 h)</th><th>Al mes</th></tr>"
    return head, "\n".join(rows)


def table_pellets():
    rows = []
    for kw in (6, 8, 10, 12, 14):
        k = kg_h("pellet", kw, 0.6)
        day = k * 6 * P["saco"] / 15
        rows.append(f"<tr><td>{nf(kw)} kW</td><td>{nf(kg_h('pellet', kw, 1), 1)} kg</td><td><b>{nf(k, 1)} kg</b></td>"
                    f"<td>{nf(15 / k, 0)} h</td><td>{eur(day, 2)}</td><td>{nf(k * 6 * 30 / 15)} sacos · {eur(day * 30, 0)}</td></tr>")
    head = "<tr><th>Potencia</th><th>Pellets por hora a tope</th><th>Por hora a potencia media</th><th>Dura un saco</th><th>Al día (6 h)</th><th>Al mes</th></tr>"
    return head, "\n".join(rows)


def table_lena():
    rows = []
    for kw in (5, 7, 9, 11, 13):
        k = kg_h("lena", kw, 0.6)
        rows.append(f"<tr><td>{nf(kw)} kW</td><td><b>{nf(k, 1)} kg</b></td><td>{eur(k * P['lena'], 2)}</td>"
                    f"<td>{nf(k * 6)} kg · {eur(k * 6 * P['lena'], 2)}</td><td>{nf(rnd(k * 6 * 30))} kg · {eur(k * 6 * 30 * P['lena'], 0)}</td></tr>")
    head = "<tr><th>Potencia</th><th>Leña por hora</th><th>Por hora</th><th>Al día (6 h)</th><th>Al mes</th></tr>"
    return head, "\n".join(rows)


TABLES = {"butano": table_butano, "electrica": table_electrica, "pellets": table_pellets, "lena": table_lena}
TABLE_TITLES = {
    "butano": ("Gasto de una estufa de butano según su potencia",
               "Con la bombona de 12,5 kg a " + eur(P["bombona"], 2) + ". «Media» es como suele usarse con la habitación ya caliente."),
    "electrica": ("Gasto de una estufa eléctrica según su potencia",
                  f"Con la luz a {nf(LUZ, 2)} €/kWh. Con termostato, la estufa trabaja de media un 60 % del tiempo."),
    "pellets": ("Gasto de una estufa de pellets según su potencia",
                f"Con el saco de 15 kg a {eur(P['saco'], 2)}. Potencia media = 60 % de la nominal, lo normal con la casa ya caliente."),
    "lena": ("Gasto de una estufa de leña según su potencia",
             f"Leña seca a {nf(P['lena'], 2)} €/kg, a potencia media (60 % de la nominal) y con un rendimiento del 70 %."),
}


PRODUCT_NOTES = {
    "butano": "Casi todas tienen 4.200 W, así que gastan lo mismo a igual uso. Lo que cambia es el tipo de calor (llama azul, infrarrojos o catalítica), la seguridad y lo fácil que es moverla.",
    "electrica": "A igual potencia, todas gastan lo mismo por hora: lo que cambia es cómo reparten el calor y si tienen termostato, que es lo que de verdad ahorra.",
    "pellets": "Cuanta más potencia, más pellet queman a tope, pero con termostato una estufa bien elegida para tus metros trabaja menos rato. No compres más potencia de la que necesitas.",
    "lena": "Lo que gastan depende sobre todo de la potencia a la que la uses y de lo seca que esté la leña. Elige la potencia según los metros que quieres calentar.",
}


def product_table(key):
    cfg = PAGES[key]["cfg"]
    fuel = cfg["fuel"]
    items = {"butano": gas_top, "electrica": el_top, "pellets": pel_top, "lena": len_top}[key]
    hours = cfg["hours"]
    rows = []
    for p in items:
        kw = p["potencia_kw"]
        h = kw * 0.6 * cpk(fuel)
        extra = ""
        if fuel == "butano":
            extra = f"<td>{nf(bomb_kwh / (kw * 0.6))} h</td>"
        elif fuel in ("pellet", "lena"):
            extra = f"<td>{nf(kg_h(fuel, kw, 0.6), 1)} kg</td>"
        r, rc = p.get("valoracion_media"), p.get("resenas_cantidad") or 0
        val = f"{nf(r, 1)} ★ <small>({nf(rc)})</small>" if r and rc else "–"
        rows.append(f'<tr><td><a href="{PROD_URL(p["id"])}">{esc(p["name"])}</a></td><td>{nf(kw, 1)} kW</td>'
                    f'<td>{p["superficie_calefactable_m2"]} m²</td><td><b>{eur(h, 2)}</b></td>{extra}'
                    f'<td>{eur(h * hours * 30, 0)}</td><td>{val}</td></tr>')
    extra_head = {"butano": "<th>Dura una bombona</th>", "pellet": "<th>Pellets por hora</th>",
                  "lena": "<th>Leña por hora</th>"}.get(fuel, "")
    head = (f"<tr><th>Modelo</th><th>Potencia</th><th>Calienta hasta</th><th>Por hora</th>{extra_head}"
            f"<th>Al mes ({hours} h/día)</th><th>Valoración</th></tr>")
    return head, "\n".join(rows)


# ---------------------------------------------------------------- secciones propias de cada tipo
def extra_sections(key):
    if key == "butano":
        return f"""
<section class="card prose">
  <h2>Seguridad: lo que hay que saber antes de encenderla</h2>
  <p>Una estufa de butano quema el gas dentro de la habitación: consume oxígeno y suelta el vapor de agua y los gases de la combustión en casa. Bien usada es segura, pero conviene seguir estas reglas:</p>
  <ul>
    <li><b>Ventila a menudo.</b> Deja una rendija abierta o abre la ventana unos minutos cada pocas horas.</li>
    <li><b>No la uses en el baño ni en el dormitorio</b>, y nunca duermas con ella encendida.</li>
    <li><b>Comprueba que tenga detector de oxígeno</b> (sistema ODS o «analizador de atmósfera»): apaga la estufa si el aire se empobrece. Las estufas actuales lo llevan de serie.</li>
    <li><b>Revisa la goma</b>: lleva impresa la fecha de caducidad; si ha caducado o está agrietada, cámbiala.</li>
    <li><b>Ojo con la humedad.</b> A potencia media suelta unos {nf(b_water, 1)} litros de agua por hora en forma de vapor. En casas con condensación, es mejor otra estufa.</li>
  </ul>
</section>"""
    if key == "electrica":
        return f"""
<section class="card prose">
  <h2>¿Existen las estufas eléctricas de bajo consumo?</h2>
  <p>No del todo: <b>todas las estufas eléctricas convierten el 100 % de la electricidad en calor</b>. Una de 2.000 W gasta lo mismo que cualquier otra de 2.000 W mientras está encendida. Lo que cambia es cómo reparten el calor y cuánto rato trabajan:</p>
  <ul>
    <li><b>Termostato</b>: es lo que más ahorra, porque apaga la estufa cuando llega a la temperatura que eliges.</li>
    <li><b>Estufas de cuarzo o halógenas</b>: calientan a quien tienen delante, al momento. Buenas para ratos cortos o un baño, no para toda la casa.</li>
    <li><b>Calefactores cerámicos y convectores</b>: calientan el aire de la habitación rápido.</li>
    <li><b>Radiadores de aceite</b>: tardan más en arrancar pero guardan el calor y lo sueltan poco a poco.</li>
  </ul>
  <h2>A qué hora es más barato encenderla</h2>
  <p>Con la tarifa regulada (PVPC), la luz cuesta menos en las horas valle: <b>de 0 a 8 h entre semana y todo el día los sábados, domingos y festivos nacionales</b>. Las más caras son de 10 a 14 h y de 18 a 22 h entre semana. Con una tarifa de precio fijo, la hora da igual.</p>
  <p>Además, con 3,45 kW contratados, una estufa de 2.000 W junto al horno o la lavadora puede hacer saltar el limitador.</p>
</section>"""
    if key == "pellets":
        elec_day = 0.08 * 6 * LUZ + 0.35 * (10 / 60) * LUZ
        return f"""
<section class="card prose">
  <h2>¿Gasta luz una estufa de pellets?</h2>
  <p>Sí, pero poco. La mayoría necesita enchufe para la resistencia de encendido (unos 300–400 W durante unos minutos) y para los ventiladores y el sinfín que lleva el pellet al quemador (unos 50–100 W mientras funciona). Encendiéndola una vez al día y usándola 6 horas, son unos <b>{eur(elec_day, 2)} de luz al día</b>. Hay modelos <a href="{CB}producto/pellets-joima-naturstyle-negro.html">sin electricidad</a> que funcionan por gravedad.</p>
  <h2>Qué pellet comprar para gastar menos</h2>
  <ul>
    <li><b>Certificado ENplus A1</b>: menos ceniza y menos humedad, así que da más calor por kilo y ensucia menos el quemador.</li>
    <li><b>Por palé sale más barato</b> que por sacos sueltos, si tienes sitio seco donde guardarlo.</li>
    <li><b>Guárdalo seco</b>: el pellet que coge humedad se deshace y quema peor.</li>
  </ul>
</section>"""
    if key == "lena":
        return f"""
<section class="card prose">
  <h2>La leña seca marca la diferencia</h2>
  <p>El cálculo supone leña <b>seca, con menos del 20 % de humedad</b>. La leña verde o mojada gasta buena parte de su energía en evaporar el agua: da hasta un tercio menos de calor, ensucia el cristal y llena el tiro de hollín. Por kilo, casi todas las maderas secas dan un calor parecido; las densas, como la encina, el roble o el olivo, ocupan menos y duran más en la estufa.</p>
  <h2>Estufa de leña o chimenea abierta</h2>
  <p>Una chimenea abierta aprovecha solo un 20 % del calor; el resto se va por el tiro. Para dar el mismo calor que una estufa de leña, <b>gasta unas {nf(EFF['lena'] / EFF['chimenea'], 1)} veces más leña</b>: el calor útil sale a {nf(c_chi * 100, 1)} céntimos el kWh, frente a {nf(c_len * 100, 1)} céntimos con una estufa. Poner un insertable o una estufa en la chimenea se paga en pocos inviernos.</p>
</section>"""
    return ""


TIPS = {
    "butano": [
        "Úsala como apoyo en la habitación donde estás, no para toda la casa: para más de 35–40 m² necesitarías varias.",
        "Ponla a potencia media en cuanto la habitación se caliente: a tope gasta casi el doble.",
        "Compra la bombona regulada de 12,5 kg: su precio máximo lo fija el Gobierno.",
        "Cierra puertas y baja persianas al anochecer para no perder el calor.",
    ],
    "electrica": [
        "Usa siempre el termostato y ponlo a 19–20 °C: cada grado de más sube el gasto alrededor de un 7 %.",
        "Calienta solo la habitación donde estás y cierra la puerta.",
        "Si tienes la tarifa regulada, aprovecha las horas valle y los fines de semana.",
        "Para muchas horas al día o para toda la casa, una estufa de pellets o de leña sale bastante más barata.",
    ],
    "pellets": [
        "Programa el encendido: arrancar la estufa gasta luz y pellet, así que mejor pocas veces y en modo bajo que encender y apagar a menudo.",
        "Limpia el brasero cada día o cada dos y el cristal en frío: un quemador sucio quema peor.",
        "Elige la potencia justa para tus metros: una estufa muy grande trabaja casi siempre al mínimo y se ensucia más.",
        "Haz el mantenimiento anual con un técnico: sale más barato que una avería a mitad de invierno.",
    ],
    "lena": [
        "Quema solo leña seca y guárdala a cubierto pero ventilada.",
        "Carga poca leña y a menudo: una estufa llena de troncos con el aire cerrado quema mal y ensucia.",
        "Limpia el tiro una vez al año; un tiro sucio tira peor y es peligroso.",
        "Si tienes chimenea abierta, un insertable o una estufa te ahorra más de la mitad de la leña.",
    ],
}


def faqs(key):
    if key == "butano":
        return [
            ("¿Cuánto dura una bombona de butano con una estufa?",
             f"Una bombona de 12,5 kg dura unas {nf(b_dur_full)} horas con una estufa de 4.200 W a tope, unas {nf(b_dur_norm)} horas a potencia media y unas {nf(b_dur_soft)} horas en mínimo. Usándola 5 horas al día, una bombona dura entre {nf(b_dur_full / 5)} y {nf(b_dur_soft / 5)} días."),
            ("¿Cuánto gasta una estufa de butano por hora?",
             f"Con la bombona a {eur(P['bombona'], 2)}, una estufa de 4.200 W gasta unos {eur(b_h_full, 2)} por hora a tope y unos {eur(b_h_norm, 2)} a potencia media."),
            ("¿Qué gasta menos, una estufa de butano o una eléctrica?",
             f"El calor del butano sale más barato: {nf(c_but * 100, 1)} céntimos por kWh, frente a {nf(c_luz * 100, 1)} céntimos de una estufa eléctrica con la luz a {nf(LUZ, 2)} €/kWh. Para dar el mismo calor, la eléctrica cuesta casi el doble; a cambio, no hay que ventilar ni cargar bombonas."),
            ("¿Cuántos metros calienta una estufa de butano?",
             "Una estufa de 4.200 W calienta bien entre 30 y 40 m², según el aislamiento y el clima. Para más superficie hacen falta varias o un sistema de calefacción con salida de humos."),
            ("¿Cuándo cambia el precio de la bombona de butano?",
             f"El precio máximo de la bombona regulada se revisa cada dos meses, el tercer martes de enero, marzo, mayo, julio, septiembre y noviembre. Desde el 15 de septiembre de 2026 cuesta {eur(P['bombona'], 2)}; la próxima revisión es el {BUTANO_NEXT}."),
            ("¿Se puede dormir con la estufa de butano encendida?",
             "No. Consume oxígeno de la habitación y suelta gases de la combustión: apágala antes de dormir y no la uses en dormitorios ni baños."),
        ]
    if key == "electrica":
        return [
            ("¿Cuánto gasta una estufa eléctrica de 2.000 W al mes?",
             f"Con la luz a {nf(LUZ, 2)} €/kWh y termostato, unos {eur(e_h_norm, 2)} por hora: {eur(rnd(e_month), 0)} al mes usándola 5 horas al día, o {eur(rnd(e_h_norm * 8 * 30), 0)} si la usas 8 horas. A tope todo el rato serían {eur(e_h_full * 5 * 30, 0)} al mes con 5 horas al día."),
            ("¿Cuánto gasta una estufa eléctrica de 800 W?",
             f"A tope consume 0,8 kWh cada hora: {eur(0.8 * LUZ, 2)} por hora con la luz a {nf(LUZ, 2)} €/kWh. Usándola 3 horas al día son unos {eur(0.8 * LUZ * 3 * 30, 0)} al mes."),
            ("¿Qué gasta menos, un radiador de aceite o un calefactor?",
             "A igual potencia gastan lo mismo por hora. El radiador de aceite tarda más en calentar pero mantiene el calor y el termostato lo apaga más rato; el calefactor calienta antes y va mejor para ratos cortos."),
            ("¿Cuánto gasta una chimenea eléctrica?",
             f"Lo que gasta es la resistencia: una de 2.000 W cuesta lo mismo que cualquier estufa de 2.000 W, {eur(e_h_full, 2)} por hora a tope. El efecto llama solo, con el calor apagado, consume muy poco."),
            ("¿Es más barata una estufa eléctrica que una de butano?",
             f"No: el calor eléctrico sale a {nf(c_luz * 100, 1)} céntimos por kWh y el del butano a {nf(c_but * 100, 1)} céntimos. Pero la eléctrica no necesita ventilar ni bombonas y es más segura para dormitorios y baños."),
        ]
    if key == "pellets":
        season = p_season_sacos * P["saco"]
        return [
            ("¿Cuántos kilos de pellets gasta una estufa al día?",
             f"Una estufa de 8 kW a potencia media quema unos {nf(p_kgh, 1)} kg por hora: {nf(p_day_kg, 1)} kg en 6 horas, medio saco al día. A tope serían {nf(p_kgh_full, 1)} kg por hora."),
            ("¿Cuánto dura un saco de pellets de 15 kg?",
             f"Con una estufa de 8 kW, unas {nf(15 / p_kgh)} horas a potencia media y unas {nf(15 / p_kgh_full)} horas a tope."),
            ("¿Cuántos sacos de pellets se gastan en un invierno?",
             f"Para una estufa de 8 kW encendida 6 horas al día durante {MONTHS} meses, unos {nf(rnd(p_season_sacos))} sacos de 15 kg, ≈ {eur(rnd(season), 0)}. En zonas frías o con más horas de uso, bastantes más: calcula tu casa en la calculadora."),
            ("¿Qué es más barato, pellets o gasóleo?",
             f"Con los precios de {PRICES_TXT}, el calor de una estufa de pellets sale a {nf(c_pel * 100, 1)} céntimos por kWh y el de una caldera de gasóleo a {nf(c_gas * 100, 1)} céntimos: con pellets pagas alrededor de un {nf((1 - c_pel / c_gas) * 100)} % menos."),
            ("¿Pellets o leña, qué sale más barato?",
             f"Muy parecido: {nf(c_pel * 100, 1)} céntimos por kWh con pellets y {nf(c_len * 100, 1)} con leña comprada a {nf(P['lena'], 2)} €/kg. Si tienes leña propia, gana la leña; si quieres comodidad (encendido programado, termostato), ganan los pellets."),
            ("¿Cuánto cuesta el saco de pellets en 2026?",
             f"De media, unos {eur(P['saco'], 2)} el saco de 15 kg según el índice de precios de AVEBIOM del segundo trimestre de 2026. Por palé sale algo más barato."),
        ]
    if key == "lena":
        season_eur = l_season_kg * P["lena"]
        return [
            ("¿Cuántos kilos de leña gasta una estufa al día?",
             f"Una estufa de 8 kW a potencia media quema unos {nf(l_kgh, 1)} kg de leña seca por hora: unos {nf(l_day_kg)} kg en 6 horas."),
            ("¿Cuánta leña se necesita para todo el invierno?",
             f"Para una estufa de 8 kW encendida 6 horas al día durante {MONTHS} meses, unos {nf(rnd(l_season_kg))} kg (≈ {nf(l_season_kg / 1000, 1)} toneladas), unos {eur(rnd(season_eur), 0)} a {nf(P['lena'], 2)} €/kg. En zonas frías o casas grandes, bastante más."),
            ("¿Qué gasta menos, una estufa de leña o una de pellets?",
             f"Con leña comprada sale muy parecido: {nf(c_len * 100, 1)} céntimos por kWh frente a {nf(c_pel * 100, 1)} con pellets. Con leña propia o barata, la estufa de leña es la calefacción más económica."),
            ("¿Gasta luz una estufa de leña?",
             "Las normales no: funcionan sin enchufe. Solo gastan algo de luz las que llevan ventilador para repartir el calor."),
            ("¿Cuánto cuesta la leña en 2026?",
             "La leña seca de encina con entrega a domicilio suele costar entre 0,20 y 0,35 €/kg; comprada por toneladas y recogida por ti, menos."),
        ]
    return []


# ---------------------------------------------------------------- plantilla
GTAG = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-QXVWVPP7SK"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-QXVWVPP7SK');
</script>"""

FAVICON = """<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23C1440E'/%3E%3Cpath d='M16 6c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-5 3-6 0 2 1 3 2 3 0-3-1-6 1-9z' fill='%23F2A93B'/%3E%3C/svg%3E">"""

EXTRA_CSS = """<style>
.crumbs{font-size:13.5px;color:var(--muted);margin:16px 0 0}
.crumbs a{color:var(--muted)}
.answer{background:var(--amber-soft);border-left:4px solid var(--primary);border-radius:12px;padding:16px 18px;font-size:17px;margin:6px 0 0;max-width:820px}
.answer p{margin:0}
.calc{margin-top:22px}
.below{grid-template-columns:minmax(0,1fr)}
.below > *{min-width:0}
.prose p,.prose li{color:var(--text);font-size:16px}
.prose ul{padding-left:20px;margin:8px 0 0}
.prose li{margin-bottom:6px}
.prose h2 + p{margin-top:6px}
.prose h2:not(:first-child){margin-top:22px}
.tw{overflow-x:auto;margin-top:12px;-webkit-overflow-scrolling:touch}
table.data{width:100%;border-collapse:collapse;font-size:14.5px;min-width:560px}
table.data th,table.data td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--border);vertical-align:top}
table.data th{font-size:12.5px;color:var(--muted);font-weight:600}
table.data tr.me td{background:var(--amber-soft)}
table.data td small{color:var(--muted)}
.price-in{display:flex;align-items:center;gap:8px}
.price-in input{max-width:120px}
.note{font-size:13.5px;color:var(--muted);margin:10px 0 0}
.netlinks.four{grid-template-columns:repeat(4,1fr)}
@media (max-width:900px){.netlinks.four{grid-template-columns:1fr 1fr}}
@media (max-width:640px){.netlinks.four{grid-template-columns:1fr}.answer{font-size:16px}}
</style>"""


GUIDES = {
    "potencia": dict(slug="calculadora-potencia-estufa", nav="Potencia",
                     h1="¿Qué potencia de estufa necesito?",
                     short="Los kW según tus m², tu provincia y el aislamiento."),
    "barata": dict(slug="que-calefaccion-es-mas-barata", nav="Más barata",
                   h1="¿Qué calefacción es más barata en 2026?",
                   short="Lo que cuesta cada sistema y cuál te conviene."),
    "seguridad": dict(slug="es-peligrosa-estufa-butano", nav="Seguridad butano",
                      h1="¿Es peligrosa una estufa de butano?",
                      short="Riesgos reales y cómo usarla sin peligro."),
}
SHORT = {
    "butano": "Por hora, cuánto dura la bombona y al mes.",
    "electrica": "800, 1.500 y 2.000 W por hora y al mes.",
    "pellets": "Kilos por hora, sacos al mes y por invierno.",
    "lena": "Kilos por hora y leña para todo el invierno.",
}


def any_url(k):
    if k == "home":
        return BASE
    pg = PAGES.get(k) or GUIDES[k]
    return BASE + pg["slug"] + ".html"


def nav_html(active):
    def a(k, label):
        cls = ' class="on"' if k == active else ""
        return f'<a{cls} href="{any_url(k)}">{label}</a>'
    links = [f'<a class="star" href="{CB}">★ CalorBrasa</a>', a("home", "Calculadora"), a("potencia", "Potencia"),
             a("barata", "Más barata")]
    links += [a(k, "Gasto " + pg["nav"].lower()) for k, pg in PAGES.items()]
    links += [a("seguridad", "Seguridad butano"), f'<a href="{CB}comparador.html">Comparador de estufas</a>']
    return "\n    ".join(links)


RELATED = {
    "butano": ["seguridad", "electrica", "barata", "potencia"],
    "electrica": ["barata", "butano", "potencia", "pellets"],
    "pellets": ["potencia", "lena", "barata", "electrica"],
    "lena": ["potencia", "pellets", "barata", "butano"],
    "potencia": ["barata", "pellets", "electrica", "butano"],
    "barata": ["potencia", "pellets", "electrica", "lena"],
    "seguridad": ["butano", "electrica", "barata", "potencia"],
}


def related(active):
    cards = []
    for k in RELATED[active]:
        pg = PAGES.get(k) or GUIDES[k]
        short = SHORT.get(k) or GUIDES[k]["short"]
        cards.append(f'<a href="{any_url(k)}"><b>{pg["h1"]}</b><span>{short}</span></a>')
    return "\n      ".join(cards)


JS = r"""
const $ = id => document.getElementById(id);
const nf = (v, d = 0) => v.toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
const eur = (v, d) => { if (d === undefined) d = v < 10 ? 2 : 0; return nf(v, d) + " €"; };
const round = v => v >= 100 ? Math.round(v / 10) * 10 : v >= 10 ? Math.round(v) : Math.round(v * 10) / 10;
const PCI = { pellet: 4.8, lena: 3.8, butano: 12.7 };
const SYS = [
  { id: "pellet", name: "Estufa de pellets", fuel: "pellet", eff: 0.85, url: CB + "categoria/estufas-de-pellets.html" },
  { id: "lena", name: "Estufa de leña", fuel: "lena", eff: 0.70, url: CB + "categoria/estufas-de-lena.html" },
  { id: "butano", name: "Estufa de butano", fuel: "butano", eff: 1.0, url: CB + "categoria/calefactores-de-gas.html" },
  { id: "luz", name: "Estufa o radiador eléctrico", fuel: "luz", eff: 1.0, url: CB + "categoria/calefactores-electricos.html" },
];
function cpk(s) {
  switch (s.fuel) {
    case "luz": return P.nose / s.eff;
    case "pellet": return (P.saco / 15) / (PCI.pellet * s.eff);
    case "lena": return P.lena / (PCI.lena * s.eff);
    case "butano": return (P.bombona / 12.5) / (PCI.butano * s.eff);
  }
}
const ME = SYS.find(s => s.id === CFG.fuel);
const S = { pow: CFG.def, lvl: 0.6, hours: CFG.hours, days: 30, months: CFG.months };
const fmtPow = v => nf(v, v % 1 ? 1 : 0) + " " + CFG.unit;

function render() {
  $("powChips").innerHTML = CFG.opts.map(o => `<button type="button" class="chip" data-v="${o}" aria-pressed="${o === S.pow}">${fmtPow(o)}</button>`).join("");
  if (document.activeElement !== $("pow")) $("pow").value = S.pow;
  $("powOut").textContent = fmtPow(S.pow);
  $("lvl").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.v === S.lvl)));
  $("hoursOut").textContent = `${S.hours} h`;
  $("daysOut").textContent = `${S.days} días`;
  $("monthsOut").textContent = `${S.months} ${S.months === 1 ? "mes" : "meses"}`;

  const kwNom = CFG.unit === "W" ? S.pow / 1000 : S.pow;
  const heat = kwNom * S.lvl;
  const perH = heat * cpk(ME), perD = perH * S.hours, perM = perD * S.days, perS = perM * S.months;
  $("dH").textContent = eur(perH, 2);
  $("dD").textContent = eur(perD, 2);
  $("dM").textContent = eur(perM, perM < 100 ? 2 : 0);
  $("dS").textContent = eur(round(perS), 0);
  $("dSl").textContent = `por invierno (${S.months} ${S.months === 1 ? "mes" : "meses"})`;
  $("calcSub").textContent = `${CFG.label} de ${fmtPow(S.pow)}, ${S.hours} h al día, ${S.days} días al mes, en modo ${S.lvl === 1 ? "a tope" : S.lvl === 0.6 ? "medio" : "suave"}.`;

  const f = [], hMonth = S.hours * S.days;
  if (ME.fuel === "luz") {
    f.push(`Consume <b>${nf(heat, 2)} kWh</b> cada hora (${nf(round(heat * hMonth))} kWh al mes) con la luz a ${nf(P.nose, 2)} €/kWh.`);
    f.push(`A tope costaría ${eur(kwNom * P.nose, 2)} por hora. El termostato hace que trabaje menos rato y gaste menos.`);
  } else if (ME.fuel === "pellet") {
    const kgh = heat / (PCI.pellet * ME.eff);
    f.push(`Quema <b>${nf(kgh, 2)} kg de pellets</b> por hora: unos <b>${nf(kgh * hMonth / 15, 1)} sacos</b> de 15 kg al mes.`);
    f.push(`Un saco te dura ≈ ${nf(15 / kgh, 0)} horas de uso (≈ ${nf(15 / kgh / S.hours, 1)} días).`);
  } else if (ME.fuel === "butano") {
    const kgh = heat / (PCI.butano * ME.eff), hrs = 12.5 / kgh;
    f.push(`Una bombona de 12,5 kg te dura <b>≈ ${nf(hrs, 0)} horas</b> de uso (≈ ${nf(hrs / S.hours, 0)} días).`);
    f.push(`Necesitarás ≈ ${nf(hMonth / hrs, 1)} bombonas al mes, a ${eur(P.bombona, 2)} cada una.`);
  } else if (ME.fuel === "lena") {
    const kgh = heat / (PCI.lena * ME.eff);
    f.push(`Quema <b>≈ ${nf(kgh, 1)} kg de leña</b> seca por hora: unos ${nf(round(kgh * hMonth))} kg al mes.`);
    f.push(`Con leña húmeda gastarás bastante más: compra leña seca (menos del 20 % de humedad).`);
  }
  $("facts").innerHTML = f.map(x => `<li>${x}</li>`).join("");

  const E = heat * hMonth;
  const others = SYS.map(o => ({ s: o, month: E * cpk(o) })).sort((a, b) => a.month - b.month);
  const max = Math.max(...others.map(o => o.month));
  $("rank").innerHTML = others.map((o, i) => {
    const isMe = o.s === ME;
    return `<li class="row${isMe ? " cur" : ""}">
      <span class="pos">${i + 1}</span>
      <span class="name">${o.s.name}${isMe ? '<span class="badge">La tuya</span>' : ""}</span>
      <span class="price">${eur(o.month, o.month < 100 ? 2 : 0)}<small>al mes</small></span>
      <div class="barline" aria-hidden="true"><div class="bar" style="width:${Math.max(3, o.month / max * 100).toFixed(1)}%"></div></div>
      <div class="meta"><a href="${o.s.url}">Ver modelos en CalorBrasa →</a></div>
    </li>`;
  }).join("");
}

$("powChips").onclick = e => { const b = e.target.closest("button"); if (!b) return; S.pow = +b.dataset.v; render(); };
$("pow").oninput = e => { const v = parseFloat(e.target.value); if (v > 0) { S.pow = v; render(); } };
$("lvl").onclick = e => { const b = e.target.closest("button"); if (!b) return; S.lvl = +b.dataset.v; render(); };
$("hours").oninput = e => { S.hours = +e.target.value; render(); };
$("days").oninput = e => { S.days = +e.target.value; render(); };
$("months").oninput = e => { S.months = +e.target.value; render(); };
$("price").oninput = e => { const v = parseFloat(e.target.value); if (v >= 0) { P[CFG.priceKey] = v; render(); } };
$("pow").step = CFG.unit === "W" ? 100 : 0.1;
$("price").value = P[CFG.priceKey];
render();
"""


def page(key):
    pg = PAGES[key]
    cfg = pg["cfg"]
    url = BASE + pg["slug"] + ".html"
    th_head, th_rows = TABLES[key]()
    t_title, t_note = TABLE_TITLES[key]
    pt_head, pt_rows = product_table(key)
    fq = faqs(key)
    cat_url = CAT_URL[pg["cat"]]
    label = {"butano": "Estufa de butano", "luz": "Estufa eléctrica", "pellet": "Estufa de pellets", "lena": "Estufa de leña"}[cfg["fuel"]]
    js_cfg = dict(fuel=cfg["fuel"], unit=cfg["unit"], opts=cfg["opts"], def_=cfg["def_"], hours=cfg["hours"], months=MONTHS,
                  priceKey=cfg["priceKey"], label=label)
    js_cfg["def"] = js_cfg.pop("def_")
    cat_names = {"gas": "estufas de butano", "electricos": "estufas eléctricas", "pellets": "estufas de pellets",
                 "lena-biomasa": "estufas de leña"}
    cat_count = sum(1 for p in PRODUCTS if p["category"] == pg["cat"])

    ld = [
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in fq]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Calculadora de calefacción", "item": BASE},
            {"@type": "ListItem", "position": 2, "name": pg["h1"], "item": url}]},
        {"@context": "https://schema.org", "@type": "Article", "headline": pg["title"], "description": pg["desc"],
         "inLanguage": "es", "datePublished": UPDATED_ISO, "dateModified": UPDATED_ISO, "mainEntityOfPage": url,
         "author": {"@type": "Organization", "name": "CalorBrasa", "url": CB},
         "publisher": {"@type": "Organization", "name": "CalorBrasa", "url": CB}},
    ]
    ld_html = "\n".join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in ld)
    faq_html = "\n      ".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in fq)
    tips_html = "\n    ".join(f"<li>{t}</li>" for t in TIPS[key])
    pw_label = "Potencia" + (" (vatios)" if cfg["unit"] == "W" else " (kW)")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(pg['title'])}</title>
<meta name="description" content="{esc(pg['desc'])}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(pg['title'])}">
<meta property="og:description" content="{esc(pg['desc'])}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Calculadora de Calefacción">
<meta property="og:locale" content="es_ES">
<meta name="theme-color" content="#C1440E">
{GTAG}
{FAVICON}
{CSS}
{EXTRA_CSS}
{ld_html}
</head>
<body>

<header class="top">
  <div class="wrap">
    <a class="brand" href="{BASE}">
      <svg class="logo" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#C1440E"/><path d="M16 6c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-5 3-6 0 2 1 3 2 3 0-3-1-6 1-9z" fill="#F2A93B"/></svg>
      <span>Calculadora de Calefacción<small>una herramienta de CalorBrasa</small></span>
    </a>
    <a class="btn" href="{cat_url}">Ver {cat_names[pg['cat']]} →</a>
  </div>
</header>
<nav class="net" aria-label="Nuestras webs">
  <div class="wrap">
    {nav_html(key)}
  </div>
</nav>

<main class="wrap">
  <p class="crumbs"><a href="{BASE}">Calculadora de calefacción</a> › {pg['h1']}</p>
  <section class="hero">
    <h1>{pg['h1']}</h1>
    <p>{pg['lead']}</p>
    <div class="answer"><p>{pg['answer']}</p></div>
    <ul class="trust" style="margin-top:14px">
      <li>Actualizado en <b>{UPDATED_TXT}</b></li>
      <li>Precios de <b>{PRICES_TXT}</b></li>
      <li><b>Gratis</b> y sin registro</li>
    </ul>
  </section>

  <section class="layout calc" aria-labelledby="calcTitle">
    <form class="card inputs" onsubmit="return false" aria-label="Datos de tu estufa">
      <div class="step">
        <h2><span class="num">1</span>Tu estufa</h2>
        <div class="field">
          <label for="pow">{pw_label} <output id="powOut"></output></label>
          <div class="chips" id="powChips" role="group" aria-label="Potencias típicas"></div>
          <input type="number" id="pow" min="0" step="any" style="margin-top:8px" aria-label="Potencia exacta">
          <div class="hint">{cfg['hint']}</div>
        </div>
        <div class="field">
          <label for="price">{cfg['priceLabel']} <output>{cfg['priceUnit']}</output></label>
          <div class="price-in"><input type="number" id="price" min="0" step="{cfg['priceStep']}"></div>
          <div class="hint">Ponemos el precio de {PRICES_TXT}. Cámbialo por el tuyo si lo sabes.</div>
        </div>
      </div>
      <div class="step">
        <h2><span class="num">2</span>Cómo la usas</h2>
        <div class="field">
          <span class="lbl">Intensidad</span>
          <div class="seg c3" id="lvl" role="group" aria-label="Intensidad de uso">
            <button type="button" data-v="1">A tope<small>100 %</small></button>
            <button type="button" data-v="0.6">Media<small>Con termostato</small></button>
            <button type="button" data-v="0.35">Suave<small>Mantener</small></button>
          </div>
        </div>
        <div class="field">
          <label for="hours">Horas al día <output id="hoursOut"></output></label>
          <input type="range" id="hours" min="1" max="24" step="1" value="{cfg['hours']}">
        </div>
        <div class="field">
          <label for="days">Días al mes <output id="daysOut"></output></label>
          <input type="range" id="days" min="1" max="31" step="1" value="30">
        </div>
        <div class="field">
          <label for="months">Meses de frío <output id="monthsOut"></output></label>
          <input type="range" id="months" min="1" max="9" step="1" value="{MONTHS}">
        </div>
      </div>
    </form>

    <div class="results" aria-live="polite">
      <div class="card">
        <h2 id="calcTitle">Calcula lo que gasta la tuya</h2>
        <p class="sub" id="calcSub"></p>
        <div class="tiles">
          <div class="tile"><b id="dH">–</b><small>por hora</small></div>
          <div class="tile"><b id="dD">–</b><small>al día</small></div>
          <div class="tile"><b id="dM">–</b><small>al mes</small></div>
          <div class="tile hot"><b id="dS">–</b><small id="dSl">por invierno</small></div>
        </div>
        <ul class="facts" id="facts"></ul>
      </div>
      <div class="card">
        <h2>El mismo calor con otras estufas</h2>
        <p class="sub">Lo que costaría al mes dar exactamente el mismo calor.</p>
        <ol class="rank" id="rank"></ol>
      </div>
    </div>
  </section>

  <div class="below">
    <section class="card">
      <h2>{t_title}</h2>
      <p class="sub">{t_note}</p>
      <div class="tw"><table class="data">
        <thead>{th_head}</thead>
        <tbody>
{th_rows}
        </tbody>
      </table></div>
    </section>

    <section class="card">
      <h2>Cuánto gastan los modelos más valorados</h2>
      <p class="sub">Las {cat_names[pg['cat']]} con mejor valoración de las {cat_count} que comparamos en CalorBrasa, con su gasto a potencia media.</p>
      <div class="tw"><table class="data">
        <thead>{pt_head}</thead>
        <tbody>
{pt_rows}
        </tbody>
      </table></div>
      <div class="cta-row">
        <p>Valoraciones de compradores en Amazon. Precios y opiniones en cada ficha.</p>
        <a class="btn" href="{cat_url}">Ver las {cat_count} en CalorBrasa →</a>
      </div>
      <p class="note">{PRODUCT_NOTES[key]}</p>
    </section>

    {extra_sections(key)}

    <section class="card">
      <h2>¿Sale más barata que otras estufas?</h2>
      <p class="sub">Lo que cuesta cada kWh de calor que llega a tu casa, ya descontado lo que se pierde.</p>
      <div class="tw"><table class="data">
        <thead><tr><th>Sistema</th><th>Rendimiento</th><th>Coste por kWh de calor</th><th>1.000 kWh de calor</th></tr></thead>
        <tbody>
{comparison_rows(cfg['fuel'])}
        </tbody>
      </table></div>
      <p class="note">{COMPARISON_NOTE}</p>
    </section>

    <section class="card prose">
      <h2>Trucos para gastar menos</h2>
      <ul>
    {tips_html}
      </ul>
    </section>

    <section class="card faq" id="faq">
      <h2>Preguntas frecuentes</h2>
      {faq_html}
    </section>

    <details class="card method">
      <summary>Cómo hacemos el cálculo</summary>
      <ul>
        <li><b>Gasto por hora</b> = potencia × intensidad × precio de cada kWh de calor. «Media» supone que la estufa trabaja al 60 % de su potencia (lo normal con termostato y la habitación ya caliente); «suave», al 35 %.</li>
        <li><b>Energía de cada combustible</b>: pellet 4,8 kWh/kg, leña seca 3,8 kWh/kg, butano 12,7 kWh/kg.</li>
        <li><b>Rendimiento</b>: eléctrica y butano 100 %, estufa de pellets 85 %, estufa de leña 70 %, chimenea abierta 20 %, caldera de gasóleo 85 %.</li>
        <li><b>Gasto de los modelos</b>: calculado con la potencia de cada ficha de CalorBrasa y el mismo método, para poder compararlos entre sí.</li>
      </ul>
      <p>Es una estimación orientativa: el gasto real depende de tu casa, del clima y de la temperatura que pongas.</p>
    </details>

    <section class="bigcta">
      <div>
        <h2>Encuentra la estufa que más te conviene</h2>
        <p>En CalorBrasa comparas más de 100 estufas: potencia, metros que calientan, gasto y opiniones.</p>
      </div>
      <a class="btn" href="{CB}comparador.html">Ir al comparador de CalorBrasa →</a>
    </section>

    <section>
      <h2 style="font-size:20px;margin:0">Amplía información</h2>
      <div class="netlinks four">
      {related(key)}
      </div>
    </section>
  </div>
</main>

<footer>
  <div class="wrap">
    <div class="links">
      <a class="star" href="{CB}">★ CalorBrasa</a>
      <a href="{BASE}">Calculadora de calefacción</a>
      <a href="{CAT_URL['pellets']}">Estufas de pellets</a>
      <a href="{CAT_URL['lena-biomasa']}">Estufas de leña</a>
      <a href="{CAT_URL['electricos']}">Estufas eléctricas</a>
      <a href="{CAT_URL['gas']}">Estufas de butano</a>
      <a href="{CAT_URL['radiadores']}">Radiadores</a>
    </div>
    <p>Resultados orientativos. Los enlaces a CalorBrasa llevan a productos de Amazon con enlace de afiliado: si compras, CalorBrasa puede recibir una comisión sin coste extra para ti. © 2026 CalorBrasa.</p>
  </div>
</footer>

<script>
const CB = "{CB}";
const CFG = {json.dumps(js_cfg, ensure_ascii=False)};
const P = {json.dumps(P)};
{JS}
</script>
</body>
</html>
"""


# ======================================================================
# GUÍAS: potencia, qué calefacción es más barata y seguridad del butano
# ======================================================================
ZONES = {
    "alpha": dict(name="Muy suave", code="α", f=0.70, lf=0.35, h=3, m=2),
    "A": dict(name="Suave", code="A", f=0.85, lf=0.40, h=4, m=3),
    "B": dict(name="Templado", code="B", f=0.92, lf=0.42, h=5, m=4),
    "C": dict(name="Fresco", code="C", f=1.00, lf=0.45, h=6, m=5),
    "D": dict(name="Frío", code="D", f=1.10, lf=0.48, h=7, m=6),
    "E": dict(name="Muy frío", code="E", f=1.20, lf=0.50, h=8, m=7),
}
PROV = dict(re.findall(r'"([^"]+)":"(\w+)"', re.search(r"const PROV = \{(.*?)\};", index_src, re.S).group(1)))
INS = {"buena": 0.75, "normal": 1.0, "mala": 1.35}
BASE_W = 95

# Gas natural (TUR) y bomba de calor: rangos, no forman parte de la calculadora
GAS_TUR_LOW, GAS_TUR_HIGH = 0.050428, 0.0695   # €/kWh sin impuestos, oct. 2026 (papernest / estimación OCU)
IEH, IVA, EFF_CALDERA = 0.00234, 1.21, 0.90
c_gn_low = (GAS_TUR_LOW + IEH) * IVA / EFF_CALDERA
c_gn_high = (GAS_TUR_HIGH + IEH) * IVA / EFF_CALDERA
c_bdc_low, c_bdc_high = LUZ / 4, LUZ / 3   # SCOP 4 a 3


def need_kw(m2, zone, ins="normal", h=2.5):
    return m2 * BASE_W * ZONES[zone]["f"] * INS[ins] * (h / 2.5) / 1000


def season_kwh(m2, zone, ins="normal", hours=None, months=None):
    z = ZONES[zone]
    hours = hours or z["h"]
    months = months or z["m"]
    return need_kw(m2, zone, ins) * z["lf"] * hours * 30.4 * months


def footer_html():
    return f"""<footer>
  <div class="wrap">
    <div class="links">
      <a class="star" href="{CB}">★ CalorBrasa</a>
      <a href="{BASE}">Calculadora de calefacción</a>
      <a href="{CAT_URL['pellets']}">Estufas de pellets</a>
      <a href="{CAT_URL['lena-biomasa']}">Estufas de leña</a>
      <a href="{CAT_URL['electricos']}">Estufas eléctricas</a>
      <a href="{CAT_URL['gas']}">Estufas de butano</a>
      <a href="{CAT_URL['radiadores']}">Radiadores</a>
    </div>
    <p>Resultados orientativos. Los enlaces a CalorBrasa llevan a productos de Amazon con enlace de afiliado: si compras, CalorBrasa puede recibir una comisión sin coste extra para ti. © 2026 CalorBrasa.</p>
  </div>
</footer>"""


def shell(key, title, desc, lead, answer, body, fq, btn, script="", prices=True):
    g = GUIDES[key]
    url = any_url(key)
    ld = [
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in fq]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Calculadora de calefacción", "item": BASE},
            {"@type": "ListItem", "position": 2, "name": g["h1"], "item": url}]},
        {"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc,
         "inLanguage": "es", "datePublished": UPDATED_ISO, "dateModified": UPDATED_ISO, "mainEntityOfPage": url,
         "author": {"@type": "Organization", "name": "CalorBrasa", "url": CB},
         "publisher": {"@type": "Organization", "name": "CalorBrasa", "url": CB}},
    ]
    ld_html = "\n".join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in ld)
    faq_html = "\n      ".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in fq)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Calculadora de Calefacción">
<meta property="og:locale" content="es_ES">
<meta name="theme-color" content="#C1440E">
{GTAG}
{FAVICON}
{CSS}
{EXTRA_CSS}
{GUIDE_CSS}
{ld_html}
</head>
<body>

<header class="top">
  <div class="wrap">
    <a class="brand" href="{BASE}">
      <svg class="logo" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#C1440E"/><path d="M16 6c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-5 3-6 0 2 1 3 2 3 0-3-1-6 1-9z" fill="#F2A93B"/></svg>
      <span>Calculadora de Calefacción<small>una herramienta de CalorBrasa</small></span>
    </a>
    <a class="btn" href="{btn[0]}">{btn[1]}</a>
  </div>
</header>
<nav class="net" aria-label="Nuestras webs">
  <div class="wrap">
    {nav_html(key)}
  </div>
</nav>

<main class="wrap">
  <p class="crumbs"><a href="{BASE}">Calculadora de calefacción</a> › {g['h1']}</p>
  <section class="hero">
    <h1>{g['h1']}</h1>
    <p>{lead}</p>
    <div class="answer"><p>{answer}</p></div>
    <ul class="trust" style="margin-top:14px">
      <li>Actualizado en <b>{UPDATED_TXT}</b></li>
      {f'<li>Precios de <b>{PRICES_TXT}</b></li>' if prices else ''}
    </ul>
  </section>

{body}

  <div class="below">
    <section class="card faq" id="faq">
      <h2>Preguntas frecuentes</h2>
      {faq_html}
    </section>

    <section class="bigcta">
      <div>
        <h2>Encuentra la estufa que más te conviene</h2>
        <p>En CalorBrasa comparas más de 100 estufas: potencia, metros que calientan, gasto y opiniones.</p>
      </div>
      <a class="btn" href="{CB}comparador.html">Ir al comparador de CalorBrasa →</a>
    </section>

    <section>
      <h2 style="font-size:20px;margin:0">Amplía información</h2>
      <div class="netlinks four">
      {related(key)}
      </div>
    </section>
  </div>
</main>

{footer_html()}
{script}
</body>
</html>
"""


GUIDE_CSS = """<style>
.kpi-big{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 14px;margin:2px 0 12px}
.kpi-big b{font-size:clamp(34px,6vw,48px);letter-spacing:-1px;color:var(--amber)}
.kpi-big span{color:#d6ccc4}
.equiv{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.equiv li{background:var(--surface-2);border-radius:10px;padding:10px 12px;font-size:15px}
.equiv li a{font-weight:600}
.picks{display:grid;gap:14px}
.picks h3{font-size:15px;margin:0 0 6px}
.picks ul{margin:0;padding-left:18px}
.picks li{font-size:14.5px;margin:3px 0}
.picks small{color:var(--muted)}
.risk{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:12px}
.risk div{background:var(--surface-2);border-radius:12px;padding:14px}
.risk b{display:block;margin-bottom:4px}
.risk p{margin:0;font-size:15px;color:var(--muted)}
.alert{background:var(--amber-soft);border-left:4px solid var(--primary);border-radius:12px;padding:14px 16px;margin-top:14px}
.alert p{margin:0 0 6px}
.alert p:last-child{margin:0}
ol.rules{padding-left:22px;margin:8px 0 0}
ol.rules li{margin-bottom:8px}
.zones{columns:2;column-gap:24px;font-size:14.5px;margin:10px 0 0;padding:0;list-style:none}
.zones li{break-inside:avoid;margin-bottom:8px}
.zones b{color:var(--primary)}
@media (max-width:640px){.risk{grid-template-columns:1fr}.zones{columns:1}}
</style>"""


# ---------------------------------------------------------------- POTENCIA
def potencia_page():
    zones_cols = ["A", "B", "C", "D", "E"]
    rows = []
    for m2 in (10, 15, 20, 30, 40, 50, 60, 80, 100, 120, 150, 200):
        cells = "".join(f"<td>{nf(need_kw(m2, z), 1)} kW</td>" for z in zones_cols)
        rows.append(f"<tr><td><b>{m2} m²</b></td>{cells}</tr>")
    head = "<tr><th>Superficie</th>" + "".join(f"<th>{ZONES[z]['name']} ({z})</th>" for z in zones_cols) + "</tr>"
    by_zone = {}
    for prov, z in sorted(PROV.items(), key=lambda x: x[0]):
        by_zone.setdefault(z, []).append(prov)
    zones_html = "".join(
        f"<li><b>{ZONES[z]['name']} (zona {ZONES[z]['code']})</b>: {', '.join(by_zone[z])}</li>"
        for z in ["alpha", "A", "B", "C", "D", "E"] if z in by_zone)
    prods = [dict(id=p["id"], c=p["category"], n=p["name"], kw=p["potencia_kw"], m2=p["superficie_calefactable_m2"],
                  r=p.get("valoracion_media") or 0, rc=p.get("resenas_cantidad") or 0)
             for p in PRODUCTS if p["category"] in ("pellets", "lena-biomasa", "electricos", "gas")
             and not any(x in p["id"] for x in ("outsunny", "evocamp", "exteriores"))]
    kw50c, kw80d, kw100d = need_kw(50, "C"), need_kw(80, "D"), need_kw(100, "D")

    body = f"""  <section class="layout calc" aria-labelledby="calcTitle">
    <form class="card inputs" onsubmit="return false" aria-label="Datos de tu casa">
      <div class="step">
        <h2><span class="num">1</span>Tu casa</h2>
        <div class="field">
          <label for="prov">Provincia</label>
          <select id="prov"></select>
          <div class="clima"><span>Clima: <b id="climaName"></b></span></div>
        </div>
        <div class="field">
          <label for="m2">Metros que quieres calentar <output id="m2Out"></output></label>
          <input type="range" id="m2" min="5" max="250" step="5" value="80">
          <div class="chips" id="m2Chips" role="group" aria-label="Superficies típicas">
            <button type="button" class="chip" data-v="10">Baño 10</button>
            <button type="button" class="chip" data-v="15">Dormitorio 15</button>
            <button type="button" class="chip" data-v="30">Salón 30</button>
            <button type="button" class="chip" data-v="80">Piso 80</button>
            <button type="button" class="chip" data-v="150">Casa 150</button>
          </div>
        </div>
        <div class="field">
          <span class="lbl">Aislamiento</span>
          <div class="seg c3" id="insSeg" role="group" aria-label="Aislamiento">
            <button type="button" data-v="buena">Bueno<small>Reformada o de 2007 en adelante</small></button>
            <button type="button" data-v="normal">Normal<small>Ventanas dobles, algo de frío</small></button>
            <button type="button" data-v="mala">Malo<small>Antigua, ventanas simples</small></button>
          </div>
        </div>
        <div class="field">
          <span class="lbl">Altura de los techos</span>
          <div class="seg c3" id="hSeg" role="group" aria-label="Altura de techos">
            <button type="button" data-v="2.5">Normal<small>Hasta 2,6 m</small></button>
            <button type="button" data-v="3">Altos<small>Unos 3 m</small></button>
            <button type="button" data-v="3.5">Muy altos<small>Casa antigua, buhardilla</small></button>
          </div>
        </div>
      </div>
    </form>

    <div class="results" aria-live="polite">
      <div class="card summary">
        <h2 id="calcTitle" style="color:#fff">Potencia que necesitas</h2>
        <div class="kpi-big"><b id="kw">–</b><span id="kwCtx"></span></div>
        <ul class="equiv" id="equiv" style="color:var(--text)"></ul>
      </div>
      <div class="card">
        <h2>Modelos que encajan</h2>
        <p class="sub" id="picksSub">Estufas de CalorBrasa que calientan tus metros, ordenadas por valoración.</p>
        <div class="picks" id="picks"></div>
      </div>
    </div>
  </section>

  <div class="below">
    <section class="card prose">
      <h2>Cómo se calcula la potencia</h2>
      <p>La regla rápida es <b>1 kW por cada 10 m²</b> en una casa normal. Nosotros afinamos un poco más:</p>
      <p><b>Potencia (kW) = metros × 95 W × clima × aislamiento × altura de techos</b></p>
      <ul>
        <li><b>Clima</b>: de 0,70 en las zonas más suaves (Canarias) a 1,20 en las más frías (Burgos, León, Soria…), según la zona climática de cada provincia del Código Técnico de la Edificación.</li>
        <li><b>Aislamiento</b>: 0,75 si es bueno, 1 si es normal y 1,35 si es malo.</li>
        <li><b>Techos</b>: con techos de 3 metros hay un 20 % más de aire que calentar que con 2,5 m.</li>
      </ul>
      <p>Por ejemplo, un piso de 80 m² en Madrid (clima frío) con aislamiento normal necesita unos <b>{nf(kw80d, 1)} kW</b>.</p>
    </section>

    <section class="card">
      <h2>Tabla de potencia según los metros y el clima</h2>
      <p class="sub">Aislamiento normal y techos de 2,5 m. Busca tu provincia en la lista de abajo para saber tu clima.</p>
      <div class="tw"><table class="data">
        <thead>{head}</thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table></div>
    </section>

    <section class="card prose">
      <h2>¿Qué clima tiene tu provincia?</h2>
      <p>Usamos la zona climática de invierno de la capital de cada provincia. Si vives en un pueblo de montaña o a más de 800 m de altura, elige un clima más frío.</p>
      <ul class="zones">{zones_html}</ul>
    </section>

    <section class="card prose">
      <h2>¿Qué pasa si eliges mal la potencia?</h2>
      <ul>
        <li><b>Si se queda corta</b>, la estufa trabaja siempre a tope, gasta más por hora y aun así no llega a calentar la casa los días de más frío.</li>
        <li><b>Si te pasas mucho</b>, la pagas más cara y trabaja casi siempre al mínimo. En las de pellets y leña eso ensucia el cristal y el tiro, y quema peor.</li>
        <li><b>Lo ideal</b> es que la potencia de la estufa sea igual o un poco mayor (hasta un 25 % más) que la que te da la calculadora.</li>
        <li>Las estufas de butano tienen como mucho <b>4,2 kW</b> y las eléctricas de enchufe unos 2–2,5 kW: para más potencia hacen falta varias, y entonces suele salir mejor una estufa de pellets o de leña.</li>
      </ul>
      <p>Cuando sepas los kW, mira <a href="{any_url('barata')}">qué calefacción te sale más barata</a> y <a href="{any_url('home')}">cuánto te costará al mes</a>.</p>
    </section>
  </div>"""

    fq = [
        ("¿Qué potencia de estufa necesito para 50 m²?",
         f"Unos {nf(kw50c, 1)} kW en clima fresco (zona C) con aislamiento normal, y unos {nf(need_kw(50, 'D'), 1)} kW en clima frío como Madrid. Con mal aislamiento, un 35 % más."),
        ("¿Y para 80 o 100 m²?",
         f"En clima frío y con aislamiento normal, unos {nf(kw80d, 1)} kW para 80 m² y unos {nf(kw100d, 1)} kW para 100 m². Para tanta superficie lo más práctico es una estufa de pellets o de leña."),
        ("¿Cuántos metros calienta una estufa eléctrica de 2.000 W?",
         f"Unos {nf(2 / (BASE_W * ZONES['C']['f'] / 1000))} m² en clima fresco y unos {nf(2 / (BASE_W * ZONES['D']['f'] / 1000))} m² en clima frío, con aislamiento normal. Es la potencia típica para un dormitorio o un salón pequeño."),
        ("¿Cuántos metros calienta una estufa de butano?",
         f"Una de 4.200 W, unos {nf(4.2 / (BASE_W * ZONES['D']['f'] / 1000))} m² en clima frío y aislamiento normal. Para más superficie harían falta varias, y no conviene: hay que ventilar."),
        ("¿Cuántos metros calienta una estufa de pellets de 8 kW?",
         f"Unos {nf(8 / (BASE_W * ZONES['C']['f'] / 1000))} m² en clima fresco y unos {nf(8 / (BASE_W * ZONES['D']['f'] / 1000))} m² en clima frío, con aislamiento normal."),
        ("¿Es mejor pasarse o quedarse corto de potencia?",
         "Mejor un poco por encima, hasta un 25 % más. Quedarse corto significa pasar frío los peores días; pasarse mucho hace que la estufa trabaje al mínimo, se ensucie y gaste peor."),
    ]
    script = f"""<script>
const ZONES = {json.dumps(ZONES, ensure_ascii=False)};
const PROV = {json.dumps(PROV, ensure_ascii=False)};
const INS = {json.dumps(INS)};
const PRODUCTS = {json.dumps(prods, ensure_ascii=False)};
const CB = "{CB}";
const CAT = {json.dumps({k: CAT_URL[k] for k in ("pellets", "lena-biomasa", "electricos", "gas")})};
const GUIDE = {json.dumps({"pellets": any_url("pellets"), "lena-biomasa": any_url("lena"), "electricos": any_url("electrica"), "gas": any_url("butano")})};
{POT_JS}
</script>"""
    return shell(
        "potencia",
        "¿Qué potencia de estufa necesito? Calculadora de kW según los m²",
        f"Calcula los kW que necesitas según los metros, tu provincia, el aislamiento y la altura de techos, y qué estufa de pellets, leña, butano o eléctrica encaja. Ejemplo: 80 m² en Madrid, unos {nf(kw80d, 1)} kW.",
        "Calcula cuántos kW necesitas para tus metros, según tu provincia, el aislamiento y la altura de los techos, y qué estufas encajan con tu casa.",
        f"La regla rápida es <b>1 kW por cada 10 m²</b>. Afinando con el clima: un piso de 80 m² con aislamiento normal necesita unos <b>{nf(need_kw(80, 'C'), 1)} kW</b> en clima fresco y unos <b>{nf(kw80d, 1)} kW</b> en clima frío como Madrid. Con mal aislamiento o techos altos, bastante más.",
        body, fq, (CB + "productos.html", "Ver estufas en CalorBrasa →"), script)


POT_JS = r"""
const $ = id => document.getElementById(id);
const nf = (v, d = 0) => v.toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
const S = { prov: "Madrid", m2: 80, ins: "normal", h: 2.5 };
const score = p => ((p.r || 0) * (p.rc || 0) + 4.3 * 15) / ((p.rc || 0) + 15);
const NAMES = { pellets: "De pellets", "lena-biomasa": "De leña", electricos: "Eléctricas", gas: "De butano" };
function pick(cat, m2) {
  const list = PRODUCTS.filter(p => p.c === cat);
  const fit = list.filter(p => p.m2 >= m2);
  if (!fit.length) return { chosen: [...list].sort((a, b) => b.m2 - a.m2 || score(b) - score(a)).slice(0, 3), fits: false };
  let pool = fit.filter(p => p.m2 <= Math.max(m2 * 1.6, m2 + 15));
  if (pool.length < 3) pool = [...fit].sort((a, b) => a.m2 - b.m2).slice(0, 6);
  return { chosen: [...pool].sort((a, b) => score(b) - score(a)).slice(0, 3), fits: true };
}
function render() {
  const z = ZONES[PROV[S.prov]];
  const kw = S.m2 * 95 * z.f * INS[S.ins] * (S.h / 2.5) / 1000;
  $("climaName").textContent = `${z.name} (zona ${z.code})`;
  $("m2Out").textContent = `${S.m2} m²`;
  $("kw").textContent = `${nf(kw, 1)} kW`;
  $("kwCtx").textContent = `para ${S.m2} m² en ${S.prov} · ${nf(kw * 1000 / S.m2)} W por m²`;
  const hi = Math.ceil(kw * 1.25 * 2) / 2, lo = Math.max(0.5, Math.round(kw * 2) / 2);
  const e = [];
  const nE = Math.ceil(kw / 2), nB = Math.ceil(kw / 4.2);
  e.push(nE <= 1 ? `<b>Una estufa o radiador eléctrico de ${kw <= 1 ? "1.000" : kw <= 1.5 ? "1.500" : "2.000"} W</b> te basta. <a href="${GUIDE.electricos}">¿Cuánto gasta?</a>`
                 : `Con electricidad, <b>${nE} aparatos de 2.000 W</b>: para tanta superficie sale caro. <a href="${GUIDE.electricos}">¿Cuánto gasta?</a>`);
  e.push(nB <= 1 ? `<b>Una estufa de butano</b> (4,2 kW) llega, ventilando la habitación. <a href="${GUIDE.gas}">¿Cuánto gasta?</a>`
                 : `Con butano harían falta <b>${nB} estufas</b>: no es buena idea, mejor como apoyo puntual. <a href="${GUIDE.gas}">¿Cuánto gasta?</a>`);
  e.push(kw < 4 ? `Una estufa de pellets o de leña sería demasiado grande para tan pocos metros.`
                : `<b>Una estufa de pellets o de leña de ${nf(lo, 1)} a ${nf(hi, 1)} kW</b>. <a href="${GUIDE.pellets}">¿Cuánto gasta?</a>`);
  if (kw > 15) e.push(`Para más de 15 kW, mira estufas de pellets canalizables o una caldera.`);
  $("equiv").innerHTML = e.map(x => `<li>${x}</li>`).join("");
  const cats = kw < 4 ? ["electricos", "gas"] : ["pellets", "lena-biomasa", "electricos", "gas"];
  $("picks").innerHTML = cats.map(c => {
    const { chosen, fits } = pick(c, S.m2);
    if (!chosen.length) return "";
    const note = fits ? "" : ` <small>(ninguna llega a ${S.m2} m² sola: estas son las más potentes)</small>`;
    return `<div><h3>${NAMES[c]}${note}</h3><ul>${chosen.map(p => `<li><a href="${CB}producto/${p.id}.html">${p.n}</a> <small>· ${nf(p.kw, 1)} kW · hasta ${p.m2} m²</small></li>`).join("")}</ul>
      <small><a href="${CAT[c]}">Ver todas →</a></small></div>`;
  }).join("");
}
const sel = $("prov");
sel.innerHTML = Object.keys(PROV).sort((a, b) => a.localeCompare(b, "es")).map(p => `<option${p === S.prov ? " selected" : ""}>${p}</option>`).join("");
sel.onchange = () => { S.prov = sel.value; render(); };
const press = (id, val) => $(id).querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.v === String(val))));
$("m2").oninput = e => { S.m2 = +e.target.value; press("m2Chips", ""); render(); };
$("m2Chips").onclick = e => { const b = e.target.closest("button"); if (!b) return; S.m2 = +b.dataset.v; $("m2").value = S.m2; press("m2Chips", S.m2); render(); };
$("insSeg").onclick = e => { const b = e.target.closest("button"); if (!b) return; S.ins = b.dataset.v; press("insSeg", S.ins); render(); };
$("hSeg").onclick = e => { const b = e.target.closest("button"); if (!b) return; S.h = +b.dataset.v; press("hSeg", b.dataset.v); render(); };
press("insSeg", S.ins); press("hSeg", "2.5"); press("m2Chips", S.m2);
render();
"""


# ---------------------------------------------------------------- MÁS BARATA
def barata_page():
    systems = [
        ("bdc", "Bomba de calor (aire acondicionado con bomba de calor)", (c_bdc_low, c_bdc_high), "Hace falta tener el aparato instalado", None),
        ("gn", "Caldera de gas natural", (c_gn_low, c_gn_high), "Solo si tienes gas natural en casa", None),
        ("pellet", "Estufa de pellets", cpk("pellet"), "Necesita salida de humos", CAT_URL["pellets"]),
        ("lena", "Estufa de leña", cpk("lena"), "Necesita salida de humos", CAT_URL["lena-biomasa"]),
        ("butano", "Estufa de butano", cpk("butano"), "Sin instalación; hay que ventilar", CAT_URL["gas"]),
        ("gasoleo", "Caldera de gasóleo", cpk("gasoleo"), "Precio en subida", None),
        ("luz", "Estufa o radiador eléctrico", cpk("luz"), "Enchufar y listo", CAT_URL["electricos"]),
        ("chimenea", "Chimenea abierta de leña", cpk("chimenea"), "Se pierde el 80 % del calor", None),
    ]

    def cval(c):
        return c if isinstance(c, float) else (c[0] + c[1]) / 2

    def ctext(c, mult=100, unit=" cts"):
        if isinstance(c, tuple):
            return f"{nf(c[0] * mult, 0 if mult > 100 else 1)}–{nf(c[1] * mult, 0 if mult > 100 else 1)}{unit}"
        return f"{nf(c * mult, 0 if mult > 100 else 1)}{unit}"

    rows = []
    for i, (k, name, c, tag, url) in enumerate(sorted(systems, key=lambda s: cval(s[2]))):
        nm = f'<a href="{url}">{name}</a>' if url else name
        rows.append(f"<tr><td>{i + 1}</td><td>{nm}</td><td><b>{ctext(c)}</b></td><td>{ctext(c, 1000, ' €')}</td><td>{tag}</td></tr>")

    scen = [("Piso de 60 m² en Valencia", 60, "B"), ("Piso de 80 m² en Madrid", 80, "D"), ("Casa de 150 m² en Burgos", 150, "E")]
    scen_sys = [("Bomba de calor", (c_bdc_low, c_bdc_high)), ("Gas natural", (c_gn_low, c_gn_high)), ("Pellets", cpk("pellet")),
                ("Leña", cpk("lena")), ("Butano*", cpk("butano")), ("Gasóleo", cpk("gasoleo")), ("Eléctrica", cpk("luz"))]
    s_head = "<tr><th>Sistema</th>" + "".join(f"<th>{n}<br><small>{nf(rnd(season_kwh(m, z)))} kWh al año</small></th>" for n, m, z in scen) + "</tr>"
    s_rows = []
    for name, c in scen_sys:
        cells = []
        for _, m, z in scen:
            E = season_kwh(m, z)
            cells.append(f"<td>{nf(rnd(E * c[0]))}–{eur(rnd(E * c[1]), 0)}</td>" if isinstance(c, tuple) else f"<td><b>{eur(rnd(E * c), 0)}</b></td>")
        s_rows.append(f"<tr><td>{name}</td>{''.join(cells)}</tr>")

    E80 = season_kwh(80, "D")
    go, pl = E80 * cpk("gasoleo"), E80 * cpk("pellet")
    save = go - pl
    ratio_luz_pel = cpk("luz") / cpk("pellet")

    body = f"""  <div class="below" style="margin-top:22px">
    <section class="card">
      <h2>Lo que cuesta cada kWh de calor</h2>
      <p class="sub">Precio de cada kWh de calor que llega a tu casa, ya descontado lo que se pierde por el camino. Es la forma justa de comparar sistemas.</p>
      <div class="tw"><table class="data">
        <thead><tr><th></th><th>Sistema</th><th>Coste por kWh de calor</th><th>1.000 kWh de calor</th><th>A tener en cuenta</th></tr></thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table></div>
      <p class="note">Precios de {PRICES_TXT}: luz a {nf(LUZ, 2)} €/kWh, bombona de butano a {eur(P['bombona'], 2)}, saco de pellets de 15 kg a {eur(P['saco'], 2)}, leña seca a {nf(P['lena'], 2)} €/kg y gasóleo a {nf(P['gasoleo'], 2)} €/litro.
      Gas natural: tarifa regulada (TUR) desde el 1 de octubre de 2026, de {nf(GAS_TUR_LOW * 100, 1)} céntimos/kWh antes de impuestos según <a href="https://www.papernest.es/estudios/tur-gas-octubre-2026/" target="_blank" rel="noopener">papernest</a> a {nf(GAS_TUR_HIGH * 100, 1)} según la estimación de la <a href="https://www.ocu.org/vivienda-y-energia/gas-luz/noticias/subida-tur-octubre-2026" target="_blank" rel="noopener">OCU</a>; les sumamos impuestos y una caldera que rinde al 90 %, sin contar la cuota fija mensual.
      Bomba de calor: entre 3 y 4 kWh de calor por cada kWh de luz, según el aparato y el frío que haga.</p>
    </section>

    <section class="card">
      <h2>Lo que cuesta un invierno en tres casas</h2>
      <p class="sub">Aislamiento normal y uso habitual en cada clima: 5 h al día durante 4 meses en Valencia, 7 h durante 6 meses en Madrid y 8 h durante 7 meses en Burgos.</p>
      <div class="tw"><table class="data">
        <thead>{s_head}</thead>
        <tbody>
{chr(10).join(s_rows)}
        </tbody>
      </table></div>
      <p class="note">* Una estufa de butano llega a unos 40 m²: para un piso entero harían falta varias y no es recomendable. Calcula tu propia casa en la <a href="{BASE}">calculadora de calefacción</a>.</p>
    </section>

    <section class="card prose">
      <h2>¿Cuál te conviene a ti?</h2>
      <ul>
        <li><b>Si tienes aire acondicionado con bomba de calor</b>, úsalo: es lo más barato por kWh, sobre todo en climas suaves. Un aparato de enchufe gasta {nf(cpk('luz') / c_bdc_high, 0)}–{nf(cpk('luz') / c_bdc_low, 0)} veces más por el mismo calor.</li>
        <li><b>Si tienes gas natural</b>, la caldera sigue siendo de lo más barato aunque la tarifa haya subido en octubre. Ajusta el termostato y revisa si te compensa la TUR o una oferta del mercado libre.</li>
        <li><b>Si tienes casa con chimenea o puedes poner salida de humos</b>, una <a href="{CAT_URL['pellets']}">estufa de pellets</a> es la opción barata y cómoda (se programa y tiene termostato). Si tienes leña propia o barata, la <a href="{CAT_URL['lena-biomasa']}">estufa de leña</a> sale aún mejor.</li>
        <li><b>Si calientas con gasóleo</b>, una estufa de pellets te ahorra alrededor de un {nf((1 - cpk('pellet') / cpk('gasoleo')) * 100)} %: en un piso de 80 m² en Madrid, unos {eur(rnd(save), 0)} al año. Con una estufa de unos 1.500 € instalada, se paga en unos {math.ceil(1500 / save)} inviernos.</li>
        <li><b>Si vives en un piso sin salida de humos y sin aire acondicionado</b>, calienta solo donde estás: <a href="{CAT_URL['radiadores']}">radiadores</a> o <a href="{CAT_URL['electricos']}">estufas eléctricas</a> con termostato para ratos cortos, o una <a href="{CAT_URL['gas']}">estufa de butano</a> como apoyo en el salón, ventilando.</li>
        <li><b>Para una segunda residencia o pocas horas al mes</b>, manda el precio de compra: una eléctrica o una de butano cuestan poco y el gasto por hora importa menos si casi no la usas.</li>
      </ul>
      <p>¿No sabes qué potencia necesitas? Usa la <a href="{any_url('potencia')}">calculadora de potencia según los m²</a>.</p>
    </section>

    <section class="card prose">
      <h2>Trucos para pagar menos con cualquier calefacción</h2>
      <ul>
        <li><b>Termostato a 19–20 °C.</b> Cada grado de más sube el gasto alrededor de un 7 %.</li>
        <li><b>Calienta solo las habitaciones que usas</b> y cierra las puertas de las demás.</li>
        <li><b>Tapa las fugas de aire</b>: burletes en puertas y ventanas, y persianas bajadas al anochecer.</li>
        <li><b>Mantenimiento</b>: una estufa de pellets o una caldera sucia quema peor y gasta más.</li>
      </ul>
    </section>
  </div>"""

    fq = [
        ("¿Qué calefacción es más barata para un piso?",
         f"Si tienes bomba de calor (aire acondicionado frío-calor), es lo más barato de usar: unos {nf(c_bdc_low * 100, 0)}–{nf(c_bdc_high * 100, 0)} céntimos por kWh de calor. Le siguen el gas natural y, si el piso tiene salida de humos, la estufa de pellets ({nf(cpk('pellet') * 100, 1)} céntimos). Sin ninguna de esas opciones, calienta solo donde estás con aparatos eléctricos o butano."),
        ("¿Es más barato el aire acondicionado que una estufa eléctrica?",
         f"Sí, si tiene bomba de calor: por cada kWh de luz da entre 3 y 4 kWh de calor, así que calentar te cuesta entre la tercera y la cuarta parte que con una estufa eléctrica de resistencia."),
        ("¿Qué es más barato, pellets o gas natural?",
         f"Con la tarifa regulada de octubre de 2026, muy parecido: el gas natural sale a unos {nf(c_gn_low * 100, 0)}–{nf(c_gn_high * 100, 0)} céntimos por kWh de calor (más la cuota fija) y los pellets a {nf(cpk('pellet') * 100, 1)} céntimos. Si ya tienes caldera de gas, no compensa cambiar solo por el precio."),
        ("¿Qué calefacción es más barata sin obras?",
         f"Sin instalación, el butano ({nf(cpk('butano') * 100, 1)} céntimos por kWh) es más barato de usar que una estufa eléctrica ({nf(cpk('luz') * 100, 1)} céntimos), pero hay que ventilar y no sirve para dormitorios ni baños. Si tienes aire acondicionado con bomba de calor, gana a los dos."),
        ("¿Compensa cambiar la caldera de gasóleo por una estufa de pellets?",
         f"Con los precios de {PRICES_TXT}, sí: el calor sale alrededor de un {nf((1 - cpk('pellet') / cpk('gasoleo')) * 100)} % más barato. En un piso de 80 m² en Madrid ahorrarías unos {eur(rnd(save), 0)} al año."),
        ("¿Cuánto más cara es una estufa eléctrica que una de pellets?",
         f"Por el mismo calor, unas {nf(ratio_luz_pel, 1)} veces más: {nf(cpk('luz') * 100, 1)} céntimos por kWh frente a {nf(cpk('pellet') * 100, 1)}. Por eso la eléctrica conviene para ratos cortos o habitaciones pequeñas."),
    ]
    return shell(
        "barata",
        "¿Qué calefacción es más barata en 2026? Comparativa de costes",
        f"La bomba de calor es lo más barato de usar ({nf(c_bdc_low * 100, 0)}–{nf(c_bdc_high * 100, 0)} céntimos por kWh), seguida del gas natural y los pellets; la estufa eléctrica cuesta {nf(cpk('luz') * 100, 0)}. Comparamos 8 sistemas y el gasto de un invierno en 3 casas.",
        "Comparamos lo que cuesta calentar tu casa con cada sistema (bomba de calor, gas natural, pellets, leña, butano, gasóleo y electricidad) con los precios de este invierno.",
        f"Con los precios de este otoño, lo más barato de usar es la <b>bomba de calor</b> (unos {nf(c_bdc_low * 100, 0)}–{nf(c_bdc_high * 100, 0)} céntimos por kWh de calor), seguida del <b>gas natural</b> ({nf(c_gn_low * 100, 0)}–{nf(c_gn_high * 100, 0)} céntimos) y las <b>estufas de pellets</b> ({nf(cpk('pellet') * 100, 1)}) y <b>de leña</b> ({nf(cpk('lena') * 100, 1)}). El butano sale a {nf(cpk('butano') * 100, 1)}, el gasóleo a {nf(cpk('gasoleo') * 100, 1)} y la <b>estufa eléctrica a {nf(cpk('luz') * 100, 1)} céntimos</b>: más del doble que los pellets.",
        body, fq, (CB + "comparador.html", "Comparar estufas →"))


# ---------------------------------------------------------------- SEGURIDAD BUTANO
def seguridad_page():
    body = f"""  <div class="below" style="margin-top:22px">
    <section class="card prose">
      <h2>Los riesgos reales</h2>
      <p>Una estufa de butano quema el gas dentro de la habitación, sin chimenea. Todo lo que produce la llama se queda en casa, y por eso hay que usarla bien.</p>
      <div class="risk">
        <div><b>Falta de oxígeno</b><p>La llama consume el oxígeno del aire. En una habitación pequeña y cerrada puede bajar lo bastante como para causar mareos.</p></div>
        <div><b>Monóxido de carbono</b><p>Si el gas no se quema bien (poco oxígeno, quemador sucio o averiado) aparece monóxido: un gas sin olor ni color que intoxica.</p></div>
        <div><b>Humedad</b><p>Quemar butano produce vapor de agua: unos {nf(b_water, 1)} litros por hora a potencia media. En casas frías se condensa en ventanas y paredes.</p></div>
        <div><b>Fugas de gas</b><p>Una goma vieja o agrietada, o un regulador mal puesto, pueden dejar escapar gas. El butano pesa más que el aire y se acumula abajo.</p></div>
        <div><b>Incendio y quemaduras</b><p>La parte delantera se calienta mucho: cortinas, ropa o muebles demasiado cerca pueden prender.</p></div>
        <div><b>Vuelcos</b><p>Al moverla o si la tira un niño o una mascota. Por eso muchas llevan sistema antivuelco.</p></div>
      </div>
    </section>

    <section class="card prose">
      <h2>Los sistemas de seguridad que debe tener</h2>
      <ul>
        <li><b>Analizador de atmósfera (ODS)</b>: corta el gas si el oxígeno del aire baja. Lo llevan de serie las estufas actuales; si la tuya es muy antigua y no lo tiene, cámbiala.</li>
        <li><b>Válvula de seguridad con termopar</b>: corta el gas si la llama se apaga, para que no salga gas sin quemar.</li>
        <li><b>Antivuelco</b>: apaga la estufa si se cae. Muy recomendable con niños o mascotas.</li>
      </ul>
      <p>La norma europea de estas estufas sin salida de humos (EN 449) es para aparatos de hasta 4,2 kW: por eso casi todas las estufas de butano tienen esa potencia. Puedes ver los modelos y sus sistemas de seguridad en las <a href="{CAT_URL['gas']}">estufas de butano de CalorBrasa</a>.</p>
    </section>

    <section class="card prose">
      <h2>8 reglas para usarla sin peligro</h2>
      <ol class="rules">
        <li><b>Ventila.</b> Deja una rendija abierta o abre la ventana unos minutos cada pocas horas.</li>
        <li><b>Nunca en el dormitorio ni en el baño</b>, y nunca te duermas con ella encendida.</li>
        <li><b>No la uses en sitios pequeños y cerrados</b>, como un baño, un trastero o una caravana sin ventilación.</li>
        <li><b>Deja espacio libre delante</b>, de al menos un metro, y no seques ropa encima ni la tapes.</li>
        <li><b>Revisa la goma</b>: lleva la fecha de caducidad impresa. Si ha caducado o está agrietada, cámbiala.</li>
        <li><b>Cambia la bombona con la estufa apagada</b> y lejos de cualquier llama. Para buscar fugas usa agua con jabón (salen burbujas), nunca una cerilla o un mechero.</li>
        <li><b>Guarda las bombonas de repuesto</b> de pie, en un sitio ventilado, nunca en sótanos ni cerca del calor.</li>
        <li><b>Pon un detector de monóxido de carbono</b> en la habitación. Cuesta poco y avisa antes de que notes nada.</li>
      </ol>
    </section>

    <section class="card prose">
      <h2>Señales de alarma: qué hacer</h2>
      <div class="alert">
        <p><b>Si notas dolor de cabeza, mareo, náuseas, cansancio o mucho sueño</b> mientras la estufa está encendida, puede ser monóxido de carbono: apágala, abre las ventanas, sal al aire libre y llama al <b>112</b>.</p>
        <p><b>Si huele a gas</b>: cierra la llave de la bombona, no enciendas ni apagues luces ni aparatos, abre puertas y ventanas y sal de casa. Si el olor sigue, llama al 112.</p>
        <p><b>Si la llama es amarilla o anaranjada</b> en una estufa de llama azul, está quemando mal: apágala y que la revise un técnico.</p>
      </div>
    </section>

    <section class="card">
      <h2>¿Butano o eléctrica? Según la habitación</h2>
      <p class="sub">Para algunos sitios es mejor otra estufa.</p>
      <div class="tw"><table class="data">
        <thead><tr><th>Dónde</th><th>Mejor opción</th><th>Por qué</th></tr></thead>
        <tbody>
          <tr><td>Dormitorio</td><td><a href="{CAT_URL['radiadores']}">Radiador eléctrico</a></td><td>No consume oxígeno, es silencioso y se puede dejar con termostato.</td></tr>
          <tr><td>Baño</td><td><a href="{CB}producto/electricos-orbegozo-sp6000.html">Calefactor de baño</a></td><td>Calienta en minutos y está pensado para la humedad del baño.</td></tr>
          <tr><td>Salón, a ratos</td><td><a href="{CAT_URL['gas']}">Estufa de butano</a></td><td>Mucho calor y gasta menos que una eléctrica, ventilando de vez en cuando.</td></tr>
          <tr><td>Casa con humedad</td><td><a href="{CAT_URL['pellets']}">Pellets</a> o <a href="{CAT_URL['electricos']}">eléctrica</a></td><td>El butano añade vapor de agua y empeora la condensación.</td></tr>
          <tr><td>Toda la casa</td><td><a href="{CAT_URL['pellets']}">Estufa de pellets</a> o de leña</td><td>Una de butano no pasa de unos 40 m² y habría que ventilar mucho.</td></tr>
        </tbody>
      </table></div>
      <p class="note">¿Y lo que gasta? Mira <a href="{any_url('butano')}">cuánto gasta una estufa de butano</a> por hora y cuánto dura la bombona.</p>
    </section>
  </div>"""
    fq = [
        ("¿Se puede dormir con una estufa de butano encendida?",
         "No. Mientras duermes no notarías si falta oxígeno o aparece monóxido de carbono. Apágala antes de acostarte y no la uses en dormitorios."),
        ("¿Una estufa de butano puede dar monóxido de carbono?",
         "Sí, si el gas no se quema bien: por falta de oxígeno, un quemador sucio o una avería. Por eso hay que ventilar, revisarla y, mejor aún, tener un detector de monóxido."),
        ("¿Cada cuánto hay que ventilar con una estufa de butano?",
         "Lo más sencillo es dejar una rendija de la ventana abierta mientras funciona. Si no, abre unos minutos cada pocas horas, y siempre que notes el ambiente cargado."),
        ("¿Caduca la goma del butano?",
         "Sí. La fecha de caducidad viene impresa en la propia goma: cámbiala antes de esa fecha o en cuanto la veas agrietada o reseca."),
        ("¿Es seguro usar una estufa de butano en un piso?",
         "Sí, en el salón o en habitaciones amplias y ventilando, con una estufa que tenga analizador de atmósfera. No en dormitorios ni baños, ni en casas con mucha humedad."),
        ("¿Qué estufa de butano es más segura?",
         "Cualquiera actual con analizador de atmósfera, válvula de seguridad y antivuelco. Las de llama azul, infrarrojos y catalíticas son igual de seguras si se usan bien; cambia sobre todo cómo dan el calor."),
    ]
    return shell(
        "seguridad",
        "¿Es peligrosa una estufa de butano? Riesgos y cómo usarla segura",
        "Bien usada, una estufa de butano es segura. Los riesgos reales (falta de oxígeno, monóxido, humedad y fugas), los sistemas de seguridad que debe llevar y 8 reglas para usarla sin peligro.",
        "Los riesgos reales de una estufa de butano, los sistemas de seguridad que debe llevar, las reglas para usarla tranquilo y qué hacer si algo va mal.",
        "<b>No, si se usa bien.</b> Las estufas de butano actuales llevan un <b>analizador de atmósfera</b> que corta el gas si baja el oxígeno, y una <b>válvula de seguridad</b> que lo corta si se apaga la llama. El peligro aparece al usarla en sitios pequeños y cerrados, sin ventilar o para dormir: puede faltar oxígeno y acumularse <b>monóxido de carbono</b>.",
        body, fq, (CAT_URL["gas"], "Ver estufas de butano →"), prices=False)


GUIDE_BUILDERS = {"potencia": potencia_page, "barata": barata_page, "seguridad": seguridad_page}


def sitemap():
    urls = [(BASE, "1.0")] + [(any_url(k), "0.8") for k in list(PAGES) + list(GUIDES)]
    body = "\n".join(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{UPDATED_ISO}</lastmod>\n    <priority>{pr}</priority>\n  </url>" for u, pr in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


if __name__ == "__main__":
    for k, pg in PAGES.items():
        out = ROOT / (pg["slug"] + ".html")
        out.write_text(page(k), encoding="utf-8")
        print("escrito", out.name, len(out.read_bytes()), "bytes")
    for k, fn in GUIDE_BUILDERS.items():
        out = ROOT / (GUIDES[k]["slug"] + ".html")
        out.write_text(fn(), encoding="utf-8")
        print("escrito", out.name, len(out.read_bytes()), "bytes")
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    print("escrito sitemap.xml")
