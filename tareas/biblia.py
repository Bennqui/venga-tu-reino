"""Convierte la Biblia Platense (Mons. Juan Straubinger; módulo SpaPlatense de CrossWire, dominio público)
a biblia/<COD>.json: {"c": {"cap": {"vers": "texto"}}}.
- Solo los 73 libros del canon católico.
- Numeración de la Vulgata (Salmo 22 = «El Señor es mi pastor», como el primer número del Leccionario: «Salmo 22(23)»).
- Joel y Malaquías se pasan a los capítulos que usa el Leccionario.
- El nombre divino «Yahvé» se escribe «el Señor», como pide la Iglesia en la liturgia (Congregación para el Culto Divino, 2008)."""
import json, os, re, sys
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
CODES = {'Genesis':'GEN','Exodus':'EXO','Leviticus':'LEV','Numbers':'NUM','Deuteronomy':'DEU','Joshua':'JOS','Judges':'JDG','Ruth':'RUT',
 'I Samuel':'1SA','II Samuel':'2SA','I Kings':'1KI','II Kings':'2KI','I Chronicles':'1CH','II Chronicles':'2CH','Ezra':'EZR','Nehemiah':'NEH',
 'Tobit':'TOB','Judith':'JDT','Esther':'EST','Job':'JOB','Psalms':'PSA','Proverbs':'PRO','Ecclesiastes':'ECC','Song of Solomon':'SNG',
 'Wisdom':'WIS','Sirach':'SIR','Isaiah':'ISA','Jeremiah':'JER','Lamentations':'LAM','Baruch':'BAR','Ezekiel':'EZK','Daniel':'DAN',
 'Hosea':'HOS','Joel':'JOL','Amos':'AMO','Obadiah':'OBA','Jonah':'JON','Micah':'MIC','Nahum':'NAM','Habakkuk':'HAB','Zephaniah':'ZEP',
 'Haggai':'HAG','Zechariah':'ZEC','Malachi':'MAL','I Maccabees':'1MA','II Maccabees':'2MA','Matthew':'MAT','Mark':'MRK','Luke':'LUK',
 'John':'JHN','Acts':'ACT','Romans':'ROM','I Corinthians':'1CO','II Corinthians':'2CO','Galatians':'GAL','Ephesians':'EPH','Philippians':'PHP',
 'Colossians':'COL','I Thessalonians':'1TH','II Thessalonians':'2TH','I Timothy':'1TI','II Timothy':'2TI','Titus':'TIT','Philemon':'PHM',
 'Hebrews':'HEB','James':'JAS','I Peter':'1PE','II Peter':'2PE','I John':'1JN','II John':'2JN','III John':'3JN','Jude':'JUD','Revelation of John':'REV'}
START = re.compile(r'(^|[.!?…:]\s+|[“"«¡¿(—\[]\s*)$')
def senor(t):
    t = re.sub(r'¡?Hallelú\s+Yah!?', lambda m: '¡Aleluya!' if m.group(0).startswith('¡') else 'Aleluya', t)
    t = re.sub(r'\bAdonai,\s+(Yahvé|Yah)\b', 'Señor Dios', t)
    t = re.sub(r'\bAdonai\s+(Yahvé|Yah)\b', 'Yahvé Dios', t)
    t = re.sub(r'\bAdonai\b', 'Señor', t)
    res, pos = [], 0
    for m in re.finditer(r'\b(Yahvé|Yah)\b', t):
        before, after = t[pos:m.start()], t[m.end():]
        whole_before = ''.join(res) + before
        voc = False
        if re.search(r'\boh\s+$', whole_before, re.I): voc = True
        elif re.match(r'\s*[,!]', after) and START.search(whole_before) and not re.match(r',\s*(tu|vuestro|nuestro|su|el)\s+Dios\b', after):
            voc = True
        if voc:
            res.append(before + 'Señor')
        else:
            mb = re.search(r'\b([Aa]|[Dd]e)\s+$', before)
            if mb:
                pre = before[:mb.start()]
                w = mb.group(1)
                res.append(pre + {'a': 'al', 'A': 'Al', 'de': 'del', 'De': 'Del'}[w] + ' Señor')
            else:
                res.append(before + ('El Señor' if START.search(whole_before) else 'el Señor'))
        pos = m.end()
    res.append(t[pos:])
    return ''.join(res)
def clean(t):
    t = t.replace('{}', '').replace('[', '').replace(']', '')
    t = senor(t)
    t = re.sub(r'([Ee]l) Señor, el Señor(?!,\s*Dios)', r'\1 Señor Dios', t)
    return re.sub(r'\s+', ' ', t).strip()
d = json.load(open(src, encoding='utf-8'))
libros = {}
for b in d['books']:
    code = CODES.get(b['name'])
    if not code: continue
    chs = {}
    for c in b['chapters']:
        vs = {str(v['verse']): clean(v['text']) for v in c['verses'] if v['text'].strip()}
        if vs: chs[str(c['chapter'])] = vs
    if code == 'MAL' and '4' in chs:      # Vulgata Mal 4,1-6 = Leccionario Mal 3,19-24
        for v, t in chs.pop('4').items(): chs['3'][str(int(v) + 18)] = t
    if code == 'JOL' and len(chs.get('2', {})) > 27:   # Vulgata Jl 2,28-32 = 3,1-5; Jl 3 = 4
        tres = chs.pop('3', {})
        chs['3'] = {str(int(v) - 27): chs['2'].pop(v) for v in list(chs['2']) if int(v) >= 28}
        if tres: chs['4'] = tres
    libros[code] = chs
    json.dump({'c': chs}, open(os.path.join(out, code + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump({'fuente': 'La Sagrada Biblia, versión de Mons. Juan Straubinger (Biblia Platense, 1944-1951), dominio público; texto del módulo SpaPlatense de CrossWire',
           'notas': 'Canon católico (73 libros). Salmos con la numeración de la Vulgata, como el primer número del Leccionario. El nombre «Yahvé» se escribe «el Señor».',
           'libros': {k: len(v) for k, v in libros.items()}}, open(os.path.join(out, 'indice.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(len(libros), 'libros')
