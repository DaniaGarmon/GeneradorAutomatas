from pyformlang.finite_automaton import (
    DeterministicFiniteAutomaton,
    State,
    Symbol
)


def automata_a_dfa(automata):
    """
    Convierte un objeto Automata propio a un DFA de Pyformlang.
    """

    dfa = DeterministicFiniteAutomaton()

    # --------------------------------------------------------
    # Agregar transiciones
    # --------------------------------------------------------

    for (estado_origen, simbolo), destinos in automata.transiciones.items():

        for estado_destino in destinos:

            dfa.add_transition(
                State(str(estado_origen)),
                Symbol(str(simbolo)),
                State(str(estado_destino))
            )

    # --------------------------------------------------------
    # Estado inicial
    # --------------------------------------------------------

    dfa.add_start_state(
        State(str(automata.estado_inicial))
    )

    # --------------------------------------------------------
    # Estados finales
    # --------------------------------------------------------

    for estado_final in automata.estados_finales:

        dfa.add_final_state(
            State(str(estado_final))
        )

    return dfa


# ============================================================
# DFA → EXPRESIÓN REGULAR
# ============================================================

def automata_a_regex(automata):
    """
    Convierte el autómata a un DFA de Pyformlang
    y posteriormente obtiene su expresión regular.
    """

    dfa = automata_a_dfa(automata)

    regex = dfa.to_regex()

    return regex


# ============================================================
# ÁRBOL DE EXPRESIÓN REGULAR
# ============================================================

class NodoRegex:

    def __init__(
        self,
        tipo,
        valor=None,
        izquierda=None,
        derecha=None
    ):

        self.tipo = tipo
        self.valor = valor
        self.izquierda = izquierda
        self.derecha = derecha


# Tipos utilizados:
#
# SIMBOLO
# EPSILON
# VACIO
# UNION
# CONCAT
# KLEENE


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def es_epsilon(nodo):

    return nodo is not None and nodo.tipo == "EPSILON"


def es_vacio(nodo):

    return nodo is not None and nodo.tipo == "VACIO"


def es_kleene(nodo):

    return nodo is not None and nodo.tipo == "KLEENE"


def iguales(a, b):
    """
    Compara dos árboles de expresión regular
    estructuralmente.
    """

    if a is None or b is None:

        return a is b

    if a.tipo != b.tipo:

        return False

    if a.tipo == "SIMBOLO":

        return a.valor == b.valor

    if a.tipo in ("EPSILON", "VACIO"):

        return True

    return (
        iguales(a.izquierda, b.izquierda)
        and
        iguales(a.derecha, b.derecha)
    )


# ============================================================
# TOKENIZADOR
# ============================================================

def tokenizar_regex(texto):
    """
    Convierte una expresión regular de Pyformlang
    en una lista de tokens.

    Ejemplo:

        ((0)*.(1.(1)*))|(0)*

    se convierte en:

        ['(', '(', '0', ')', '*', '.', ...]
    """

    texto = texto.replace(" ", "")

    tokens = []

    i = 0

    while i < len(texto):

        caracter = texto[i]

        # Operadores
        if caracter in "()|.*":

            tokens.append(caracter)

        # Símbolos especiales
        elif caracter == "ε":

            tokens.append("ε")

        elif caracter == "∅":

            tokens.append("∅")

        # Cualquier símbolo del alfabeto
        else:

            tokens.append(caracter)

        i += 1

    return tokens


# ============================================================
# PARSER
# ============================================================

