"""Convierte la «Santa Biblia libre para el mundo» (dominio público, eBible.org: spablm, incluye los libros deuterocanónicos)
de USFM a archivos JSON por libro en biblia/<CÓDIGO>.json: {"c": {"1": {"1": "texto", ...}, ...}}."""
import json, os, re, sys, glob
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
def clean(t):
    t = re.sub(r'\\f .*?\\f\*', '', t)            # notas al pie
    t = re.sub(r'\\x .*?\\x\*', '', t)            # referencias cruzadas
    t = re.sub(r'\\w ([^|\\]*)\|[^\\]*\\w\*', r'\1', t)
    t = re.sub(r'\\\+?[a-z0-9]+\*?', '', t)      # resto de marcas
    return re.sub(r'\s+', ' ', t).strip()
books = {}
for f in sorted(glob.glob(os.path.join(src, '*.usfm')) + glob.glob(os.path.join(src, '*.SFM'))):
    txt = open(f, encoding='utf-8-sig').read()
    m = re.search(r'^\\id (\w{3})', txt, re.M)
    if not m: continue
    code = m.group(1).upper(); ch = None; data = {}; cur = None
    for line in txt.splitlines():
        mc = re.match(r'\\c (\d+)', line)
        if mc: ch = mc.group(1); data.setdefault(ch, {}); cur = None; continue
        if ch is None: continue
        for part in re.split(r'(?=\\v \d)', line):
            mv = re.match(r'\\v (\d+)[\w-]*\s*(.*)', part)
            if mv:
                cur = mv.group(1); data[ch][cur] = clean(mv.group(2))
            elif cur and not re.match(r'\\(s\d?|r|ms\d?|mt\d?|d|cl|h|toc\d?)\b', part):
                extra = clean(part)
                if extra: data[ch][cur] = (data[ch][cur] + ' ' + extra).strip()
    if data:
        json.dump({'c': data}, open(os.path.join(out, code + '.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
        books[code] = len(data)
json.dump({'fuente': 'Santa Biblia libre para el mundo (eBible.org, dominio público)', 'libros': books}, open(os.path.join(out, 'indice.json'), 'w'), ensure_ascii=False)
print(len(books), 'libros:', ' '.join(books))
L = json.load(open(os.path.join(out, 'LUK.json')))['c']['19']
print('Lucas 19,1-3:', ' '.join(L[str(v)] for v in range(1, 4)))
S = json.load(open(os.path.join(out, 'PSA.json')))['c']['15']
print('Salmo 15,1-2:', S['1'], S['2'])
for b in ('TOB', 'WIS', 'SIR', '1MA', 'BAR', 'ESG', 'DAG'):
    print(b, b in books)
