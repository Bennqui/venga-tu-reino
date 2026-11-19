"""Descarga a la carpeta assets/ los recursos que la app usaba desde otros servidores, para que cargue rápido y sin internet:
fuentes (Google Fonts), librerías, iconos (Lucide, licencia ISC) e imágenes de alta resolución (Wikimedia Commons).
Lo ejecuta el workflow «Recursos de la app» de GitHub (allí sí hay internet). Configuración: tareas/recursos.json."""
import json, os, re, sys, io, base64, urllib.request, urllib.parse, time
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
BOT = 'AppRecursos/1.0 (https://github.com/Bennqui; app personal sin fines de lucro)'
cfg = json.load(open('tareas/recursos.json', encoding='utf-8'))
os.makedirs('assets', exist_ok=True)
def get(url, ua=UA, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': ua})
            with urllib.request.urlopen(req, timeout=90) as r: return r.read()
        except Exception as e:
            err = e; time.sleep(3 + 4 * i)
    raise err
# 1) Fuentes: solo los rangos latinos (español, portugués, italiano, francés, alemán)
if cfg.get('fuentes'):
    os.makedirs('assets/fonts', exist_ok=True); out = []
    for css_url in cfg['fuentes']:
        css = get(css_url).decode('utf-8')
        for block in re.findall(r'/\* ([a-z-]+) \*/\s*(@font-face\s*{[^}]+})', css):
            sub, face = block
            if sub not in ('latin', 'latin-ext'): continue
            url = re.search(r'url\((https://[^)]+\.woff2)\)', face).group(1)
            fam = re.search(r"font-family:\s*'([^']+)'", face).group(1).replace(' ', '')
            wt = re.search(r'font-weight:\s*([0-9 ]+);', face).group(1).replace(' ', '-')
            st = re.search(r'font-style:\s*(\w+);', face).group(1)
            name = f'{fam}-{wt}-{st}-{sub}.woff2'
            if not os.path.exists('assets/fonts/' + name): open('assets/fonts/' + name, 'wb').write(get(url))
            out.append(face.replace(url, 'fonts/' + name).replace('font-display: swap', 'font-display: swap'))
    open('assets/fuentes.css', 'w').write('\n'.join(out) + '\n'); print('fuentes:', len(out))
# 2) Archivos sueltos (librerías)
for url, path in cfg.get('archivos', {}).items():
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, 'wb').write(get(url)); print('archivo:', path)
# 3) Iconos Lucide en un solo sprite SVG
if cfg.get('iconos'):
    ver = cfg.get('lucide', '0.468.0'); syms = []
    for n in sorted(set(cfg['iconos'])):
        try: svg = get(f'https://unpkg.com/lucide-static@{ver}/icons/{n}.svg', tries=2).decode('utf-8')
        except Exception as e: print('  icono no encontrado:', n); continue
        inner = re.sub(r'^.*?<svg[^>]*>|</svg>\s*$', '', svg, flags=re.S).strip()
        syms.append(f'<symbol id="i-{n}" viewBox="0 0 24 24">{inner}</symbol>')
    open('assets/iconos.svg', 'w').write('<svg xmlns="http://www.w3.org/2000/svg" style="display:none">' + ''.join(syms) + '</svg>\n')
    print('iconos:', len(syms))
# 4) Imágenes de Wikimedia en alta resolución (casi 4K) + versión rápida + miniatura borrosa
if cfg.get('imagenes'):
    from PIL import Image, ImageFilter
    os.makedirs('assets/img', exist_ok=True); meta = {}
    for key, url in cfg['imagenes'].items():
        m = re.match(r'(https://upload\.wikimedia\.org/wikipedia/commons)/thumb/(\w/\w\w)/([^/]+)/\d+px-[^/]+$', url)
        cands = []
        if m: cands = [f'{m.group(1)}/thumb/{m.group(2)}/{m.group(3)}/3840px-{m.group(3)}', f'{m.group(1)}/{m.group(2)}/{m.group(3)}']
        else: cands = [url]
        data = None
        for c in cands:
            try: data = get(c, BOT, 2); break
            except Exception as e: print('  no:', c[:100], e)
        if not data: print('FALLÓ', key); continue
        im = Image.open(io.BytesIO(data)); im = im.convert('RGB'); w, h = im.size
        big = im if w <= 3840 else im.resize((3840, round(h * 3840 / w)), Image.LANCZOS)
        big.save(f'assets/img/{key}-4k.webp', 'WEBP', quality=80, method=6)
        mid = im.resize((1440, round(h * 1440 / w)), Image.LANCZOS) if w > 1440 else im
        mid.save(f'assets/img/{key}.webp', 'WEBP', quality=78, method=6)
        tiny = im.resize((32, max(1, round(h * 32 / w))), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1))
        b = io.BytesIO(); tiny.save(b, 'WEBP', quality=40)
        meta[key] = {'w': big.size[0], 'h': big.size[1], 'ph': 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()}
        print('imagen:', key, big.size, os.path.getsize(f'assets/img/{key}-4k.webp') // 1024, 'KB')
    json.dump(meta, open('assets/img/imagenes.json', 'w'), separators=(',', ':'))