class ParserRegex:

    def __init__(self, tokens):

        self.tokens = tokens
        self.pos = 0

    # --------------------------------------------------------
    # Token actual
    # --------------------------------------------------------

    def actual(self):

        if self.pos < len(self.tokens):

            return self.tokens[self.pos]

        return None

    # --------------------------------------------------------
    # Avanzar
    # --------------------------------------------------------

    def avanzar(self):

        token = self.actual()

        self.pos += 1

        return token

    # --------------------------------------------------------
    # Expresión
    #
    # expresión := concatenación ( "|" concatenación )*
    # --------------------------------------------------------

    def expresion(self):

        nodo = self.concatenacion()

        while self.actual() == "|":

            self.avanzar()

            derecha = self.concatenacion()

            nodo = NodoRegex(
                "UNION",
                izquierda=nodo,
                derecha=derecha
            )

        return nodo

    # --------------------------------------------------------
    # Concatenación
    #
    # concatenación := kleene ( "." kleene )*
    # --------------------------------------------------------

    def concatenacion(self):

        nodo = self.kleene()

        while self.actual() == ".":

            self.avanzar()

            derecha = self.kleene()

            nodo = NodoRegex(
                "CONCAT",
                izquierda=nodo,
                derecha=derecha
            )

        return nodo

    # --------------------------------------------------------
    # Kleene
    #
    # kleene := primario "*"
    # --------------------------------------------------------

    def kleene(self):

        nodo = self.primario()

        while self.actual() == "*":

            self.avanzar()

            nodo = NodoRegex(
                "KLEENE",
                izquierda=nodo
            )

        return nodo

    # --------------------------------------------------------
    # Primario
    # --------------------------------------------------------

    def primario(self):

        token = self.actual()

        # Expresión vacía
        if token is None:

            return NodoRegex("EPSILON")

        # Paréntesis
        if token == "(":

            self.avanzar()

            nodo = self.expresion()

            if self.actual() == ")":

                self.avanzar()

            return nodo

        self.avanzar()

        # Epsilon
        if token == "ε":

            return NodoRegex("EPSILON")

        # Conjunto vacío
        if token == "∅":

            return NodoRegex("VACIO")

        # Símbolo
        return NodoRegex(
            "SIMBOLO",
            valor=token
        )


# ============================================================
# CLAVE ESTRUCTURAL
# ============================================================

def clave_nodo(nodo):
    """
    Genera una representación comparable del árbol.

    Se utiliza para detectar si dos expresiones
    son estructuralmente iguales.
    """

    if nodo is None:

        return None

    if nodo.tipo == "SIMBOLO":

        return (
            "SIMBOLO",
            nodo.valor
        )

    if nodo.tipo in ("EPSILON", "VACIO"):

        return (nodo.tipo,)

    return (
        nodo.tipo,
        clave_nodo(nodo.izquierda),
        clave_nodo(nodo.derecha)
    )


# ============================================================
# REGLAS AUXILIARES
# ============================================================

def es_rr_estrellita(nodo):
    """
    Detecta:

        R R*

    Por ejemplo:

        1 1*

    """

    if nodo is None:
        return False

    if nodo.tipo != "CONCAT":
        return False

    izquierda = nodo.izquierda
    derecha = nodo.derecha

    if not es_kleene(derecha):
        return False

    return iguales(
        izquierda,
        derecha.izquierda
    )


def obtener_rr_estrellita(nodo):
    """
    Si el nodo representa:

        R R*

    devuelve R.

    En otro caso devuelve None.
    """

    if not es_rr_estrellita(nodo):

        return None

    return nodo.izquierda


# ============================================================
# SIMPLIFICACIÓN
# ============================================================

