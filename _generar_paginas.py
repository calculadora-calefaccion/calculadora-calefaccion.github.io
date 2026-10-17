#!/usr/bin/env python3
"""Genera las páginas "¿Cuánto gasta una estufa de ...?" de la calculadora.

Uso:  python3 _generar_paginas.py [ruta/a/products.json]

- Los precios se leen de la constante DEF de index.html (una sola fuente).
- El catálogo se lee de products.json de CalorBrasa (por defecto, desde la web).
- Vuelve a ejecutarlo cada vez que cambien los precios en index.html.
Los archivos que empiezan por "_" no se publican en GitHub Pages.
"""
import html
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


def nav_html(active):
    links = [f'<a class="star" href="{CB}">★ CalorBrasa</a>', f'<a href="{BASE}">Calculadora</a>']
    for k, pg in PAGES.items():
        cls = ' class="on"' if k == active else ""
        links.append(f'<a{cls} href="{BASE}{pg["slug"]}.html">Gasto {pg["nav"].lower()}</a>')
    links.append(f'<a href="{CB}comparador.html">Comparador de estufas</a>')
    return "\n    ".join(links)


def related(active):
    cards = []
    desc = {
        "butano": "Por hora, cuánto dura la bombona y al mes.",
        "electrica": "800, 1.500 y 2.000 W por hora y al mes.",
        "pellets": "Kilos por hora, sacos al mes y por invierno.",
        "lena": "Kilos por hora y leña para todo el invierno.",
    }
    for k, pg in PAGES.items():
        if k == active:
            continue
        cards.append(f'<a href="{BASE}{pg["slug"]}.html"><b>{pg["h1"]}</b><span>{desc[k]}</span></a>')
    cards.append(f'<a href="{BASE}"><b>¿Cuánto te cuesta calentar tu casa?</b><span>Calcula qué estufa te sale más barata para tus metros.</span></a>')
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


def sitemap():
    urls = [(BASE, "1.0")] + [(BASE + pg["slug"] + ".html", "0.8") for pg in PAGES.values()]
    body = "\n".join(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{UPDATED_ISO}</lastmod>\n    <priority>{pr}</priority>\n  </url>" for u, pr in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


if __name__ == "__main__":
    for k, pg in PAGES.items():
        out = ROOT / (pg["slug"] + ".html")
        out.write_text(page(k), encoding="utf-8")
        print("escrito", out.name, len(out.read_bytes()), "bytes")
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    print("escrito sitemap.xml")
