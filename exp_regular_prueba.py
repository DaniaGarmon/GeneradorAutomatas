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