def simplificar_una_vez(nodo):

    if nodo is None:
        return nodo

    # --------------------------------------------------------
    # Simplificar hijos
    # --------------------------------------------------------

    if nodo.izquierda is not None:
        nodo.izquierda = simplificar_una_vez(nodo.izquierda)

    if nodo.derecha is not None:
        nodo.derecha = simplificar_una_vez(nodo.derecha)

    # ========================================================
    # KLEENE
    # ========================================================

    if nodo.tipo == "KLEENE":

        hijo = nodo.izquierda

        # (R*)* = R*
        if es_kleene(hijo):
            return hijo

        # ∅* = ε
        if es_vacio(hijo):
            return NodoRegex("EPSILON")

        # ε* = ε
        if es_epsilon(hijo):
            return NodoRegex("EPSILON")

        return nodo

    # ========================================================
    # CONCATENACIÓN
    # ========================================================

    if nodo.tipo == "CONCAT":

        izquierda = nodo.izquierda
        derecha = nodo.derecha

        # ∅R = ∅
        if es_vacio(izquierda):
            return NodoRegex("VACIO")

        # R∅ = ∅
        if es_vacio(derecha):
            return NodoRegex("VACIO")

        # εR = R
        if es_epsilon(izquierda):
            return derecha

        # Rε = R
        if es_epsilon(derecha):
            return izquierda

        return nodo

    # ========================================================
    # UNIÓN
    # ========================================================

    if nodo.tipo == "UNION":

        izquierda = nodo.izquierda
        derecha = nodo.derecha

        # ----------------------------------------------------
        # R + R = R
        # ----------------------------------------------------

        if iguales(izquierda, derecha):
            return izquierda

        # ----------------------------------------------------
        # ∅ + R = R
        # ----------------------------------------------------

        if es_vacio(izquierda):
            return derecha

        # ----------------------------------------------------
        # R + ∅ = R
        # ----------------------------------------------------

        if es_vacio(derecha):
            return izquierda

        # ----------------------------------------------------
        # ε + RR* = R*
        # ----------------------------------------------------

        if es_epsilon(izquierda):

            if (
                derecha.tipo == "CONCAT"
                and
                derecha.derecha is not None
                and
                es_kleene(derecha.derecha)
                and
                iguales(
                    derecha.izquierda,
                    derecha.derecha.izquierda
                )
            ):

                return NodoRegex(
                    "KLEENE",
                    izquierda=derecha.izquierda
                )

        # ----------------------------------------------------
        # RR* + ε = R*
        # ----------------------------------------------------

        if es_epsilon(derecha):

            if (
                izquierda.tipo == "CONCAT"
                and
                izquierda.derecha is not None
                and
                es_kleene(izquierda.derecha)
                and
                iguales(
                    izquierda.izquierda,
                    izquierda.derecha.izquierda
                )
            ):

                return NodoRegex(
                    "KLEENE",
                    izquierda=izquierda.izquierda
                )

        # ====================================================
        # FACTORIZACIÓN POR LA IZQUIERDA
        #
        # R + RS = R(ε + S)
        # ====================================================

        if derecha.tipo == "CONCAT":

            if iguales(
                izquierda,
                derecha.izquierda
            ):

                r = izquierda
                s = derecha.derecha

                interno = NodoRegex(
                    "UNION",
                    izquierda=NodoRegex("EPSILON"),
                    derecha=s
                )

                # Simplificamos ε + S
                interno = simplificar_una_vez(interno)

                resultado = NodoRegex(
                    "CONCAT",
                    izquierda=r,
                    derecha=interno
                )

                return simplificar_una_vez(resultado)

        # ====================================================
        # FACTORIZACIÓN
        #
        # RS + R = R(ε + S)
        # ====================================================

        if izquierda.tipo == "CONCAT":

            if iguales(
                izquierda.izquierda,
                derecha
            ):

                r = derecha
                s = izquierda.derecha

                interno = NodoRegex(
                    "UNION",
                    izquierda=NodoRegex("EPSILON"),
                    derecha=s
                )

                interno = simplificar_una_vez(interno)

                resultado = NodoRegex(
                    "CONCAT",
                    izquierda=r,
                    derecha=interno
                )

                return simplificar_una_vez(resultado)

        # ====================================================
        # FACTORIZACIÓN POR LA DERECHA
        #
        # R + SR = (ε + S)R
        # ====================================================

        if derecha.tipo == "CONCAT":

            if iguales(
                izquierda,
                derecha.derecha
            ):

                r = izquierda
                s = derecha.izquierda

                interno = NodoRegex(
                    "UNION",
                    izquierda=NodoRegex("EPSILON"),
                    derecha=s
                )

                interno = simplificar_una_vez(interno)

                resultado = NodoRegex(
                    "CONCAT",
                    izquierda=interno,
                    derecha=r
                )

                return simplificar_una_vez(resultado)

        # ====================================================
        # SR + R = (ε + S)R
        # ====================================================

        if izquierda.tipo == "CONCAT":

            if iguales(
                izquierda.derecha,
                derecha
            ):

                r = derecha
                s = izquierda.izquierda

                interno = NodoRegex(
                    "UNION",
                    izquierda=NodoRegex("EPSILON"),
                    derecha=s
                )

                interno = simplificar_una_vez(interno)

                resultado = NodoRegex(
                    "CONCAT",
                    izquierda=interno,
                    derecha=r
                )

                return simplificar_una_vez(resultado)

        return nodo

    return nodo


