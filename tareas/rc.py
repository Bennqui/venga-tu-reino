"""Regnum Christi (con su permiso): baja del sitio oficial el logotipo, el escudo y las fotos de las últimas noticias.

- assets/rc/logo.png      logotipo para el pie de Encuentro y Apostolado
- assets/rc/escudo.png    escudo (ícono del sitio) para el ícono de la app
- assets/rc/n1..n6.webp   fotos de las noticias, en versión para teléfono
- assets/rc/rc.json       títulos, fechas y enlaces de las noticias

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

# 1 y 2) Escudo y logotipo: se buscan todas las versiones del sitio y se elige la mejor
def originales(u):
    """La imagen tal como se subió, sin el recorte de tamaño que agrega WordPress (-300x65, cropped-)."""
    out = []
    sin = re.sub(r'-\d+x\d+(?=\.\w+$)', '', u)
    out.append(sin)
    if '/cropped-' in sin:
        out.append(sin.replace('/cropped-', '/'))
    out.append(u)
    return list(dict.fromkeys(out))

cands = []
for rel, href in re.findall(r'<link[^>]+rel="([^"]*icon[^"]*)"[^>]+href="([^"]+)"', inicio):
    cands.append(abs_url(href))
for href in re.findall(r'<link[^>]+href="([^"]+)"[^>]+rel="[^"]*icon[^"]*"', inicio):
    cands.append(abs_url(href))
for u in re.findall(r'(?:src|data-src|href|content)="([^"]+\.(?:png|jpe?g|webp))"', inicio, re.I):
    if re.search(r'logo|escudo|shield|favi|RC_|regnum', u, re.I):
        cands.append(abs_url(u))
for srcset in re.findall(r'srcset="([^"]+)"', inicio):
    for parte in srcset.split(','):
        u = parte.strip().split(' ')[0]
        if re.search(r'logo|escudo|shield|RC_', u, re.I):
            cands.append(abs_url(u))
todas = []
for c in dict.fromkeys(cands):
    for u in originales(c):
        if any(u == t[0] for t in todas):
            continue
        try:
            im = imagen(u)
            todas.append((u, im))
            print('  imagen:', u, im.size, im.mode)
        except Exception as e:
            pass

def es_blanca(im):
    """True si lo visible de la imagen es casi todo blanco (versión para fondos oscuros)."""
    rgba = im.convert('RGBA').resize((min(200, im.size[0]), max(1, round(im.size[1] * min(200, im.size[0]) / im.size[0]))))
    px = [p for p in rgba.getdata() if p[3] > 128]
    if not px:
        return True
    return sum((r + g + b) / 3 for r, g, b, a in px) / len(px) > 225

def color(im):
    rgb = im.convert('RGB').resize((60, 60))
    return sum(1 for r, g, b in rgb.getdata() if r > 120 and g < 90 and b < 90)

cuadradas = [t for t in todas if 0.75 < t[1].size[0] / t[1].size[1] < 1.33 and not es_blanca(t[1])]
if cuadradas:
    u, im = max(cuadradas, key=lambda t: (min(t[1].size) >= 400, color(t[1]) > 20, t[1].size[0]))
    escudo = sobre_blanco(im)
    escudo.save(DIR + '/escudo.png')
    resumen['escudo'] = DIR + '/escudo.png'
    print('Escudo elegido:', u, im.size)
else:
    escudo = None
horizontales = [t for t in todas if t[1].size[0] / t[1].size[1] > 2.2]
oscuras = [t for t in horizontales if not es_blanca(t[1])]
blancas = [t for t in horizontales if es_blanca(t[1])]
if oscuras:
    u, im = max(oscuras, key=lambda t: t[1].size[0])
    lg = recortar_blanco(sobre_blanco(im))
    if lg.size[1] > 300:
        lg = lg.resize((round(lg.size[0] * 300 / lg.size[1]), 300), Image.LANCZOS)
    lg.save(DIR + '/logo.png', optimize=True)
    resumen['logo'] = DIR + '/logo.png'
    print('Logotipo a color:', u, im.size)
if blancas:
    u, im = max(blancas, key=lambda t: t[1].size[0])
    lg = im.convert('RGBA')
    caja = lg.getchannel('A').getbbox()
    if caja:
        lg = lg.crop(caja)
    if lg.size[1] > 300:
        lg = lg.resize((round(lg.size[0] * 300 / lg.size[1]), 300), Image.LANCZOS)
    lg.save(DIR + '/logo-blanco.png', optimize=True)
    resumen['logo_blanco'] = DIR + '/logo-blanco.png'
    print('Logotipo blanco:', u, im.size)

# 3) El ícono de la app usa el escudo a color (assets/rc/escudo-color.png), que no se toca aquí.

# 4) Últimas noticias con foto: el canal RSS del sitio y la foto principal (og:image) de cada noticia
noticias = []
items = []
for feed in (SITIO + '/es/feed/', SITIO + '/feed/'):
    try:
        xml = get(feed).decode('utf-8', 'ignore')
        items = re.findall(r'<item>(.*?)</item>', xml, re.S)
        if items:
            print('Canal:', feed, len(items))
            break
    except Exception as e:
        print('Sin canal en', feed, e)
if not items and inicio:  # respaldo: enlaces de artículos de la portada
    for href in dict.fromkeys(re.findall(r'href="(https://regnumchristi\.org/es/[a-z0-9-]{20,}/)"', inicio)):
        items.append('<link>%s</link>' % href)
def campo(it, tag):
    m = re.search(r'<%s>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>' % (tag, tag), it, re.S)
    return html.unescape(m.group(1).strip()) if m else ''
for it in items:
    if len(noticias) >= 6:
        break
    link = campo(it, 'link')
    if not link.startswith('https://'):
        continue
    try:
        pag = get(link).decode('utf-8', 'ignore')
        m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', pag) or re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', pag)
        if not m:
            continue
        titulo = campo(it, 'title') or html.unescape((re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', pag) or [None, ''])[1]).replace(' - Regnum Christi', '')
        im = imagen(abs_url(m.group(1))).convert('RGB')
        if im.size[0] > 1000:
            im = im.resize((1000, round(im.size[1] * 1000 / im.size[0])), Image.LANCZOS)
        n = len(noticias) + 1
        im.save('%s/n%d.webp' % (DIR, n), 'WEBP', quality=78, method=6)
        fecha = ''
        pd = campo(it, 'pubDate')
        mm = re.search(r'(\d{1,2}) (\w{3}) (\d{4})', pd)
        if mm:
            mes = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(mm.group(2))
            fecha = '%d de %s de %s' % (int(mm.group(1)), MESES[mes], mm.group(3))
        noticias.append({'titulo': re.sub(r'\s+', ' ', titulo).strip(), 'link': link, 'fecha': fecha, 'img': '%s/n%d.webp' % (DIR, n)})
        print('Noticia:', titulo[:80])
        time.sleep(1)
    except Exception as e:
        print('  noticia omitida:', link[:90], e)

viejo = {}
if os.path.exists(DIR + '/rc.json'):
    viejo = json.load(open(DIR + '/rc.json', encoding='utf-8'))
salida = {
    'logo': resumen.get('logo') or viejo.get('logo'),
    'logo_blanco': resumen.get('logo_blanco') or viejo.get('logo_blanco'),
    'escudo': resumen.get('escudo') or viejo.get('escudo'),
    'noticias': noticias or viejo.get('noticias') or [],
    'fuente': 'regnumchristi.org (con permiso del Regnum Christi)',
}
json.dump(salida, open(DIR + '/rc.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('Listo:', {k: (len(v) if isinstance(v, list) else v) for k, v in salida.items()})
