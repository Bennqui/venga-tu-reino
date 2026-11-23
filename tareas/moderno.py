"""Español actual para la Biblia de Straubinger: «vosotros» -> «ustedes», como se habla en Venezuela y en el Leccionario.

Cambia solo la segunda persona del plural; el resto del texto (y su sentido) queda igual:
- vosotros/vosotras -> ustedes; vuestro/a/os/as -> su/sus (el vuestro -> el suyo)
- verbos: sois -> son, habéis -> han, tenéis -> tienen, haréis -> harán, hicisteis -> hicieron, hagáis -> hagan...
- imperativos: mirad -> miren, venid -> vengan, levantaos -> levántense, decidle -> díganle
- os -> se (reflexivo), les o los (complemento); os lo -> se lo; daros -> darles, diciéndoos -> diciéndoles
Lo usa tareas/biblia.py; también se puede ejecutar solo: python3 tareas/moderno.py biblia
"""
import json, os, re, sys, unicodedata

L = r"A-Za-zÁÉÍÓÚáéíóúÑñÜü"
TOK = re.compile(r"[%s]+" % L)

def sin_tilde(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').replace('ñ', 'ñ')

TILDE = {'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú'}
QUITA = {v: k for k, v in TILDE.items()}

def quitar_tilde(s):
    return ''.join(QUITA.get(c, c) for c in s)

# ---------- verbos con cambio de raíz (en las formas con acento en la raíz) ----------
IE = """pensar cerrar comenzar empezar despertar sentar acertar apretar atravesar calentar confesar encerrar enterrar
gobernar helar manifestar merendar negar renegar quebrar recomendar encomendar regar sembrar temblar tentar desterrar
alentar desalentar zaherir concertar desconcertar apacentar acrecentar enmendar aterrar mentar plegar desplegar fregar segar cegar sosegar asentar errar
tener contener detener entretener mantener obtener retener sostener abstener atener
querer perder entender atender extender tender encender defender descender ascender trascender verter
venir convenir intervenir prevenir sobrevenir
arrepentir sentir consentir presentir resentir mentir desmentir convertir divertir advertir pervertir invertir revertir herir
preferir referir conferir proferir sugerir digerir hervir adherir requerir inquirir adquirir""".split()
UE = """contar descontar recontar encontrar mostrar demostrar probar aprobar comprobar recordar acordar costar acostar
rogar soltar sonar resonar soñar volar tronar colgar consolar renovar poblar despoblar apostar forzar esforzar almorzar
avergonzar trocar volcar revolcar degollar tostar morder
volver devolver envolver revolver resolver disolver absolver poder mover conmover promover remover llover doler oler
soler torcer retorcer cocer moler
dormir morir jugar""".split()
EI = """pedir despedir impedir medir servir seguir conseguir perseguir proseguir vestir revestir investir desvestir
repetir competir gemir rendir elegir corregir regir concebir decir bendecir maldecir contradecir freír reír sonreír
derretir embestir ceñir teñir reñir constreñir henchir""".split()
CAMBIO = {**{v: 'ie' for v in IE}, **{v: 'ue' for v in UE}, **{v: 'i' for v in EI}}
NO_CAMBIA = set("pretender ofender presentar representar intentar contentar ventilar dispensar compensar entregar "
                "interrogar prorrogar derogar arrogar personar ostentar sustentar cementar".split())

def cambio(inf):
    if inf in NO_CAMBIA: return None
    return CAMBIO.get(inf)

def aplicar_cambio(raiz, tipo):
    """Cambia la vocal de la raíz: e/i -> ie, o/u -> ue, e -> i (sin tocar la u de gu/qu)."""
    if not tipo: return raiz
    for i in range(len(raiz) - 1, -1, -1):
        c = raiz[i]
        if c == 'u' and i and raiz[i - 1] in 'gq': continue
        if tipo == 'ie' and c in 'ei': return raiz[:i] + 'ie' + raiz[i + 1:]
        if tipo == 'ue' and c in 'ou':
            if i == 0: return 'hue' + raiz[1:]                       # oler -> huelen
            if raiz[i - 1] == 'g': return raiz[:i] + 'üe' + raiz[i + 1:]  # avergonzar -> avergüenzan
            return raiz[:i] + 'ue' + raiz[i + 1:]
        if tipo == 'i' and c == 'e': return raiz[:i] + 'i' + raiz[i + 1:]
    return raiz

def pret_ir(raiz, inf):
    """Raíz del pretérito «ellos» de los -ir con cambio: pedir -> pid, morir -> mur."""
    t = cambio(inf)
    if not t or not inf.endswith(('ir', 'ír')): return raiz
    for i in range(len(raiz) - 1, -1, -1):
        c = raiz[i]
        if c == 'u' and i and raiz[i - 1] in 'gq': continue
        if c == 'e': return raiz[:i] + 'i' + raiz[i + 1:]
        if c == 'o': return raiz[:i] + 'u' + raiz[i + 1:]
        if c in 'aiu': return raiz
    return raiz

ACENTO_I = set("enviar confiar fiar desviar guiar criar espiar vaciar variar ampliar rociar desafiar extraviar porfiar "
               "continuar actuar habituar evaluar insinuar reunir prohibir rehusar aislar".split())

# ---------- subjuntivo «ustedes» a partir del infinitivo (para los imperativos) ----------
SUBJ_IRR = {'ser': 'sean', 'ir': 'vayan', 'ver': 'vean', 'dar': 'den', 'estar': 'estén', 'saber': 'sepan',
            'haber': 'hayan', 'caber': 'quepan', 'oír': 'oigan', 'reír': 'rían', 'oler': 'huelan', 'errar': 'yerren',
            'jugar': 'jueguen', 'prever': 'prevean'}
G_IRR = {'hacer': 'hag', 'decir': 'dig', 'tener': 'teng', 'venir': 'veng', 'poner': 'pong', 'salir': 'salg',
         'valer': 'valg', 'traer': 'traig', 'caer': 'caig', 'satisfacer': 'satisfag'}

def subj3(inf):
    if inf in SUBJ_IRR: return SUBJ_IRR[inf]
    for base, r in sorted(G_IRR.items(), key=lambda x: -len(x[0])):
        if inf.endswith(base):
            pre = inf[:-len(base)]
            if base == 'decir' and pre in ('ben', 'mal'): return pre + 'digan'
            return pre + r + 'an'
    raiz, t = inf[:-2], quitar_tilde(inf[-2:])
    tipo = cambio(inf)
    if inf.endswith('uir') and not inf.endswith(('guir', 'quir')):
        return raiz + 'yan'
    if t == 'ar':
        r = aplicar_cambio(raiz, tipo)
        if r.endswith('c'): r = r[:-1] + 'qu'
        elif r.endswith('g'): r = r + 'u'
        elif r.endswith('z'): r = r[:-1] + 'c'
        elif r.endswith('gu'): r = r[:-2] + 'gü'
        if inf in ACENTO_I:
            r = r[:-1] + TILDE[r[-1]] if r[-1] in 'iu' else r
        return r + 'en'
    # -er / -ir
    if re.search(r'[aeiou]c$', raiz) and inf not in ('cocer', 'mecer'): r = raiz[:-1] + 'zc'
    elif raiz.endswith('duc'): r = raiz[:-1] + 'zc'
    elif raiz.endswith('c'): r = raiz[:-1] + 'z'
    elif raiz.endswith('gu') and t == 'ir': r = raiz[:-1]
    elif raiz.endswith('g'): r = raiz[:-1] + 'j'
    else: r = raiz
    if t == 'ir' and tipo == 'ie' and not inf.endswith('venir'):
        r = aplicar_cambio(r, 'ie')
    elif t == 'ir' and tipo == 'ue':
        r = aplicar_cambio(r, 'ue')
    else:
        r = aplicar_cambio(r, tipo)
    if inf in ACENTO_I and r[-1] in 'iu': r = r[:-1] + TILDE[r[-1]]
    return r + 'an'

# ---------- acento al añadir pronombres al final (levanten + se -> levántense) ----------
NUC = re.compile(r'[iuü]?[aeoáéó][iuy]?(?![aeo])|[iu][iu]|[aeiouáéíóú]', re.I)

def con_enclitico(base, encl):
    if re.search('[áéíóú]', base): return base + encl
    nucs = [m for m in re.finditer(r'[aeiouáéíóúü]+', base, re.I)]
    # separa hiatos de vocales fuertes (se-an, le-an)
    sil = []
    for m in nucs:
        s, st = m.group(), m.start()
        partes, ini = [], 0
        for i in range(1, len(s)):
            if s[i - 1] in 'aeoAEO' and s[i] in 'aeoAEO':
                partes.append((st + ini, s[ini:i])); ini = i
        partes.append((st + ini, s[ini:]))
        sil.extend(partes)
    if len(sil) < 2: return base + encl
    pos, v = sil[-2]
    # la vocal que lleva la tilde: la fuerte, o la segunda de iu/ui
    idx = None
    for i, c in enumerate(v):
        if c in 'aeoAEO': idx = i; break
    if idx is None: idx = len(v) - 1
    k = pos + idx
    return base[:k] + TILDE.get(base[k], base[k]) + base[k + 1:] + encl

# ---------- conjugaciones de «vosotros» -> «ustedes» ----------
IRR = {'sois': 'son', 'vais': 'van', 'dais': 'dan', 'deis': 'den', 'veis': 'ven', 'habéis': 'han', 'estáis': 'están',
       'estéis': 'estén', 'oís': 'oyen', 'reís': 'ríen', 'fuisteis': 'fueron', 'disteis': 'dieron',
       'visteis': 'vieron', 'erais': 'eran', 'seáis': 'sean', 'id': 'vayan', 'idos': 'váyanse',
       'hayáis': 'hayan', 'vayáis': 'vayan', 'oíd': 'oigan', 'podáis': 'puedan', 'erráis': 'yerran',
       'erréis': 'yerren', 'erguíos': 'yérganse', 'iréis': 'irán', 'iríais': 'irían', 'ibais': 'iban',
       'hubiereis': 'han', 'fuereis': 'fueren', 'viereis': 'ven', 'oyereis': 'oyen', 'dijereis': 'dicen',
       'tuviereis': 'tienen', 'retuviereis': 'retienen', 'pudiereis': 'pueden', 'quisiereis': 'quieren',
       'cayereis': 'caen', 'muriereis': 'mueren', 'convirtiereis': 'convierten', 'estaos': 'quédense', 'creyereis': 'creen', 'estuviereis': 'están', 'hiciereis': 'hacen'}
NO_INF = set('cuer fuer postrer primer tercer tender mujer lugar altar mar collar pilar'.split())
NO_VERBO = set('acad ebed ébed sémed jasís seis dieciséis veintiséis correos sabeos seos heredad merced sabad arad libertad intimidad hadad terceros primeros tenderos'.split())

def inf_de(raiz, term, infs):
    """Infinitivo probable de una raíz de presente («ten» + «éis» -> tener)."""
    cand = []
    if term == 'áis': cand = [raiz + 'ar']
    elif term == 'éis': cand = [raiz + 'er']
    elif term == 'ís': cand = [raiz + 'ir']
    return cand

def inf_subj(raiz, term):
    """Infinitivos posibles de una raíz de subjuntivo («hag»+«áis» -> hacer)."""
    c = []
    if term == 'éis':
        r = raiz
        if r.endswith('qu'): r = r[:-2] + 'c'
        elif r.endswith('gu'): r = r[:-1]
        elif r.endswith('gü'): r = r[:-1] + 'u'
        elif r.endswith('c'): r = r[:-1] + 'z'
        c.append(r + 'ar')
    else:
        for base, g in G_IRR.items():
            if raiz.endswith(g): c.append(raiz[:-len(g)] + base)
        r = raiz
        if r.endswith('zc'): c += [r[:-2] + 'cer', r[:-2] + 'cir']
        if r.endswith('j'): c += [r[:-1] + 'ger', r[:-1] + 'gir']
        if r.endswith('z'): c += [r[:-1] + 'cer']
        if r.endswith('y'): c += [r[:-1] + 'ir']
        c += [r + 'er', r + 'ir', r + 'uir']
        # -ir con cambio: sint -> sentir, durm -> dormir, pid -> pedir, sig -> seguir
        for i in range(len(r) - 1, -1, -1):
            if r[i] in 'iu':
                alt = r[:i] + ('e' if r[i] == 'i' else 'o') + r[i + 1:]
                c += [alt + 'ir', alt + 'uir'.replace('u', '') if False else alt + 'ir']
                if alt.endswith('g'): c.append(alt + 'uir')
                if alt.endswith('j'): c.append(alt[:-1] + 'gir')
                break
            if r[i] in 'aeo': break
    return c

def presente(w, infs):
    """Formas de presente (indicativo o subjuntivo) en -áis/-éis/-ís."""
    for term in ('áis', 'éis', 'ís'):
        if w.endswith(term):
            raiz = w[:-len(term)]
            break
    else:
        return None
    fin = 'an' if term == 'áis' else 'en'
    # 1) indicativo: tenéis -> tener
    ind = inf_de(raiz, term, infs)[0]
    # 2) subjuntivo: hagáis -> hacer, entréis -> entrar
    sub = inf_subj(raiz, term)
    inf = None
    if ind in infs or ind in CAMBIO or ind in ACENTO_I: inf, modo = ind, 'ind'
    else:
        for c in sub:
            if c in infs or c in CAMBIO or c in ACENTO_I: inf, modo = c, 'sub'; break
    if term == 'ís':
        if not inf: return None                     # país, Laquís...: no son verbos
        if raiz.endswith('u') and not raiz.endswith(('gu', 'qu')): return raiz + 'yen'   # huís -> huyen
    if inf is None:
        inf, modo = (ind, 'ind') if term == 'áis' else (ind, 'ind')
    tipo = cambio(inf)
    if modo == 'sub' and any(raiz.endswith(g) for g in G_IRR.values()): tipo = None
    r = raiz
    if tipo:
        if modo == 'ind' or quitar_tilde(inf[-2:]) == 'ar' or quitar_tilde(inf[-2:]) == 'er':
            r = aplicar_cambio(raiz, tipo)
        else:   # subjuntivo de -ir: sintáis -> sientan, durmáis -> duerman, pidáis -> pidan
            r = aplicar_cambio(raiz, tipo) if tipo in ('ie', 'ue') else raiz
    if inf.endswith('venir') and modo == 'sub': r = raiz      # vengáis -> vengan
    if inf in ACENTO_I and r and r[-1] in 'iu': r = r[:-1] + TILDE[r[-1]]
    return r + fin

FUT_IRR = ('haréis', 'diréis', 'habréis', 'sabréis', 'podréis', 'querréis', 'cabréis', 'saldréis', 'valdréis')

def verbo(w, infs):
    lw = w.lower()
    if lw in NO_VERBO: return None
    if lw in IRR: return IRR[lw]
    # pretérito: hicisteis -> hicieron, pedisteis -> pidieron, ceñisteis -> ciñeron
    m = re.match(r'(.*?)(asteis|isteis|ísteis)$', lw)
    if m:
        r, t = m.groups()
        if t == 'asteis': return r + 'aron'
        if r.endswith(('j', 'ñ', 'll')): return pret_ir(r, r + 'ir') + 'eron'
        if (r and r[-1] in 'aeou' and not r.endswith(('gu', 'qu'))) or t == 'ísteis': return r + 'yeron'
        return pret_ir(r, r + 'ir') + 'ieron'
    # futuro: amaréis -> amarán (no confundir con «celebréis», subjuntivo)
    if lw.endswith('réis'):
        base = lw[:-3]
        b2 = base[:-2] + 'ír' if base.endswith('ir') else base
        if (lw.endswith(FUT_IRR) or re.search(r'(tendr|podr|habr|sabr|cabr|pondr|saldr|vendr|valdr|querr)$', base)
                or (not (base + 'ar' in infs or base + 'er' in infs)
                    and (base in infs or b2 in infs or (re.search(r'(ar|er|ir)$', base) and len(base) > 3)))):
            return lw[:-4] + 'rán'
    # futuro de subjuntivo («si escuchareis»): presente de hoy («si escuchan»)
    m = re.match(r'(.+?)(areis|iereis|yereis)$', lw)
    if m and len(lw) > 7:
        r, t = m.groups()
        if t == 'areis':
            return aplicar_cambio(r, cambio(r + 'ar')) + 'an'
        inf = r + ('er' if r + 'er' in infs else 'ir')
        rr = r
        if cambio(inf) in ('ie', 'ue'): rr = aplicar_cambio(r, cambio(inf))
        if t == 'yereis': rr = r + 'y'
        return rr + 'en'
    for a, b in (('ríais', 'rían'), ('íais', 'ían'), ('abais', 'aban'), ('rais', 'ran'), ('seis', 'sen')):
        if lw.endswith(a) and len(lw) > len(a) + 1:
            if a == 'seis' and not re.search(r'(a|e|ie|ye)seis$', lw): continue
            return lw[:-len(a)] + b
    return presente(lw, infs)

ENC = r'(me|te|le|les|lo|la|los|las|nos|selo|sela|selos|selas|melo|mela|nosla|noslo)'

def imperativo(w, infs, prev):
    """mirad -> miren, levantaos -> levántense, decidle -> díganle."""
    lw = w.lower()
    if lw in NO_VERBO: return None
    if lw in IRR: return IRR[lw]
    if lw == 'sed':
        sig, pausa = SIG.get('w', ''), SIG.get('pausa', False)
        if prev in SED_SUST or (pausa and sig not in ('pues', 'sí')): return None
        return 'sean' if (sig.endswith('s') or sig in ('pues', 'conmigo', 'también', 'como', 'en', 'sí')) else None
    if lw in ('id', 'oíd', 'idos'): return IRR[lw]
    m = re.match(r'(.*[aeií])d(%s)?$' % ENC[1:-1] if False else r'(.*[aeií])d' + ENC + r'?$', lw)
    if m and len(lw) > 2:
        raiz, enc = m.group(1), m.group(2) or ''
        inf = quitar_tilde(raiz[:-1]) + raiz[-1] + 'r'
        inf2 = quitar_tilde(raiz) + 'r'
        inf = inf2 if inf2 in infs or inf2 in CAMBIO or inf2 in SUBJ_IRR or any(inf2.endswith(b) for b in G_IRR) else (raiz + 'r')
        if raiz.endswith('í'): inf = raiz[:-1] + 'ir' if raiz[:-1] + 'ir' in infs or raiz == 'oí' else raiz + 'r'
        if raiz == 'oí': inf = 'oír'
        if not (inf in infs or inf in CAMBIO or inf in SUBJ_IRR or any(inf.endswith(b) for b in G_IRR)):
            return None
        if enc.startswith('se') or enc in ('melo', 'mela'):
            pass
        s = tildes(subj3(inf))
        return con_enclitico(s, enc) if enc else s
    m = re.match(r'(.*[aeí])os$', lw)
    if m and len(m.group(1)) >= 3:
        raiz = m.group(1)
        inf = quitar_tilde(raiz) + 'r'
        if inf in infs or inf in CAMBIO:
            return con_enclitico(tildes(subj3(inf)), 'se')
    return None

SIG = {}
SED_SUST = set("la de su mi tu con sin por nuestra vuestra gran tanta tengo tienes tiene tienen tenía tenían tuvo "
               "tuvieron tendrá tendrán tendré padecen padece mucha esa esta y ni que mi el tenéis tengáis tendréis teníais padecéis morir muero muera morirán muriendo sufrimos sufrían sufriendo padecieron padecido grandísima teniendo tienes tenga hambre".split())

# «os» con verbos que llevan complemento directo de persona -> «los»; si no, «les» (les digo, les doy)
DIRECTO = re.compile(r'^(am|llam|salv|libr|bendig|bendec|bendij|elij|eleg|escog|escoj|conoc|conozc|guard|llev|traig|traj|'
                     r'sac|busc|esper|juzg|castig|consuel|conduc|conduz|conduj|dispers|disip|reun|reún|multiplic|'
                     r'destru|entreg|visit|purific|santific|rescat|redim|san|odi|aborrec|aborrez|persig|perseg|mat|her|'
                     r'hir|tom|pus|pong|establec|planst|plant|edific|introduc|introduj|exhort|bautiz|envi|recib|recog|'
                     r'recoj|sostend|sosten|sostuv|fortalec|confirm|acog|acoj|alimen|apacent|conden|acus|engañ|turb|'
                     r'persuad|amonest|exalt|humill|proteg|protej|defend|defiend|guí|gui|arroj|expuls|ech|esparc|esparz|'
                     r'cautiv|vend|compr|cuid|conserv|sell|ung|ungi|prob|prueb|tient|provoc|alegr|consagr|invit|'
                     r've|vi|ver|hall|encontr|encuentr|aguard|socorr|ayud|consol|reconoc|devor|destroz|aniquil|'
                     r'extermin|arranc|lanz|precipit|abandon|desampar|olvid|recuerd|record|pastor|congreg|junt|'
                     r'hic|har|hag|hac|ech|vuelv|volv|devuelv|devolv|lav|limpi|perdon|exhort|import|molest|asust|'
                     r'espant|aterr|atemoriz|asombr|sorprend|confund|avergonz|cubr|vist|vest|cort|derrib|venc|venz|'
                     r'reprend|preced|enví|corrig|correg|instru|form|engendr|alab|seduj|seduc|exclu|insult|maldig|maldij|maldec|calumni|golpe|abofete|despreci|desprecia|rechaz|apedre|encarcel|prend|ultraj|vitupe|escarne|azot|flagel|crucific|adopt|justific|glorific|santific|'
                     r'consagr|unj|ung|hiri|suj|sujet|somet|domin|oprim|aflig|afligi|azot|herid)', re.I)
AUX = set("he has ha hemos han había habían habrá habrán habré hube hubo haya hayan voy va vamos van iba iban "
          "quiero quiere quieren quise puedo puede pueden podrá podré debo debe deben suelo vuelvo vuelve "
          "vendré vendrá vino viene hago hace estoy está están no".split())

DET = set('el la los las un una unos unas este esta estos estas esto eso esa ese esos esas aquel aquella aquello mi mis '
          'tu tus su sus nuestro nuestra nuestros nuestras todo toda todos todas '
          'algo nada cuanto cuanta cuantos cuantas pan agua tierra paz vida gloria'.split())

def tras(toks, j, texto, n):
    """Palabras que siguen al token j, sin cruzar una puntuación."""
    out = []
    for x in range(j + 1, min(len(toks), j + 1 + n)):
        if re.search(r'[.,;:!?«»“”()]', texto[toks[x - 1][1]:toks[x][0]]): break
        w = toks[x][2]
        out.append(w if w[:1].isupper() and len(out) else w.lower())
    return out

def os_por(sig, sig2, es_vos, despues=()):
    """«os» ante un verbo que no es de «ustedes»: «los» si ustedes son el complemento directo (los amo),
    «les» si reciben algo (les doy la paz, les digo)."""
    if es_vos: return 'se'
    if sig in ('lo', 'la', 'los', 'las'): return 'se'
    v, k = sig, 0
    if v in AUX and sig2: v, k = sig2, 1
    if not DIRECTO.match(v or ''): return 'les'
    if re.match(r'^env[ií]', v or '') and despues[k:k + 1] and despues[k].lower() not in ('como', 'a', 'al'): return 'les'   # «les envío profetas» / «los envío como ovejas»
    obj = list(despues[k:k + 3])
    if not obj or obj[0].lower() not in DET: return 'los'
    if len(obj) > 1 and obj[0].lower() in ('el', 'la', 'su') and obj[1][:1].isupper(): return 'los'
    obj = [w.lower() for w in obj]   # «los prueba el Señor» (sujeto)
    # «los odien los hombres», «los devorará la tierra»: si el artículo concuerda con el verbo, es el sujeto
    if obj[0] in ('el', 'la', 'los', 'las') and (obj[0] in ('los', 'las')) == sig.endswith('n'): return 'los'
    return 'les'

# ---------- segunda pasada: futuro de subjuntivo y pronombres al final del verbo ----------
ENCL_PAS = {'díjole': 'le dijo', 'díjoles': 'les dijo', 'díjome': 'me dijo', 'díjolo': 'lo dijo', 'apareciósele': 'se le apareció',
            'habíase': 'se había', 'habíanse': 'se habían', 'hacíanse': 'se hacían', 'hacíale': 'le hacía',
            'fortalecíase': 'se fortalecía', 'prendiósele': 'se le prendió', 'púsose': 'se puso', 'púsole': 'le puso',
            'púsolo': 'lo puso', 'púsolas': 'las puso', 'repúsole': 'le repuso', 'reprendíanle': 'le reprendían',
            'respondióle': 'le respondió', 'hízolo': 'lo hizo', 'hízose': 'se hizo', 'dióme': 'me dio',
            'bendíjolos': 'los bendijo', 'ruégote': 'te ruego', 'hallábase': 'se hallaba', 'levantóse': 'se levantó',
            'fuése': 'se fue', 'acercóse': 'se acercó', 'díjose': 'se dijo', 'estimádselo': 'estímenlo', 'daos': 'dense'}

PRET_IRR = {'hub': 'haber', 'hic': 'hacer', 'hiz': 'hacer', 'vin': 'venir', 'dij': 'decir', 'tuv': 'tener', 'quis': 'querer',
            'pud': 'poder', 'pus': 'poner', 'sup': 'saber', 'estuv': 'estar', 'anduv': 'andar', 'traj': 'traer',
            'cup': 'caber', 'plugu': 'placer', 'fu': 'ser', 'di': 'dar', 'vi': 'ver', 'oy': 'oír', 'cay': 'caer', 'crey': 'creer',
            'ley': 'leer', 'conduj': 'conducir', 'produj': 'producir', 'introduj': 'introducir', 'reduj': 'reducir',
            'bendij': 'bendecir', 'maldij': 'maldecir', 'contradij': 'contradecir', 'predij': 'predecir',
            'satisfic': 'satisfacer', 'deshic': 'deshacer', 'rehic': 'rehacer'}
PRES_IRR = {'haber': ('ha', 'han'), 'hacer': ('hace', 'hacen'), 'venir': ('viene', 'vienen'), 'decir': ('dice', 'dicen'),
            'tener': ('tiene', 'tienen'), 'querer': ('quiere', 'quieren'), 'poder': ('puede', 'pueden'),
            'poner': ('pone', 'ponen'), 'saber': ('sabe', 'saben'), 'estar': ('está', 'están'), 'ser': ('es', 'son'),
            'ir': ('va', 'van'), 'dar': ('da', 'dan'), 'ver': ('ve', 'ven'), 'oír': ('oye', 'oyen'), 'caer': ('cae', 'caen'),
            'traer': ('trae', 'traen'), 'creer': ('cree', 'creen'), 'leer': ('lee', 'leen'), 'caber': ('cabe', 'caben'),
            'andar': ('anda', 'andan'), 'reír': ('ríe', 'ríen')}
NO_FS = set('quiere quieren hiere hieren profiere profieren refiere refieren adquiere adquieren requiere requieren '
            'prefiere prefieren sugiere sugieren difiere difieren confiere confieren infiere infieren transfiere '
            'transfieren inquiere inquieren digiere digieren adhiere adhieren interfiere zare separe preparen prepare '
            'declare compare ampare repare mare clare tare zahiere zahieren reparen declaren separen amparen paren pare desampare'.split())

def lema_fs(r, t, infs):
    """Infinitivo de un futuro de subjuntivo: toc+are -> tocar, pid+iere -> pedir, hub+iere -> haber."""
    if t.startswith('ar'):
        if len(r) >= 2 and (r + 'ar') in infs: return r + 'ar'
        if len(r) >= 3 and (r + 'arar') not in infs and (r + 'rar') not in infs: return r + 'ar'
        return None
    if r in ('d', 'v'): return {'d': 'dar', 'v': 'ver'}[r]
    for pre in ('', 'con', 'de', 're', 'pre', 'pro', 'sobre', 'inter', 'ob', 'sos', 'man', 'dis', 'pro', 'im', 'ex', 'com', 'su', 'pos'):
        if r.startswith(pre):
            st = r[len(pre):]
            if st in PRET_IRR:
                base = PRET_IRR[st]
                if pre and base in ('dar', 'ver', 'ser', 'oír', 'leer', 'creer'): continue
                return pre + base
    for e in ('er', 'ir'):
        if r + e in infs: return r + e
    # -ir con cambio en el pretérito: pid -> pedir, mur -> morir, sirv -> servir, convirt -> convertir
    for i in range(len(r) - 1, -1, -1):
        if r[i] == 'u' and i and r[i - 1] in 'gq': continue
        if r[i] in 'iu':
            alt = r[:i] + ('e' if r[i] == 'i' else 'o') + r[i + 1:] + 'ir'
            if alt in infs or alt in CAMBIO: return alt
            break
        if r[i] in 'aeo': break
    if r.endswith('uy'): return r[:-1] + 'ir'          # destruyere -> destruir
    if r.endswith('ey'): return r[:-1] + 'er'          # poseyere -> poseer
    if len(r) >= 3: return r + 'er'                    # en 3.ª persona, -er y -ir se conjugan igual
    return None

def presente_de(inf, plural, modo, sig=''):
    """Presente de indicativo o subjuntivo, 3.ª persona (él / ellos-ustedes)."""
    if modo == 'sub':
        s = tildes(subj3(inf))
        if plural: return s
        s = s[:-1]
        return {'de': 'dé', 'este': 'esté'}.get(s, s) if inf in ('dar', 'estar') else s
    if inf == 'haber' and not re.search(r'(ado|ido|to|so|cho)$', sig or ''): return 'hay' if not plural else 'hay'
    for base, (sg, pl) in sorted(PRES_IRR.items(), key=lambda x: -len(x[0])):
        if inf == base or (inf.endswith(base) and len(base) > 3):
            pre = inf[:-len(base)]
            return pre + (pl if plural else sg)
    raiz, t = inf[:-2], quitar_tilde(inf[-2:])
    if inf.endswith('uir') and not inf.endswith(('guir', 'quir')): return raiz + ('yen' if plural else 'ye')
    r = aplicar_cambio(raiz, cambio(inf))
    if t == 'ar':
        fin = 'an' if plural else 'a'
    else:
        if raiz.endswith('gu') and t == 'ir' and not cambio(inf): r = raiz
        fin = 'en' if plural else 'e'
    if inf in ACENTO_I and r[-1] in 'iu': r = r[:-1] + TILDE[r[-1]]
    return tildes(r + fin)

def si_antes(toks, i, texto):
    for j in range(i - 1, max(-1, i - 14), -1):
        if re.search(r'[.;:?!«»“”]', texto[toks[j][1]:toks[j + 1][0]]): return False
        w = toks[j][2].lower()
        if w == 'si': return True
        if w in ('que', 'quien', 'cuando', 'donde', 'adonde', 'cual', 'cuanto', 'cuantos', 'cuanta', 'como', 'mientras', 'hasta', 'antes'):
            return False
    return False

def fut_subj(lw, toks, i, texto, infs, sig, prev=''):
    if lw in NO_FS: return None
    m = re.match(r'^(.+?)(areis|iereis|yereis|ereis|aren|ieren|yeren|eren|are|iere|yere|ere)$', lw)
    if not m: return None
    r, t = m.groups()
    if t.startswith('y'): r, t = r + 'y', t[1:]
    if t.startswith('e') and not (r.endswith(('j', 'y')) or r in ('fu', 'tuv')): return None    # dijere, oyere
    if t.startswith('e'): t = 'i' + t
    vos = t.endswith('eis')
    plural = vos or t.endswith('en')
    tt = t.replace('eis', 'e').replace('en', 'e') if not t.startswith('ar') else ('are')
    inf = lema_fs(r, 'are' if t.startswith('ar') else 'iere', infs)
    if not inf: return None
    if inf == 'ser' and (sig in ('a', 'al', 'hacia', 'adonde', 'donde') or prev in ('adonde', 'donde', 'dondequiera')): inf = 'ir'
    modo = 'ind' if si_antes(toks, i, texto) else 'sub'
    return presente_de(inf, plural, modo, sig)

def tildes(n):
    return re.sub(r'^(reun|prohib|rehus|aisl)(?=(a|e|an|en|anse|ense|e|a)$)', lambda m: {'reun': 'reún', 'prohib': 'prohíb', 'rehus': 'rehús', 'aisl': 'aísl'}[m.group(1)], n)

def caso(orig, nuevo):
    if orig[:1].isupper(): return nuevo[:1].upper() + nuevo[1:]
    return nuevo

def vos_antes(toks, i, texto, infs):
    """¿Hay un verbo de «ustedes» poco antes, en la misma frase? («quieren iros» -> «irse»)"""
    for j in range(i - 1, max(-1, i - 6), -1):
        if re.search(r'[.;:!?,]', texto[toks[j][1]:toks[j + 1][0]]): return False
        if es_vos_verbo(toks[j][2], infs): return True
    return False

def es_vos_verbo(w, infs):
    if not w: return False
    lw = w.lower()
    if lw in IRR and lw not in ('id', 'idos', 'sed', 'oíd'): return True
    if re.search(r'(asteis|isteis|ísteis|íais|abais|rais|seis|reis|éis|áis)$', lw) and lw not in ('seis',): return True
    if lw.endswith('ís') and presente(lw, infs): return True
    return False

FUNC = set('que y o u en de con por para a no es son está están se los las el la lo le les como cuando pues mas sino ni si porque'.split())
POSES = {'vuestro': 'su', 'vuestra': 'su', 'vuestros': 'sus', 'vuestras': 'sus'}
SUYO = {'vuestro': 'suyo', 'vuestra': 'suya', 'vuestros': 'suyos', 'vuestras': 'suyas'}

def modernizar(texto, infs):
    toks = [(m.start(), m.end(), m.group()) for m in TOK.finditer(texto)]
    out, pos = [], 0
    for i, (a, b, w) in enumerate(toks):
        lw = w.lower()
        prev = toks[i - 1][2].lower() if i else ''
        sig = toks[i + 1][2].lower() if i + 1 < len(toks) else ''
        sig2 = toks[i + 2][2].lower() if i + 2 < len(toks) else ''
        n = None
        SIG['w'] = sig
        SIG['pausa'] = bool(i + 1 < len(toks) and re.search(r'[.,;:!?]', texto[b:toks[i + 1][0]]))
        if lw in ('vosotros', 'vosotras'): n = 'ustedes'
        elif lw in POSES:
            despues = texto[b:toks[i + 1][0]] if i + 1 < len(toks) else texto[b:]
            pospuesto = bool(re.match(r'\s*[^\s%s]' % L, despues)) or not sig or sig in FUNC
            if prev in ('el', 'la', 'los', 'las', 'lo') or (prev in ('es', 'son', 'sea', 'sean', 'será', 'serán') and pospuesto): n = SUYO[lw]
            elif pospuesto and prev not in ('de', 'a', 'en', 'con', 'por', 'para', 'y', 'o', 'que', 'todo', 'toda', 'todos', 'todas'): n = 'de ustedes'
            else: n = POSES[lw]
        elif lw == 'os' and sig in ('unos', 'mutuamente'):
            n = 'se'
        elif lw == 'os' and prev == 'se':
            n = 'les'
        elif lw == 'os':
            n = os_por(sig, sig2, es_vos_verbo(sig, infs) or (sig in ('lo', 'la', 'los', 'las') and es_vos_verbo(sig2, infs)),
                       tras(toks, i + 1, texto, 4))
        elif lw.endswith('ndoos'):
            base = lw[:-2]
            n = base + ('los' if DIRECTO.match(sin_tilde(base)) else 'les')
            if es_vos_reflexivo_gerundio(base) or sig in ('unos', 'mutuamente'): n = base + 'se'
        elif lw in NO_VERBO:
            n = None
        elif (re.search(r'(ar|er|ir|ír)os$', lw) and lw[:-2] in infs and lw[:-2] not in NO_INF) or lw == 'iros':
            base = lw[:-2]
            if sig in ('unos', 'mutuamente') or lw == 'iros' or vos_antes(toks, i, texto, infs) or REFLEX_INF.match(base): n = base + 'se'
            elif DIRECTO.match(base) and not (base.startswith('envi') and sig == 'a') and sig not in DET: n = base + 'los'
            else: n = base + 'les'
        else:
            medio = w[0].isupper() and re.search(r'[%s,;]\s*$' % L, texto[:a]) is not None
            if lw in ENCL_PAS: n = ENCL_PAS[lw]
            elif medio: n = None
            else: n = fut_subj(lw, toks, i, texto, infs, sig, prev) or imperativo(w, infs, prev) or verbo(w, infs)
        if n and n != lw:
            out.append(texto[pos:a]); out.append(caso(w, tildes(n))); pos = b
    out.append(texto[pos:])
    t = ''.join(out)
    return t

# gerundios reflexivos: «apartándoos» -> «apartándose» (el sujeto son ustedes)
REFLEX_GER = re.compile(r'^(apart|postr|acord|separ|alleg|arrim|comport|rebel|apoy|convirti|apropi|esforz|despoj|'
                        r'sujet|ocup|adhiri|opon|entreteni|corrompi|guard|deshaci)', re.I)

REFLEX_INF = re.compile(r'^(levantar|apartar|acordar|acercar|alegrar|regocijar|arrepentir|convertir|humillar|someter|despojar|revestir|vestir|esforzar|gloriar|jactar|quejar|atrever|postrar|prosternar|reconciliar|abstener)$')

def es_vos_reflexivo_gerundio(base):
    return bool(REFLEX_GER.match(sin_tilde(base).replace('a', 'a')) or REFLEX_GER.match(base))

def infinitivos(textos):
    s = set()
    for t in textos:
        for w in TOK.findall(t):
            lw = w.lower()
            for x in (lw, re.sub(r'(me|te|le|les|lo|la|los|las|nos|se|selo|sela|selos)$', '', lw)):
                if re.search(r'(ar|er|ir|ír)$', x) and len(x) > 2: s.add(x)
    return s

ERRATAS = {('LEV', '25', '25'): ('se empobreceré', 'se empobreciere'), ('JDG', '4', '22'): ('te mostrare', 'te mostraré')}

def modernizar_libros(libros):
    """libros: {cod: {cap: {vers: texto}}} -> mismo formato, en español actual."""
    # erratas del texto de origen
    for (lib, c, v), (a, b) in ERRATAS.items():
        t = libros.get(lib, {}).get(c, {}).get(v)
        if t and a in t: libros[lib][c][v] = t.replace(a, b)
    infs = infinitivos(t for chs in libros.values() for c in chs.values() for t in c.values())
    infs |= set(CAMBIO) | set(ACENTO_I) | set('loar aullar aclamar prorrumpir uncir ulular moler expurgar anhelar reaccionar aprovechar desmochar '
             'derrumbar educar embrazar repasar engrasar alegar despejar acicalar lamentar forjar confortar dilatar encaminar '
             'maravillar apurar admirar ensanchar pasmar apegar desaprobar horrorizar emborrachar circular salmodiar preceder'.split())
    return {k: {c: {v: modernizar(t, infs) for v, t in vs.items()} for c, vs in chs.items()} for k, chs in libros.items()}

if __name__ == '__main__':
    d = sys.argv[1]
    libros = {f[:-5]: json.load(open(os.path.join(d, f), encoding='utf-8'))['c']
              for f in sorted(os.listdir(d)) if f.endswith('.json') and f != 'indice.json'}
    nuevos = modernizar_libros(libros)
    for k, chs in nuevos.items():
        json.dump({'c': chs}, open(os.path.join(d, k + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(len(nuevos), 'libros en español actual')
