# Genera un video animado (MP4) a partir de config.json y de las tablas de datos/.
# Uso:  python3 herramientas/hacer_video.py [--lento 1.6] [--audio musica.wav] [--salida video.mp4] [--cuadro 12.5]
#   --lento   multiplica la duración de cada hecho (1 = ritmo para redes; 1.6 = pausado)
#   --audio   pista de audio que se añade al final (use sólo música con derechos claros)
#   --cuadro  en vez del video, guarda en PNG el cuadro de ese segundo, para revisar
# Requiere Python 3, Pillow (pip install pillow) y ffmpeg.
# Copyright (c) 2026 Leopoldo López Valencia. Licencia MIT (véase LICENSE).
import argparse, math, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import leer_config, Proyeccion, costas, cargar_datos, ruta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument('--lento', type=float, default=1.0)
ap.add_argument('--audio')
ap.add_argument('--salida', default=ruta('video.mp4'))
ap.add_argument('--cuadro', type=float)
A = ap.parse_args()

cfg = leer_config()
proy = Proyeccion(cfg)
W, H, FPS, SS, K = proy.W, proy.H, 30, 2, A.lento
lugares, conexiones = cargar_datos(cfg, proy)
BY = {l['id']: l for l in lugares}

OCEAN, LAND, COAST, INK, RED, GOLD = (214, 205, 184), (240, 232, 212), (120, 96, 70), (59, 42, 26), (128, 30, 30), (176, 128, 30)
def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
GCOL = {k: hexrgb(v['color']) for k, v in cfg['grupos'].items()}

# ---------- tipografía ----------
CANDIDATAS = {'': ['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', '/Library/Fonts/Georgia.ttf', 'C:/Windows/Fonts/georgia.ttf'],
              'b': ['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', '/Library/Fonts/Georgia Bold.ttf', 'C:/Windows/Fonts/georgiab.ttf'],
              'i': ['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf', '/Library/Fonts/Georgia Italic.ttf', 'C:/Windows/Fonts/georgiai.ttf']}
PROPIAS = {'': cfg.get('fuente_ttf'), 'b': cfg.get('fuente_ttf_negrita'), 'i': cfg.get('fuente_ttf_cursiva')}
_cache = {}
def F(estilo, tam):
    key = (estilo, tam)
    if key not in _cache:
        for p in [PROPIAS[estilo]] + CANDIDATAS[estilo]:
            if p and os.path.exists(p):
                _cache[key] = ImageFont.truetype(p, tam); break
        else:
            _cache[key] = ImageFont.load_default(size=tam)
    return _cache[key]

