"""Regnum Christi (con su permiso): baja del sitio oficial el logotipo, el escudo y las fotos de las últimas noticias.

- assets/rc/logo.png      logotipo para el pie de Encuentro y Apostolado
- assets/rc/escudo.png    escudo (ícono del sitio) para el ícono de la app
- assets/rc/n1..n6.webp   fotos de las noticias, en versión para teléfono
- assets/rc/rc.json       títulos, fechas y enlaces de las noticias
- icon-180/192/512.png    ícono de la app hecho con el escudo, sobre blanco

Lo ejecuta el workflow «Regnum Christi» (cada semana y cuando cambia este archivo).
Si algo no se encuentra, deja lo que había y lo dice en el registro.
"""
import html, io, json, os, re, time, urllib.parse, urllib.request
from PIL import Image

SITIO = 'https://regnumchristi.org'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
DIR = 'assets/rc'
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
os.makedirs(DIR, exist_ok=True)


def get(url, tries=3):
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'es'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            err = e
            time.sleep(2 + 3 * i)
    raise err


def jget(url):
    return json.loads(get(url).decode('utf-8'))


def abs_url(u):
    return urllib.parse.urljoin(SITIO + '/', html.unescape(u))


def imagen(url):
    data = get(url)
    if url.lower().endswith('.svg') or data[:200].lstrip().startswith(b'<'):
        raise ValueError('svg')  # Pillow no lee SVG
    return Image.open(io.BytesIO(data))


def sobre_blanco(im):
    im = im.convert('RGBA')
    fondo = Image.new('RGBA', im.size, (255, 255, 255, 255))
    fondo.alpha_composite(im)
    return fondo.convert('RGB')


def recortar_blanco(im, margen=0.02):
    gris = im.convert('L').point(lambda v: 255 if v < 245 else 0)
    caja = gris.getbbox()
    if not caja:
        return im
    w, h = im.size
    m = int(max(w, h) * margen)
    return im.crop((max(0, caja[0] - m), max(0, caja[1] - m), min(w, caja[2] + m), min(h, caja[3] + m)))


resumen = {}
inicio = ''
try:
    inicio = get(SITIO + '/es/').decode('utf-8', 'ignore')
except Exception as e:
    print('No se pudo abrir la portada:', e)

# 1) Escudo: el ícono oficial del sitio (el más grande que haya)
escudo = None
cands = []
try:
    idx = jget(SITIO + '/wp-json/')
    if idx.get('site_icon_url'):
        cands.append(idx['site_icon_url'])
except Exception as e:
    print('Sin índice REST:', e)
for rel, href in re.findall(r'<link[^>]+rel="([^"]*icon[^"]*)"[^>]+href="([^"]+)"', inicio):
    cands.append(abs_url(href))
for href in re.findall(r'<link[^>]+href="([^"]+)"[^>]+rel="[^"]*icon[^"]*"', inicio):
    cands.append(abs_url(href))
mejor = None
for u in dict.fromkeys(cands):
    try:
        im = imagen(u)
        if not mejor or im.size[0] > mejor[1].size[0]:
            mejor = (u, im)
    except Exception as e:
        print('  ícono no usable:', u[:120], e)
if mejor:
    escudo = sobre_blanco(mejor[1])
    escudo.save(DIR + '/escudo.png')
    resumen['escudo'] = DIR + '/escudo.png'
    print('Escudo:', mejor[0], mejor[1].size)

# 2) Logotipo completo (escudo + letras), del encabezado del sitio
logo = None
imgs = re.findall(r'<img[^>]+>', inicio)
for tag in imgs:
    if not re.search(r'logo', tag, re.I):
        continue
    srcs = re.findall(r'(?:src|data-src)="([^"]+)"', tag)
    srcset = re.findall(r'srcset="([^"]+)"', tag)
    if srcset:
        srcs = [p.strip().split(' ')[0] for p in srcset[0].split(',')][::-1] + srcs
    for u in srcs:
        try:
            im = imagen(abs_url(u))
            if im.size[0] < 120:
                continue
            logo = recortar_blanco(sobre_blanco(im))
            print('Logotipo:', u, im.size)
            break
        except Exception as e:
            print('  logotipo no usable:', u[:120], e)
    if logo:
        break
if logo:
    if logo.size[1] > 300:
        logo = logo.resize((round(logo.size[0] * 300 / logo.size[1]), 300), Image.LANCZOS)
    logo.save(DIR + '/logo.png', optimize=True)
    resumen['logo'] = DIR + '/logo.png'

# 3) Ícono de la app: el escudo centrado sobre blanco (el manual pide fondo blanco y no deformarlo)
if escudo:
    base = recortar_blanco(escudo, 0)
    for n in (180, 192, 512):
        lienzo = Image.new('RGB', (n, n), (255, 255, 255))
        lado = round(n * 0.78)
        k = lado / max(base.size)
        e = base.resize((max(1, round(base.size[0] * k)), max(1, round(base.size[1] * k))), Image.LANCZOS)
        lienzo.paste(e, ((n - e.size[0]) // 2, (n - e.size[1]) // 2))
        lienzo.save('icon-%d.png' % n, optimize=True)
    print('Íconos de la app hechos con el escudo')

# 4) Últimas noticias con foto
noticias = []
for base in (SITIO + '/es', SITIO):
    try:
        posts = jget(base + '/wp-json/wp/v2/posts?per_page=12&_embed=1')
        if posts:
            break
    except Exception as e:
        print('Sin noticias en', base, e)
        posts = []
for p in posts:
    if len(noticias) >= 6:
        break
    try:
        media = (p.get('_embedded') or {}).get('wp:featuredmedia') or []
        if not media:
            continue
        m = media[0]
        sizes = (m.get('media_details') or {}).get('sizes') or {}
        url = (sizes.get('large') or sizes.get('medium_large') or sizes.get('full') or {}).get('source_url') or m.get('source_url')
        if not url:
            continue
        im = imagen(url).convert('RGB')
        if im.size[0] > 1000:
            im = im.resize((1000, round(im.size[1] * 1000 / im.size[0])), Image.LANCZOS)
        n = len(noticias) + 1
        im.save('%s/n%d.webp' % (DIR, n), 'WEBP', quality=78, method=6)
        titulo = html.unescape(re.sub(r'<[^>]+>', '', p['title']['rendered'])).strip()
        y, mo, d = p['date'][:10].split('-')
        noticias.append({'titulo': titulo, 'link': p['link'], 'fecha': '%d de %s de %s' % (int(d), MESES[int(mo) - 1], y), 'img': '%s/n%d.webp' % (DIR, n)})
        print('Noticia:', titulo[:80])
    except Exception as e:
        print('  noticia omitida:', e)

viejo = {}
if os.path.exists(DIR + '/rc.json'):
    viejo = json.load(open(DIR + '/rc.json', encoding='utf-8'))
salida = {
    'logo': resumen.get('logo') or viejo.get('logo'),
    'escudo': resumen.get('escudo') or viejo.get('escudo'),
    'noticias': noticias or viejo.get('noticias') or [],
    'fuente': 'regnumchristi.org (con permiso del Regnum Christi)',
}
json.dump(salida, open(DIR + '/rc.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('Listo:', {k: (len(v) if isinstance(v, list) else v) for k, v in salida.items()})
