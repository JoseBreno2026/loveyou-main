import streamlit as st
import streamlit.components.v1 as components
import json
import math as m
import random as r

# Configuração da página no Streamlit
st.set_page_config(
    page_title="Love Heart",
    page_icon="❤️",
    layout="centered"
)

# --- LÓGICA E CONSTANTES DO CÓDIGO ORIGINAL ---
SC = 21
OY = 20
DURATION = 10
TICK = 16
ANIM = 42
LIFT = 34
GAP = 7
SIZES = (9, 10, 11, 12)
FONT = "Arial"
BG = "#060208"

PHRASES = [
    "I love you", "Seni seviyorum", "Te amo", "Je t'aime",
    "Ich liebe dich", "Ti amo", "Eu te amo", "Я тебя люблю",
    "사랑해", "愛してる", "我爱你", "मैं तुमसे प्यार करता हूँ",
    "Σ' αγαπώ", "Ik hou van jou", "Jag älskar dig", "Kocham cię",
    "ฉันรักเธอ", "Anh yêu em", "Aku cinta kamu", "Я тебе кохаю",
]

rng = r.Random(11)

def heart(a):
    x = 16 * (m.sin(a) ** 3)
    y = (
        13 * m.cos(a)
        - 5 * m.cos(2 * a)
        - 2 * m.cos(3 * a)
        - m.cos(4 * a)
    )
    return x * SC, y * SC + OY

def mix(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b))

POLY = [heart(2 * m.pi * i / 720) for i in range(720)]
EDGES = list(zip(POLY, POLY[1:] + POLY[:1]))
YMAX = max(p[1] for p in POLY)
YMIN = min(p[1] for p in POLY)
CY = (YMAX + YMIN) / 2

def spans(y):
    xs = []
    for (x1, y1), (x2, y2) in EDGES:
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2]))

def intersect(A, B):
    out = []
    for a in A:
        for b in B:
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi - lo > 14:
                out.append((lo, hi))
    return out

def phrase_cycle():
    while True:
        order = PHRASES[:]
        rng.shuffle(order)
        yield from order

def math_dist(x, y):
    return m.hypot(x / (16 * SC), (y - CY) / (14.5 * SC))

def build():
    cycle = phrase_cycle()
    row_h = 16  # estimativa de altura de linha em pixels
    half = row_h / 2
    placed = []

    y = YMAX - half
    while y > YMIN + half:
        row = intersect(spans(y + half), spans(y - half))

        for lo, hi in row:
            lo += 4
            hi -= 4
            cur = lo + rng.uniform(0, 8)
            line = []

            while True:
                fit = None
                for _ in range(10):
                    text = next(cycle)
                    size = rng.choice(SIZES)
                    # Estimativa aproximada de largura por tamanho de fonte
                    w = len(text) * size * 0.65
                    if cur + w <= hi:
                        fit = (text, size, w)
                        break
                if not fit:
                    break
                text, size, w = fit
                line.append([cur + w / 2, text, size, w])
                cur += w + GAP

            if not line:
                continue

            if len(line) > 1:
                left = hi - (line[-1][0] + line[-1][3] / 2)
                for i, it in enumerate(line):
                    it[0] += left * i / (len(line) - 1)
            else:
                line[0][0] = (lo + hi) / 2

            for i, (x, text, size, w) in enumerate(line):
                edge = i == 0 or i == len(line) - 1
                placed.append(dict(x=x, y=y, text=text, size=size, edge=edge))

        y -= row_h

    wine = (0.58, 0.0, 0.09)
    crimson = (0.90, 0.05, 0.14)
    blood = (0.98, 0.10, 0.16)
    for p in placed:
        rad = min(1.0, math_dist(p["x"], p["y"]))
        base = mix(wine, crimson, 0.25 + 0.75 * rad)
        base = mix(base, blood, rng.uniform(0, 0.35) + (0.3 if p["edge"] else 0))
        p["color"] = [min(1.0, v) for v in base]
        p["rad"] = rad

    edges = [p for p in placed if p["edge"]]
    inner = [p for p in placed if not p["edge"]]
    edges.sort(key=lambda p: m.atan2(p["x"], p["y"] - CY) % (2 * m.pi))
    inner.sort(key=lambda p: -p["rad"] + rng.uniform(0, 0.08))
    return edges + inner