# ---------- mapa base ----------
def base():
    im = Image.new('RGB', (W * SS, H * SS), OCEAN); d = ImageDraw.Draw(im)
    lo0, la0, lo1, la1 = proy.limites(10)
    for lo in range(int(lo0 // 5 * 5), int(lo1) + 5, 5):
        d.line([tuple(c * SS for c in proy.xy(lo, la)) for la in (la0, la1)], fill=(198, 188, 165), width=2)
    for la in range(int(la0 // 5 * 5), int(la1) + 5, 5):
        d.line([tuple(c * SS for c in proy.xy(lo, la)) for lo in (lo0, lo1)], fill=(198, 188, 165), width=2)
    an = costas(proy)
    for exterior, S in an:
        d.polygon([(x * SS, y * SS) for x, y in S], fill=LAND if exterior else OCEAN)
    for _, S in an:
        pts = [(x * SS, y * SS) for x, y in S]
        d.line(pts + [pts[0]], fill=COAST, width=3, joint='curve')
    im = im.resize((W, H), Image.LANCZOS); d = ImageDraw.Draw(im)
    for r in cfg.get('rotulos_mar', []):
        d.text(proy.xy(r['lon'], r['lat']), r['texto'], font=F('i', 30), fill=(140, 120, 95), anchor='mm')
    v = Image.new('L', (W, H), 90); ImageDraw.Draw(v).rectangle([W * .06, H * .07, W * .94, H * .93], fill=0)
    return Image.composite(Image.new('RGB', (W, H), (150, 125, 95)), im, v.filter(ImageFilter.GaussianBlur(120)))

# ---------- cronología ----------
ev = []   # (anio, orden, tipo, datos)
for l in lugares:
    ev.append((l['anio'], 0, 'aparece', l['id']))
    if l['elev']: ev.append((l['elev'], 1, 'eleva', l['id']))
    for p in l['pos'][1:]: ev.append((p[0], 2, 'traslado', (l['id'], p)))
for c in conexiones: ev.append((c['anio'], 3, 'conexion', c))
ev.sort(key=lambda e: (e[0], e[1]))

T0 = 3.6
SEG, YK = [], []          # segmentos (t, dur, tipo, datos, leyenda); claves del contador (t, año)
t = T0; prev = None
anios = sorted(set(e[0] for e in ev))
for a in anios:
    if prev is not None and a - prev > 15:
        YK.append((t, prev)); t += 0.8 * K
    grupo = [e for e in ev if e[0] == a]
    nuevos = [e[3] for e in grupo if e[2] == 'aparece']
    if nuevos:
        stag = 0.0 if len(nuevos) == 1 else 0.6
        nombres = [BY[i]['nombre'] for i in nuevos]
        ley = BY[nuevos[0]]['leyenda'] if len(nuevos) == 1 else (', '.join(nombres[:-1]) + ' y ' + nombres[-1] if len(nombres) <= 3 else f'{len(nuevos)} lugares nuevos')
        dur = (1.45 + stag * len(nuevos)) * K
        SEG.append((t, dur, 'aparece', [(i, t + j * stag * K) for j, i in enumerate(nuevos)], ley)); YK.append((t, a)); t += dur
    for e in grupo:
        if e[2] == 'eleva':
            l = BY[e[3]]; SEG.append((t, 1.4 * K, 'eleva', l['id'], f"{l['nombre']}: {cfg.get('etiqueta_elevacion', '')}")); YK.append((t, a)); t += 1.4 * K
        elif e[2] == 'traslado':
            lid, p = e[3]; SEG.append((t, 1.8 * K, 'traslado', (lid, p[0]), p[4] or f"{BY[lid]['nombre']} cambia de sede")); YK.append((t, a)); t += 1.8 * K
        elif e[2] == 'conexion':
            c = e[3]; d = (1.0 + 0.25 * len(c['destinos']) + 1.6) * K
            SEG.append((t, d, 'conexion', c, c['nombre'] + ('\n' + c['fechas'] if c['fechas'] else ''))); YK.append((t, a)); t += d
    YK.append((t - 0.01, a)); prev = a
CREDITO = t + 1.5; FIN = CREDITO + 5.0

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u

APARECE = {}; ELEVA = {}; TRAS = []
for s in SEG:
    if s[2] == 'aparece':
        for i, ti in s[3]: APARECE[i] = ti
    elif s[2] == 'eleva': ELEVA[s[3]] = s[0]
    elif s[2] == 'traslado': TRAS.append((s[0], s[3][0], s[3][1]))

def anio_en(tt):
    ks = sorted(YK)
    if tt <= ks[0][0]: return ks[0][1]
    for (t0, y0), (t1, y1) in zip(ks, ks[1:]):
        if tt <= t1: return round(lerp(y0, y1, ease((tt - t0) / (t1 - t0)) if t1 > t0 else 1))
    return ks[-1][1]

def pos(lid, tt):
    l = BY[lid]; x, y, lab = l['pos'][0][1], l['pos'][0][2], l['pos'][0][3]
    for tm, i, an in TRAS:
        if i != lid or tt < tm: continue
        p = next(p for p in l['pos'] if p[0] == an)
        u = ease((tt - tm) / (1.4 * K)); x, y = lerp(x, p[1], u), lerp(y, p[2], u)
        if u > .5: lab = p[3]
    return x, y, lab

BASE = None
def cuadro(tt):
    im = BASE.copy().convert('RGBA')
    ov = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    tx = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(tx)
    # conexiones
    for s in SEG:
        if s[2] != 'conexion' or not (s[0] <= tt < s[0] + s[1] + 0.8): continue
        c = s[3]; a = 1 - ease((tt - (s[0] + s[1] - 0.2)) / 0.8)
        x0, y0, _ = pos(c['centro'], tt)
        r = 17 * SS; od.ellipse([x0 * SS - r, y0 * SS - r, x0 * SS + r, y0 * SS + r], outline=GOLD + (int(230 * a),), width=4 * SS)
        for i, k in enumerate(c['destinos']):
            u = ease((tt - s[0] - 0.25 * K * i) / (0.9 * K))
            if u <= 0: continue
            x1, y1, _ = pos(k, tt)
            od.line([(x0 * SS, y0 * SS), (lerp(x0, x1, u) * SS, lerp(y0, y1, u) * SS)], fill=GOLD + (int(220 * a),), width=5)
    # traslados: estela punteada
    for tm, lid, an in TRAS:
        if not (tm <= tt < tm + 3.2 * K): continue
        g = 1 - ease((tt - (tm + 2.2 * K)) / (1.0 * K))
        xa, ya, _ = pos(lid, tm - 0.001); xb, yb, _ = pos(lid, tt); L = math.hypot(xb - xa, yb - ya)
        n = max(1, int(L / 10))
        for i in range(0, n, 2):
            od.line([(lerp(xa, xb, i / n) * SS, lerp(ya, yb, i / n) * SS), (lerp(xa, xb, (i + 1) / n) * SS, lerp(ya, yb, (i + 1) / n) * SS)], fill=RED + (int(220 * g),), width=3 * SS)
        r = 8 * SS; od.ellipse([xa * SS - r, ya * SS - r, xa * SS + r, ya * SS + r], outline=RED + (int(200 * g),), width=2 * SS)
    # lugares
    for l in lugares:
        ta = APARECE.get(l['id'])
        if ta is None or tt < ta: continue
        x, y, lab = pos(l['id'], tt); u = ease((tt - ta) / 0.4); X, Y = x * SS, y * SS
        pu = (tt - ta) / 1.2
        if pu < 1: r = (8 + 40 * pu) * SS; od.ellipse([X - r, Y - r, X + r, Y + r], outline=GCOL.get(l['grupo'], RED) + (int(200 * (1 - pu)),), width=3 * SS)
        el = ELEVA.get(l['id']); isA = el is not None and tt >= el
        if isA:
            ua = ease((tt - el) / 0.6); r = (13 + (1 - ua) * 20) * SS
            od.ellipse([X - r, Y - r, X + r, Y + r], outline=GOLD + (int(255 * ua),), width=int(3.5 * SS))
        r = 7 * u * SS
        od.ellipse([X - r - 2 * SS, Y - r - 2 * SS, X + r + 2 * SS, Y + r + 2 * SS], fill=(250, 244, 228, int(255 * u)))
        od.ellipse([X - r, Y - r, X + r, Y + r], fill=GCOL.get(l['grupo'], RED) + (int(255 * u),))
        dx, dy, anc = l['off']; aa = int(255 * u)
        d.text((x + dx, y + dy), lab, font=F('b' if isA else '', 22), fill=INK + (aa,), anchor=anc, stroke_width=3, stroke_fill=LAND + (int(aa * .85),))
    im.alpha_composite(ov.resize((W, H), Image.LANCZOS))
    # marca de agua
    ma = cfg.get('marca_agua_en')
    if ma:
        gx, gy = proy.xy(ma['lon'], ma['lat']); a = int(170 * ease((tt - T0 + .6) / .6) * (1 - ease((tt - CREDITO) / .5)))
        for i, ln in enumerate([f"© {cfg['anio_copyright']} {cfg['autor']}", cfg.get('institucion', ''), cfg.get('licencia_contenido', '')]):
            if ln and a > 1: d.text((gx, gy + 40 + i * 28), ln, font=F('i', 22), fill=INK + (a,), anchor='mm')
    # año y leyenda
    if tt >= T0 - .6:
        a = int(255 * ease((tt - T0 + .6) / .6))
        d.text((W - 80, 70), str(anio_en(tt)), font=F('b', 120), fill=(90, 62, 38, a), anchor='rt')
        for s in SEG:
            fin = s[0] + max(s[1], 1.2)
            if not (s[0] <= tt < fin): continue
            g = ease((tt - s[0]) / .35) * (1 - ease((tt - (fin - .25)) / .25)); A2 = int(255 * g)
            l1, _, l2 = s[4].partition('\n'); col = GOLD if s[2] in ('conexion', 'eleva') else RED
            f1, f2 = F('', 32), F('i', 25); w = max(d.textlength(l1, font=f1), d.textlength(l2, font=f2) if l2 else 0) + 56
            x1, y0 = W - 74, 205; x0 = x1 - w; bh = 70 + (36 if l2 else 0)
            d.rectangle([x0, y0, x1, y0 + bh], fill=(246, 240, 224, int(225 * g)), outline=col + (A2,), width=2)
            d.rectangle([x0, y0, x0 + 8, y0 + bh], fill=col + (A2,))
            d.text((x0 + 30, y0 + 35), l1, font=f1, fill=INK + (A2,), anchor='lm')
            if l2: d.text((x0 + 30, y0 + 71), l2, font=f2, fill=(95, 70, 45, A2), anchor='lm')
    # leyenda de colores
    lx, ly = 70, H - 70
    for k, gcfg in list(cfg['grupos'].items())[::-1]:
        d.ellipse([lx - 7, ly - 7, lx + 7, ly + 7], fill=GCOL[k] + (220,)); d.text((lx + 18, ly), gcfg['etiqueta'], font=F('', 22), fill=INK + (220,), anchor='lm'); ly -= 34
    # título y créditos
    if tt < T0 + .4:
        a = 1 - ease((tt - (T0 - .9)) / 1.1)
        im.alpha_composite(Image.new('RGBA', (W, H), (240, 232, 212, int(200 * a))))
        d.text((W / 2, H / 2 - 30), cfg['titulo'], font=F('b', 64), fill=INK + (int(255 * a),), anchor='mm')
        if cfg.get('subtitulo'): d.text((W / 2, H / 2 + 45), cfg['subtitulo'], font=F('i', 32), fill=(110, 80, 50, int(255 * a)), anchor='mm')
    im.alpha_composite(tx)
    if tt >= CREDITO:
        g = ease((tt - CREDITO) / .9)
        im.alpha_composite(Image.new('RGBA', (W, H), (240, 232, 212, int(245 * g))))
        c = ImageDraw.Draw(im); A2 = int(255 * ease((tt - CREDITO - .4) / .8))
        for yy, txt, est, tam in [(H / 2 - 120, cfg['autor'], 'b', 60), (H / 2 - 50, cfg.get('institucion', ''), 'i', 38),
                                  (H / 2 + 40, 'Fuentes: ' + cfg.get('fuentes', ''), '', 24), (H / 2 + 90, 'Licencia ' + cfg.get('licencia_contenido', ''), '', 24),
                                  (H - 60, 'Hecho con la plantilla de mapas históricos de Leopoldo López Valencia', 'i', 20)]:
            if txt: c.text((W / 2, yy), txt, font=F(est, tam), fill=INK + (A2,), anchor='mm')
    fade = min(ease(tt / .8), 1 - ease((tt - (FIN - 1)) / 1))
    if fade < 1: im = Image.blend(Image.new('RGBA', (W, H), (20, 14, 8, 255)), im, fade)
    return im.convert('RGB')

BASE = base()
if A.cuadro is not None:
    out = ruta(f'cuadro_{A.cuadro:06.1f}.png'); cuadro(A.cuadro).save(out); print(out); sys.exit()
tmp = A.salida + '.tmp.mp4'
p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
n = int(FIN * FPS)
for i in range(n):
    p.stdin.write(cuadro(i / FPS).tobytes())
    if i % (FPS * 10) == 0: print(f'{i / FPS:5.0f} s de {FIN:.0f} s', flush=True)
p.stdin.close()
if p.wait() != 0: sys.exit('ffmpeg falló')
if A.audio:
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-i', A.audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', A.salida], check=True)
    os.remove(tmp)
else:
    os.replace(tmp, A.salida)
print('Listo:', A.salida, f'({FIN:.0f} s)')
