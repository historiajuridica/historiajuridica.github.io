# Genera index.html (mapa interactivo) a partir de config.json y de las tablas de datos/.
# Uso:  python3 herramientas/construir_mapa.py
# Copyright (c) 2026 Leopoldo López Valencia. Licencia MIT (véase LICENSE).
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import leer_config, Proyeccion, costas, cargar_datos, ruta

cfg = leer_config()
proy = Proyeccion(cfg)
lugares, conexiones = cargar_datos(cfg, proy)

tierra = ''.join(('M' + 'L'.join(f'{x:.0f} {y:.0f}' for x, y in S) + 'Z') for _, S in costas(proy))
rotulos = [dict(t=r['texto'], x=proy.xy(r['lon'], r['lat'])[0], y=proy.xy(r['lon'], r['lat'])[1])
           for r in cfg.get('rotulos_mar', [])]
ma = cfg.get('marca_agua_en')
marca = proy.xy(ma['lon'], ma['lat']) if ma else None
grat = []
lo0, la0, lo1, la1 = proy.limites(10)
for lo in range(int(lo0 // 5 * 5), int(lo1) + 5, 5):
    grat.append([*proy.xy(lo, la0), *proy.xy(lo, la1)])
for la in range(int(la0 // 5 * 5), int(la1) + 5, 5):
    grat.append([*proy.xy(lo0, la), *proy.xy(lo1, la)])

D = dict(cfg=cfg, lugares=lugares, conexiones=conexiones, rotulos=rotulos, marca=marca, grat=grat,
         W=proy.W, H=proy.H)
with open(ruta('herramientas', 'plantilla_mapa.html'), encoding='utf-8') as f:
    html = f.read()
html = (html.replace('__TIERRA__', tierra)
            .replace('__DATOS__', json.dumps(D, ensure_ascii=False))
            .replace('__TITULO__', cfg['titulo'])
            .replace('__W__', str(proy.W)).replace('__H__', str(proy.H)))
with open(ruta('index.html'), 'w', encoding='utf-8') as f:
    f.write(html)
print(f"index.html: {len(lugares)} lugares, {len(conexiones)} conexiones, {len(html)//1024} KB")