# Gera os dados calculados do coração no Python
placed_items = build()
items_json = json.dumps(placed_items)

# --- RENDERIZADOR WEB EM HTML5 CANVAS/JS EMBUTIDO ---
html_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0;
        background-color: {BG};
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        overflow: hidden;
    }}
    canvas {{
        background-color: {BG};
    }}
</style>
</head>
<body>
<canvas id="canvas" width="800" height="800"></canvas>
<script>
    const items = {items_json};
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");

    const BG = "{BG}";
    const FONT = "{FONT}";
    const ANIM = {ANIM};
    const LIFT = {LIFT};
    const TICK = {TICK};
    const DURATION = {DURATION};
    const FLASH = [1.0, 0.78, 0.78];
    const BGC = [6/255, 2/255, 8/255];

    let active = [];
    let main_ids = [];
    let spawning = true;
    let acc = 0.0;
    let index = 0;
    const RATE = items.length / (DURATION * 1000 / TICK);

    function hx(c) {{
        let r = Math.floor(Math.max(0, Math.min(1, c[0])) * 255);
        let g = Math.floor(Math.max(0, Math.min(1, c[1])) * 255);
        let b = Math.floor(Math.max(0, Math.min(1, c[2])) * 255);
        return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }}

    function mix(a, b, k) {{
        return a.map((p, i) => p + (b[i] - p) * k);
    }}

    function dim(c, k) {{
        return c.map(v => v * k);
    }}

    function clamp(v) {{
        return Math.max(0.0, Math.min(1.0, v));
    }}

    function spawn(p) {{
        p.f = 0;
        p.dx = (Math.random() - 0.5) * 20;
        active.push(p);
        main_ids.push(p);
    }}

    function step() {{
        if (spawning) {{
            acc += RATE;
            while (acc >= 1 && index < items.length) {{
                acc -= 1;
                spawn(items[index]);
                index++;
            }}
            if (index >= items.length) spawning = false;
        }}

        // Limpa a tela
        ctx.fillStyle = BG;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Atualiza e desenha todas as palavras
        for (let i = active.length - 1; i >= 0; i--) {{
            let p = active[i];
            p.f += 1;
            let u = clamp(p.f / ANIM);
            let e = 1 - Math.pow(1 - u, 3);
            let c = p.color;

            // Coordenadas ajustadas para o centro da tela
            let x = p.x + 400;
            let y = -p.y + 400;

            let hover = (1 - e) * LIFT;
            let px = x + p.dx * (1 - e);
            let py = y - hover;

            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            // Sombra
            ctx.font = "bold " + p.size + "px " + FONT;
            ctx.fillStyle = hx(mix(BGC, dim(c, 0.30), e));
            ctx.fillText(p.text, x + 2, y + 3);

            // Halo
            ctx.font = "bold " + (p.size + 1) + "px " + FONT;
            ctx.fillStyle = hx(mix(BGC, dim(c, 0.20), e * e));
            ctx.fillText(p.text, px, py);

            // Texto Principal
            let flash = 0.75 * Math.sin(Math.PI * clamp((u - 0.55) / 0.45));
            let col = mix(mix(BGC, c, Math.pow(e, 1.5)), FLASH, flash);
            ctx.font = "bold " + p.size + "px " + FONT;
            ctx.fillStyle = hx(col);
            ctx.fillText(p.text, px, py);

            if (u >= 1) {{
                p.done = true;
            }}
        }}

        requestAnimationFrame(step);
    }}

    step();
</script>
</body>
</html>
"""

components.html(html_code, height=820, width=820)