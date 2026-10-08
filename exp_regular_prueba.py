# Expresión regular de un autómata finito por eliminación de estados.
# Notación: unión "+", cerradura "*", cadena vacía "ε", lenguaje vacío None.

def _nivel(s, ch):
    p = 0
    for c in s:
        if c == "(":
            p += 1
        elif c == ")":
            p -= 1
        elif c == ch and p == 0:
            return True
    return False


def _atomo(s):
    if len(s) == 1:
        return True
    if s.endswith("*"):
        return _atomo(s[:-1])
    if s.startswith("(") and s.endswith(")"):
        p = 0
        for i, c in enumerate(s):
            p += c == "("
            p -= c == ")"
            if p == 0 and i < len(s) - 1:
                return False
        return True
    return False


def union(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a == b:
        return a
    partes = []
    for x in (a, b):
        for t in _separar(x):
            if t not in partes:
                partes.append(t)
    return "+".join(partes)


def _separar(s):
    partes, p, ini = [], 0, 0
    for i, c in enumerate(s):
        if c == "(":
            p += 1
        elif c == ")":
            p -= 1
        elif c == "+" and p == 0:
            partes.append(s[ini:i])
            ini = i + 1
    partes.append(s[ini:])
    return partes


def concat(a, b):
    if a is None or b is None:
        return None
    if a == "ε":
        return b
    if b == "ε":
        return a
    a = f"({a})" if _nivel(a, "+") else a
    b = f"({b})" if _nivel(b, "+") else b
    return a + b


def estrella(a):
    if a is None or a == "ε":
        return "ε"
    if _atomo(a):
        return a if a.endswith("*") else a + "*"
    # (R*)* = R*  y  (ε+R)* = R*
    partes = [t for t in _separar(a) if t != "ε"]
    a = "+".join(partes)
    if len(partes) == 1 and partes[0].endswith("*") and _atomo(partes[0]):
        return partes[0]
    return a + "*" if _atomo(a) else f"({a})*"


def automata_a_regex(automata):
    """Devuelve la ER del lenguaje del autómata (None si es vacío)."""
    INI, FIN = "__ini__", "__fin__"
    estados = sorted(automata.estados, key=lambda e: (e != automata.estado_inicial, e))

    # Matriz de aristas con etiquetas regex
    R = {}

    def poner(o, d, r):
        R[(o, d)] = union(R.get((o, d)), r)

    for (o, s), destinos in automata.transiciones.items():
        for d in destinos:
            poner(o, d, "ε" if s in ("", "ε") else s)
    poner(INI, automata.estado_inicial, "ε")
    for f in automata.estados_finales:
        poner(f, FIN, "ε")

    # Eliminar estados: en cada paso, el que deje las etiquetas más cortas
    def eliminar(R, q, vivos):
        R2 = dict(R)
        bucle = estrella(R2.get((q, q)))
        entran = [p for p in vivos if p != q and R2.get((p, q)) is not None]
        salen = [r for r in vivos if r != q and R2.get((q, r)) is not None]
        for p in entran:
            for r in salen:
                nuevo = concat(concat(R2[(p, q)], bucle), R2[(q, r)])
                R2[(p, r)] = union(R2.get((p, r)), nuevo)
        for k in [k for k in R2 if q in k]:
            del R2[k]
        return R2

    def costo(R):
        return sum(len(v) for v in R.values())

    pendientes = list(estados)
    vivos = [INI, FIN] + estados
    while pendientes:
        mejor = None
        for q in pendientes:
            R2 = eliminar(R, q, vivos)
            c = costo(R2)
            if mejor is None or c < mejor[0]:
                mejor = (c, q, R2)
        _, q, R = mejor
        pendientes.remove(q)
        vivos.remove(q)

    return R.get((INI, FIN))


# =====================================================================
#  SIMPLIFICACIÓN ALGEBRAICA (con verificación)
# =====================================================================
# AST: ("eps",) ("sym", x) ("cat", [..]) ("uni", [..]) ("star", r)

def _parsear(s):
    pos = 0

    def uni():
        nonlocal pos
        ts = [cat()]
        while pos < len(s) and s[pos] == "+":
            pos += 1
            ts.append(cat())
        return ts[0] if len(ts) == 1 else ("uni", ts)

    def cat():
        nonlocal pos
        fs = []
        while pos < len(s) and s[pos] not in "+)":
            fs.append(estr())
        if not fs:
            return ("eps",)
        return fs[0] if len(fs) == 1 else ("cat", fs)

    def estr():
        nonlocal pos
        if s[pos] == "(":
            pos += 1
            r = uni()
            pos += 1  # ")"
        elif s[pos] == "ε":
            pos += 1
            r = ("eps",)
        else:
            r = ("sym", s[pos])
            pos += 1
        while pos < len(s) and s[pos] == "*":
            pos += 1
            r = ("star", r)
        return r

    return uni()


def _texto(r, ctx=0):
    # ctx: 0 = unión, 1 = concatenación, 2 = bajo estrella
    t = r[0]
    if t == "eps":
        return "ε"
    if t == "sym":
        return r[1]
    if t == "star":
        return _texto(r[1], 2) + "*"
    if t == "cat":
        out = "".join(_texto(x, 1) for x in r[1])
        return f"({out})" if ctx == 2 else out
    out = "+".join(_texto(x, 0) for x in r[1])
    return f"({out})" if ctx >= 1 else out


def _nulo(r):
    t = r[0]
    if t in ("eps", "star"):
        return True
    if t == "sym":
        return False
    if t == "cat":
        return all(_nulo(x) for x in r[1])
    return any(_nulo(x) for x in r[1])


def _cat(fs):
    out = []
    for f in fs:
        if f[0] == "cat":
            out.extend(f[1])
        elif f[0] != "eps":
            out.append(f)
    # X* (ε + Y (X+Y)*)  ->  (X+Y)*
    i = 0
    while i < len(out) - 1:
        a, b = out[i], out[i + 1]
        if a[0] == "star" and b[0] == "uni" and len(b[1]) == 2 and ("eps",) in b[1]:
            otro = [t for t in b[1] if t != ("eps",)][0]
            fs = _lista_cat(otro)
            if len(fs) == 2 and fs[1][0] == "star":
                z = fs[1][1]
                zt = z[1] if z[0] == "uni" else [z]
                if len(zt) == 2 and all(x in zt for x in (a[1], fs[0])):
                    out[i:i + 2] = [fs[1]]
                    continue
        i += 1
    # X* X*  ->  X*
    res = []
    for f in out:
        if res and f[0] == "star" and res[-1] == f:
            continue
        res.append(f)
    if not res:
        return ("eps",)
    return res[0] if len(res) == 1 else ("cat", res)


def _lista_cat(r):
    return list(r[1]) if r[0] == "cat" else ([] if r[0] == "eps" else [r])


def _star(r):
    if r[0] == "eps":
        return r
    if r[0] == "star":
        return r
    if r[0] == "uni":
        ts = []
        for t in r[1]:
            if t[0] == "eps":
                continue
            if t[0] == "star":
                t = t[1]
            ts.append(t)
        r = _uni(ts)
        if r[0] == "eps":
            return r
    return ("star", r)


def _uni(ts):
    plano = []
    for t in ts:
        if t[0] == "uni":
            plano.extend(t[1])
        else:
            plano.append(t)
    uniq = []
    for t in plano:
        if t not in uniq:
            uniq.append(t)
    ts = uniq

    # ε + R  con R anulable  ->  R ;   ε + X X*  ->  X*
    if ("eps",) in ts:
        otros = [t for t in ts if t != ("eps",)]
        if any(_nulo(t) for t in otros):
            ts = otros
        else:
            for t in otros:
                fs = _lista_cat(t)
                if len(fs) == 2 and fs[1][0] == "star" and fs[1][1] == fs[0]:
                    ts = [("star", fs[0]) if x == t else x for x in otros]
                    break
                if len(fs) == 2 and fs[0][0] == "star" and fs[0][1] == fs[1]:
                    ts = [("star", fs[1]) if x == t else x for x in otros]
                    break
    # X* absorbe a X, ε y a todo X^k que sea término suyo
    for t in list(ts):
        if t[0] == "star":
            ts = [x for x in ts if x != t[1] and x != ("eps",) or x == t]
    # c + c b b*  ->  c b*   (R + R S S*)
    cambio = True
    while cambio:
        cambio = False
        for x in ts:
            for y in ts:
                if x is y:
                    continue
                fx, fy = _lista_cat(x), _lista_cat(y)
                if len(fy) >= len(fx) + 2 and fy[: len(fx)] == fx:
                    resto = fy[len(fx):]
                    if (len(resto) == 2 and resto[1][0] == "star"
                            and resto[1][1] == resto[0]):
                        nuevo = _cat(fx + [resto[1]])
                        ts = [z for z in ts if z is not x and z is not y] + [nuevo]
                        cambio = True
                        break
            if cambio:
                break
    # factor común por la izquierda / derecha (solo si acorta)
    ts = _factorizar(ts, izquierda=True)
    ts = _factorizar(ts, izquierda=False)
    if not ts:
        return ("eps",)
    return ts[0] if len(ts) == 1 else ("uni", ts)


def _factorizar(ts, izquierda):
    cambio = True
    while cambio:
        cambio = False
        grupos = {}
        for t in ts:
            fs = _lista_cat(t)
            if not fs:
                continue
            k = fs[0] if izquierda else fs[-1]
            grupos.setdefault(repr(k), []).append(t)
        for k, g in grupos.items():
            if len(g) < 2:
                continue
            fs0 = _lista_cat(g[0])
            f = fs0[0] if izquierda else fs0[-1]
            restos = []
            for t in g:
                fs = _lista_cat(t)
                restos.append(_cat(fs[1:] if izquierda else fs[:-1]))
            comp = _uni(restos)
            nuevo = _cat([f, comp]) if izquierda else _cat([comp, f])
            antes = sum(len(_texto(t)) for t in g) + len(g) - 1
            if len(_texto(nuevo)) <= antes + 2:
                ts = [t for t in ts if all(t is not x for x in g)] + [nuevo]
                cambio = True
                break
    return ts


def _simp(r):
    t = r[0]
    if t in ("eps", "sym"):
        return r
    if t == "star":
        return _star(_simp(r[1]))
    if t == "cat":
        c = _cat([_simp(x) for x in r[1]])
        if c[0] == "cat" and c[1][0][0] == "star" and c[1][1][0] == "uni":
            # X*(A+B)  ->  X*A + X*B   si así queda más corta
            ts = c[1][1][1]
            d = _uni([_cat([c[1][0], t] + []) for t in ts])
            d = _cat([d] + c[1][2:]) if c[1][2:] else d
            if d[0] == "uni" and c[1][2:]:
                d = _uni([_cat([t] + c[1][2:]) for t in d[1]])
            if len(_texto(d)) < len(_texto(c)):
                return d
        return c
    return _uni([_simp(x) for x in r[1]])


def simplificar_regex(regex):
    """Simplifica algebraicamente una ER (notación +, *, ε)."""
    if regex is None:
        return None
    r = _parsear(regex)
    for _ in range(20):
        n = _simp(r)
        if n == r:
            break
        r = n
    return _texto(r)


def _acepta_regex(patron, cadena):
    return patron.fullmatch(cadena) is not None


def equivalentes(r1, r2, alfabeto, largo=8):
    """Compara dos ERs probando todas las cadenas hasta `largo`."""
    import itertools, re

    def comp(r):
        return re.compile(r.replace("ε", "").replace("+", "|"))

    p1, p2 = comp(r1), comp(r2)
    for k in range(largo + 1):
        for t in itertools.product(sorted(alfabeto), repeat=k):
            s = "".join(t)
            if _acepta_regex(p1, s) != _acepta_regex(p2, s):
                return False
    return True


def mejor_regex(automata):
    """(ER obtenida, ER simplificada). La simplificada solo se usa si es
    equivalente (verificada) y no es más larga."""
    base = automata_a_regex(automata)
    if base is None:
        return None, None
    simp = simplificar_regex(base)
    if len(simp) > len(base) or not equivalentes(base, simp, automata.alfabeto, 7):
        simp = base
    return base, simp