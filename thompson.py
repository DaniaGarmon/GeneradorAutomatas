from automata import Automata, EPSILON

# Agrupación: () [] {}   |   Unión: +  (también |)   |   Cerradura: *   |   Cadena vacía: ε
ABRE = {"(": ")", "[": "]", "{": "}"}
CIERRA = set(ABRE.values())
UNION = ("+", "|")


class _Thompson:
    """
    Recorre la ER según la precedencia (de menor a mayor):
        unión  <  concatenación  <  cerradura  <  símbolos y agrupación
    y arma un NFA por cada subexpresión. Un fragmento es (inicio, fin, estados).
    """

    def __init__(self, texto, extremos_en_concatenacion=True):
        self.texto = texto.replace(" ", "")
        self.extremos_en_concatenacion = extremos_en_concatenacion
        self.pos = 0
        self.contador = 0
        self.transiciones = {}
        self.alfabeto = set()
        self.pasos = []

    # ------------------------------------------------------------ utilidades
    def _actual(self):
        return self.texto[self.pos] if self.pos < len(self.texto) else None

    def _nuevo_estado(self):
        nombre = f"q{self.contador}"
        self.contador += 1
        return nombre

    def _agregar(self, origen, simbolo, destino):
        self.transiciones.setdefault((origen, simbolo), set()).add(destino)

    def _registrar(self, operacion, expresion, fragmento):
        """Guarda una copia del NFA de esta subexpresión para mostrar el proceso."""
        inicio, fin, estados = fragmento
        trans = {k: set(v) for k, v in self.transiciones.items() if k[0] in estados}
        alfabeto = {s for (_, s) in trans if s != EPSILON}
        self.pasos.append({
            "operacion": operacion,
            "expresion": expresion,
            "automata": Automata(set(estados), alfabeto, trans, inicio, {fin}),
        })

    # ------------------------------------------------------------ análisis
    def parsear(self):
        if not self.texto:
            raise ValueError("Escribe una expresión regular.")
        fragmento = self._expr()
        if self.pos < len(self.texto):
            raise ValueError(
                f"Símbolo inesperado '{self.texto[self.pos]}' en la posición {self.pos + 1}."
            )
        return fragmento

    def _expr(self):                      # unión: la de menor precedencia
        inicio_texto = self.pos
        fragmento = self._termino()
        while self._actual() in UNION:
            self.pos += 1
            derecho = self._termino()
            fragmento = self._union(fragmento, derecho)
            self._registrar("Unión", self.texto[inicio_texto:self.pos], fragmento)
        return fragmento

    def _termino(self):                   # concatenación
        inicio_texto = self.pos
        fragmento = self._factor()
        while self._actual() is not None and self._actual() not in UNION \
                and self._actual() not in CIERRA:
            siguiente = self._factor()
            fragmento = self._concatenar(fragmento, siguiente)
            self._registrar("Concatenación", self.texto[inicio_texto:self.pos], fragmento)
        return fragmento

    def _factor(self):                    # cerradura
        inicio_texto = self.pos
        fragmento = self._atomo()
        while self._actual() == "*":
            self.pos += 1
            fragmento = self._cerradura(fragmento)
            self._registrar("Cerradura", self.texto[inicio_texto:self.pos], fragmento)
        return fragmento

    def _atomo(self):                     # símbolo o agrupación
        c = self._actual()
        if c is None:
            raise ValueError("La expresión termina antes de tiempo: falta un operando.")
        if c in ABRE:
            cierre = ABRE[c]
            self.pos += 1
            fragmento = self._expr()
            if self._actual() != cierre:
                raise ValueError(f"Falta cerrar '{c}' con '{cierre}'.")
            self.pos += 1
            return fragmento              # agrupar no crea estados
        if c in CIERRA or c in UNION or c == "*":
            raise ValueError(f"Falta un operando antes de '{c}' (posición {self.pos + 1}).")
        self.pos += 1
        return self._simbolo(c)

    # ------------------------------------------------------------ patrones de Thompson
    def _simbolo(self, c):
        inicio, fin = self._nuevo_estado(), self._nuevo_estado()
        if c == EPSILON:
            self._agregar(inicio, EPSILON, fin)
        else:
            self._agregar(inicio, c, fin)
            self.alfabeto.add(c)
        fragmento = (inicio, fin, {inicio, fin})
        self._registrar("Símbolo", c, fragmento)
        return fragmento

    def _union(self, a, b):
        inicio, fin = self._nuevo_estado(), self._nuevo_estado()
        self._agregar(inicio, EPSILON, a[0])
        self._agregar(inicio, EPSILON, b[0])
        self._agregar(a[1], EPSILON, fin)
        self._agregar(b[1], EPSILON, fin)
        return (inicio, fin, a[2] | b[2] | {inicio, fin})

    def _concatenar(self, a, b):
        if not self.extremos_en_concatenacion:
            self._agregar(a[1], EPSILON, b[0])
            return (a[0], b[1], a[2] | b[2])

        inicio, fin = self._nuevo_estado(), self._nuevo_estado()
        self._agregar(inicio, EPSILON, a[0])
        self._agregar(a[1], EPSILON, b[0])
        self._agregar(b[1], EPSILON, fin)
        return (inicio, fin, a[2] | b[2] | {inicio, fin})

    def _cerradura(self, a):
        inicio, fin = self._nuevo_estado(), self._nuevo_estado()
        self._agregar(inicio, EPSILON, a[0])
        self._agregar(inicio, EPSILON, fin)
        self._agregar(a[1], EPSILON, a[0])
        self._agregar(a[1], EPSILON, fin)
        return (inicio, fin, a[2] | {inicio, fin})


def _numerar(inicio, transiciones):
    """q0 = estado inicial; el resto se numera en el orden en que se alcanza."""
    def numero(e):
        return int(e[1:])

    orden, vistos, i = [inicio], {inicio}, 0
    while i < len(orden):
        actual = orden[i]
        i += 1
        claves = sorted(
            (k for k in transiciones if k[0] == actual),
            key=lambda k: (k[1] == EPSILON, k[1]),
        )
        for clave in claves:
            for destino in sorted(transiciones[clave], key=numero):
                if destino not in vistos:
                    vistos.add(destino)
                    orden.append(destino)
    return {e: f"q{n}" for n, e in enumerate(orden)}


def er_a_nfa(regex, extremos_en_concatenacion=True):
    """
    Construye el NFA de una expresión regular con el método de Thompson.
    Devuelve (nfa, pasos): 'pasos' trae el NFA de cada subexpresión, en el orden en que se armó.
    """
    t = _Thompson(regex, extremos_en_concatenacion)
    inicio, fin, estados = t.parsear()

    mapa = _numerar(inicio, t.transiciones)

    nfa = Automata(
        estados=set(estados),
        alfabeto=set(t.alfabeto),
        transiciones=t.transiciones,
        estado_inicial=inicio,
        estados_finales={fin},
    ).aplicar_mapa(mapa)
    nfa.calcular_cerraduras()

    pasos = []
    for paso in t.pasos:
        sub = paso["automata"]
        pasos.append({
            "operacion": paso["operacion"],
            "expresion": paso["expresion"],
            "automata": sub.aplicar_mapa({e: mapa[e] for e in sub.estados}),
        })
    return nfa, pasos