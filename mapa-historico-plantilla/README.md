# Plantilla de mapas históricos animados e interactivos

Esta plantilla genera, a partir de unas tablas sencillas, dos productos:

1. **Un mapa interactivo** (una página web de un solo archivo) con línea del tiempo, botón de reproducción, fichas con fuente para cada lugar, traslados animados y conexiones entre lugares (por ejemplo, una metrópoli y sus sufragáneas, una audiencia y sus gobernaciones, una casa matriz y sus fundaciones).
2. **Un video animado** (MP4) con la misma cronología, para presentaciones o redes.

Es la herramienta con que se hizo el mapa [Sedes episcopales de México, 1519-1899](https://historiajuridica.github.io/sedes-episcopales/), de Leopoldo López Valencia (El Colegio de Michoacán). Puede ver la plantilla funcionando con datos de ejemplo en [historiajuridica.github.io/mapa-historico-plantilla](https://historiajuridica.github.io/mapa-historico-plantilla/).

## Licencias

- **El código** (carpeta `herramientas/`) está bajo licencia **MIT**: puede usarlo, adaptarlo y redistribuirlo libremente, con la sola condición de conservar el aviso de autoría ("Copyright (c) 2026 Leopoldo López Valencia") en las copias del código.
- **Los datos de ejemplo** de la carpeta `datos/` son ficticios.
- **El contenido de su propio mapa** es suyo: elija la licencia que prefiera y anótela en `config.json`.
- **El mapa de las sedes episcopales** de México (datos, cronología y fichas) no forma parte de esta plantilla y sigue bajo licencia CC BY-NC-ND 4.0.
- Las costas proceden de Natural Earth (dominio público), en la versión de world-atlas (licencia ISC).

Si publica un mapa hecho con esta plantilla, se agradece la mención: "Hecho con la plantilla de mapas históricos de Leopoldo López Valencia".

## Qué necesita

- **Python 3** (para preparar el mapa y el video).
- Para el video, además: **Pillow** (`pip install pillow`) y **ffmpeg** (instalable desde ffmpeg.org, o con `brew install ffmpeg` en Mac).

## Cómo usarla, paso a paso

### 1. Descargue la carpeta

Descargue la carpeta `mapa-historico-plantilla` de este repositorio (en GitHub: botón "Code" → "Download ZIP") y descomprímala.

### 2. Ajuste `config.json`

Abra `config.json` con cualquier editor de texto y cambie:

| campo | qué es |
|---|---|
| `titulo`, `subtitulo` | Encabezado del mapa y del video. |
| `autor`, `institucion`, `anio_copyright` | Crédito, marca de agua y referencia para citar. |
| `licencia_contenido`, `licencia_url` | Licencia de **sus** datos (por ejemplo CC BY 4.0). |
| `url_publica` | Dirección donde publicará el mapa; se usa en "Cómo citar este mapa". |
| `fuentes` | Texto de fuentes que aparece al pie y en los créditos del video. |
| `anio_inicio`, `anio_fin` | Extremos de la línea del tiempo. |
| `proyeccion` | Centro del mapa (`lat_centro`, `lon_centro`), `escala` (píxeles por grado de latitud; más alto = más cerca) y tamaño del lienzo (`ancho`, `alto`). Para todo México basta el valor de ejemplo; para una región menor, suba la escala. |
| `grupos` | Categorías con su etiqueta y color (por ejemplo, siglos u órdenes religiosas). |
| `etiqueta_elevacion` | Qué significa el anillo dorado (arzobispado, capital, cabecera…). |
| `etiqueta_conexiones` | Título de la lista de conexiones (concilios, visitas, rutas…). |
| `rotulos_mar` | Nombres de mares u otros rótulos fijos, con su latitud y longitud. |
| `marca_agua_en` | Dónde va la marca de agua (conviene un lugar vacío, en el mar). |
| `fuente_ttf…` | Opcional: rutas a tipografías para el video. Si se dejan vacías se usa una tipografía con serifas del sistema. |

### 3. Llene las tablas de `datos/`

Las tres tablas son archivos CSV (se editan en Excel, LibreOffice o Google Sheets y se guardan como "CSV UTF-8").

**`lugares.csv`**: una fila por lugar.

| columna | obligatoria | qué es |
|---|---|---|
| `id` | sí | Clave breve y única (sin espacios conviene). |
| `nombre` | sí | Nombre que se ve en el mapa. |
| `anio` | sí | Año en que aparece. |
| `lat`, `lon` | sí | Coordenadas en grados decimales (lat positiva al norte; lon negativa al oeste). |
| `grupo` | sí | Una de las claves de `grupos` en `config.json`. |
| `anio_elevacion` | no | Año en que recibe el anillo dorado. |
| `leyenda` | no | Texto del letrero del video cuando aparece. |
| `etiqueta_dx`, `etiqueta_dy` | no | Desplazamiento del nombre en píxeles respecto del punto (por omisión 12 y 0). |
| `etiqueta_ancla` | no | Cómo se alinea el nombre: `lm` a la derecha del punto, `rm` a la izquierda, `lb` arriba a la derecha, `rb` arriba a la izquierda, `rt` abajo a la izquierda. |
| `ficha_…` | no | Todas las columnas que empiecen por `ficha_` aparecen en la ficha del lugar; el resto del nombre es el rótulo (`ficha_acto_de_fundacion` se lee "Acto de fundacion"). |
| `fuente` | no | Fuente que se muestra al pie de la ficha. |

**`traslados.csv`** (opcional): una fila por cada cambio de residencia de un lugar: `id` (el del lugar), `anio`, `lat`, `lon`, `etiqueta` (nombre que tendrá después) y `leyenda` (letrero del traslado).

**`conexiones.csv`** (opcional): `id`, `nombre`, `anio`, `fechas`, `centro` (id del lugar central), `destinos` (ids separados por punto y coma, por ejemplo `B;C;F`) y `nota`.

### 4. Genere el mapa interactivo

Desde la carpeta de la plantilla:

```
python3 herramientas/construir_mapa.py
```

Se crea o actualiza `index.html`. Ábralo con doble clic para revisarlo en su navegador.

### 5. Genere el video (opcional)

```
python3 herramientas/hacer_video.py
```

Opciones útiles:

- `--lento 1.6` alarga cada hecho (1 es el ritmo para redes sociales; 1.6, uno pausado).
- `--cuadro 20` guarda sólo el cuadro del segundo 20 como imagen, para revisar sin esperar el video entero.
- `--audio musica.wav` añade una pista de audio. **Use sólo música de dominio público en grabación propia o con licencia libre (CC0 o CC BY)**: las grabaciones comerciales, aunque la obra sea antigua, suelen provocar reclamaciones de derechos en las redes.
- `--salida mi_video.mp4` elige el nombre del archivo.

### 6. Publique el mapa

El mapa es un solo archivo, `index.html`, y funciona en cualquier sitio web. La forma gratuita más sencilla es GitHub Pages: cree un repositorio, suba `index.html` y active Pages en "Settings → Pages". También puede alojarlo en el sitio de su institución.

## Consejos

- Revise primero con pocos lugares y añada los demás después.
- Si dos nombres se enciman, cambie `etiqueta_dx`, `etiqueta_dy` o `etiqueta_ancla` del lugar.
- Las coordenadas de un lugar histórico son las de su residencia; si se mudó, use `traslados.csv` en vez de cambiar la fila original.
- Cada dato de la ficha debe llevar su fuente: el mapa es tan confiable como su tabla.

---

Copyright (c) 2026 Leopoldo López Valencia. Código bajo licencia MIT.
