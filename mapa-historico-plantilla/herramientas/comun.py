# Mapa histórico animado e interactivo. Funciones comunes al mapa y al video.
# Copyright (c) 2026 Leopoldo López Valencia. Licencia MIT (véase LICENSE).
import csv, json, math, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ruta(*p):
    return os.path.join(RAIZ, *p)


def leer_config():
    with open(ruta('config.json'), encoding='utf-8') as f:
        return json.load(f)


def leer_csv(nombre):
    p = ruta('datos', nombre)
    if not os.path.exists(p):
        return []
    with open(p, encoding='utf-8-sig', newline='') as f:
        return [{k.strip(): (v or '').strip() for k, v in r.items()} for r in csv.DictReader(f)]


class Proyeccion:
    """Equirrectangular con corrección de latitud: sencilla y fiel a escala regional."""

    def __init__(self, cfg):
        p = cfg['proyeccion']
        self.lat0, self.lon0 = p['lat_centro'], p['lon_centro']
        self.S, self.W, self.H = p['escala'], p['ancho'], p['alto']
        self.C = math.cos(math.radians(self.lat0))

    def xy(self, lon, lat):
        return (self.W / 2 + (lon - self.lon0) * self.S * self.C,
                self.H / 2 - (lat - self.lat0) * self.S)

    def limites(self, margen=4):
        dlon = self.W / 2 / (self.S * self.C) + margen
        dlat = self.H / 2 / self.S + margen
        return self.lon0 - dlon, self.lat0 - dlat, self.lon0 + dlon, self.lat0 + dlat


def recortar(pts, x0, y0, x1, y1):
    """Recorte de Sutherland-Hodgman de un anillo contra un rectángulo (en grados)."""
    def corta(poly, dentro, cruce):
        out = []
        for i in range(len(poly)):
            a, b = poly[i - 1], poly[i]
            if dentro(b):
                if not dentro(a):
                    out.append(cruce(a, b))
                out.append(b)
            elif dentro(a):
                out.append(cruce(a, b))
        return out
    def cx(a, b, x):
        return (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    def cy(a, b, y):
        return (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    poly = list(pts)
    for dentro, cruce in ((lambda p: p[0] >= x0, lambda a, b: cx(a, b, x0)),
                          (lambda p: p[0] <= x1, lambda a, b: cx(a, b, x1)),
                          (lambda p: p[1] >= y0, lambda a, b: cy(a, b, y0)),
                          (lambda p: p[1] <= y1, lambda a, b: cy(a, b, y1))):
        if not poly:
            break
        poly = corta(poly, dentro, cruce)
    return poly


def costas(proy, archivo='land-50m.json', paso=1.6):
    """Devuelve la tierra firme como lista de anillos en píxeles (Natural Earth vía world-atlas)."""
    with open(ruta('geodatos', archivo), encoding='utf-8') as f:
        tj = json.load(f)
    sc, tr = tj['transform']['scale'], tj['transform']['translate']
    arcos = []
    for a in tj['arcs']:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx
            y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcos.append(pts)

    def anillo(r):
        out = []
        for i in r:
            p = arcos[i] if i >= 0 else arcos[~i][::-1]
            out += p if not out else p[1:]
        return out

    lo0, la0, lo1, la1 = proy.limites(6)
    anillos = []
    for g in tj['objects']['land']['geometries']:
        polis = g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']]
        for poli in polis:
            for k, r in enumerate(poli):
                pts = anillo(r)
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                if max(xs) < lo0 or min(xs) > lo1 or max(ys) < la0 or min(ys) > la1:
                    continue
                P = [proy.xy(lo, la) for lo, la in recortar(pts, lo0, la0, lo1, la1)]
                if len(P) < 3:
                    continue
                S = [P[0]]
                for q in P[1:]:
                    if abs(q[0] - S[-1][0]) + abs(q[1] - S[-1][1]) > paso:
                        S.append(q)
                if len(S) >= 4:
                    anillos.append((k == 0, S))
    return anillos


def num(v, defecto=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return defecto


def cargar_datos(cfg, proy):
    """Lee las tres tablas y devuelve lugares (con traslados) y conexiones, ya proyectados."""
    lugares = []
    for r in leer_csv('lugares.csv'):
        x, y = proy.xy(float(r['lon']), float(r['lat']))
        ficha = [(k[6:].replace('_', ' ').capitalize(), v) for k, v in r.items()
                 if k.startswith('ficha_') and v]
        lugares.append(dict(
            id=r['id'], nombre=r.get('nombre') or r['id'], anio=int(float(r['anio'])),
            grupo=r.get('grupo', ''), elev=int(num(r.get('anio_elevacion'), 0)) or None,
            leyenda=r.get('leyenda') or r.get('nombre') or r['id'],
            off=[num(r.get('etiqueta_dx'), 12), num(r.get('etiqueta_dy'), 0), r.get('etiqueta_ancla') or 'lm'],
            pos=[[int(float(r['anio'])), x, y, r.get('nombre') or r['id'], '']],
            ficha=ficha, fuente=r.get('fuente', '')))
    por_id = {l['id']: l for l in lugares}
    for t in sorted(leer_csv('traslados.csv'), key=lambda t: float(t['anio'])):
        l = por_id.get(t['id'])
        if not l:
            raise SystemExit(f"traslados.csv: no existe el lugar '{t['id']}' en lugares.csv")
        x, y = proy.xy(float(t['lon']), float(t['lat']))
        l['pos'].append([int(float(t['anio'])), x, y, t.get('etiqueta') or l['nombre'], t.get('leyenda', '')])
    conexiones = []
    for c in leer_csv('conexiones.csv'):
        dest = [d.strip() for d in c.get('destinos', '').split(';') if d.strip()]
        for k in [c['centro']] + dest:
            if k not in por_id:
                raise SystemExit(f"conexiones.csv: no existe el lugar '{k}' en lugares.csv")
        conexiones.append(dict(id=c['id'], nombre=c['nombre'], anio=int(float(c['anio'])),
                               fechas=c.get('fechas', ''), centro=c['centro'], destinos=dest,
                               nota=c.get('nota', '')))
    conexiones.sort(key=lambda c: c['anio'])
    return lugares, conexiones