# ============================================================
# SIMPLIFICADOR COMPLETO
# ============================================================

def simplificar(nodo):

    if nodo is None:
        return nodo

    anterior = None
    actual = nodo

    for _ in range(100):

        actual = simplificar_una_vez(actual)

        actual_clave = clave_nodo(actual)

        if actual_clave == anterior:
            break

        anterior = actual_clave

    return actual

# ============================================================
# FORMATEAR ÁRBOL COMO TEXTO
# ============================================================

def precedencia(nodo):

    if nodo is None:
        return 0

    if nodo.tipo == "UNION":
        return 1

    if nodo.tipo == "CONCAT":
        return 2

    if nodo.tipo == "KLEENE":
        return 3

    return 4


# ============================================================
# EXPRESIÓN REGULAR → TEXTO
# ============================================================

def regex_a_texto(nodo):

    if nodo is None:
        return ""

    # --------------------------------------------------------
    # Símbolo
    # --------------------------------------------------------

    if nodo.tipo == "SIMBOLO":
        return str(nodo.valor)

    # --------------------------------------------------------
    # Epsilon
    # --------------------------------------------------------

    if nodo.tipo == "EPSILON":
        return "ε"

    # --------------------------------------------------------
    # Conjunto vacío
    # --------------------------------------------------------

    if nodo.tipo == "VACIO":
        return "∅"

    # --------------------------------------------------------
    # Kleene
    # --------------------------------------------------------

    if nodo.tipo == "KLEENE":

        hijo = nodo.izquierda

        texto_hijo = regex_a_texto(hijo)

        if hijo.tipo in ("UNION", "CONCAT"):
            texto_hijo = "(" + texto_hijo + ")"

        return texto_hijo + "*"

    # --------------------------------------------------------
    # Concatenación
    # --------------------------------------------------------

    if nodo.tipo == "CONCAT":

        izquierda = regex_a_texto(
            nodo.izquierda
        )

        derecha = regex_a_texto(
            nodo.derecha
        )

        return izquierda + derecha

    # --------------------------------------------------------
    # Unión
    # --------------------------------------------------------

    if nodo.tipo == "UNION":

        izquierda = regex_a_texto(
            nodo.izquierda
        )

        derecha = regex_a_texto(
            nodo.derecha
        )

        return izquierda + " + " + derecha

    # --------------------------------------------------------
    # Si aparece un tipo desconocido
    # --------------------------------------------------------

    raise ValueError(
        f"Tipo de nodo desconocido: {nodo.tipo}"
    )

# ============================================================
# FUNCIÓN PÚBLICA DE SIMPLIFICACIÓN
# ============================================================

# ============================================================
# FUNCIÓN PÚBLICA
# ============================================================

def simplificar_regex(regex):

    texto = str(regex)

    print("REGEX ORIGINAL:")
    print(texto)

    tokens = tokenizar_regex(texto)

    print("TOKENS:")
    print(tokens)

    parser = ParserRegex(tokens)

    arbol = parser.expresion()

    print("TIPO DE RAÍZ:")
    print(arbol.tipo)

    arbol_simplificado = simplificar(arbol)

    print("TIPO FINAL:")
    print(arbol_simplificado.tipo)

    resultado = regex_a_texto(
        arbol_simplificado
    )

    print("RESULTADO:")
    print(resultado)

    return resultado