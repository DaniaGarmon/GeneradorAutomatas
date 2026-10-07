EPSILON = "ε"

class Automata:

    def __init__(
        self,
        estados,
        alfabeto,
        transiciones,
        estado_inicial,
        estados_finales
    ):
        self.estados = estados
        self.alfabeto = alfabeto
        self.transiciones = transiciones
        self.estado_inicial = estado_inicial
        self.estados_finales = estados_finales
        self.tipo_automata = None
        self.cerraduras = None 

    def transicion(self, estado, simbolo):
        return self.transiciones.get(
            (estado, simbolo),
            set()
        )
        
    def tiene_epsilon(self):
        return any(simbolo == EPSILON for (_, simbolo) in self.transiciones)
    
    def identificar_estados_mismo_tiempo(self):
        for (estado,simbolo), destinos in self.transiciones.items():
            if len(destinos) > 1:
                return True
            return False
    
    def tipo(self):
        if self.tiene_epsilon() or self.identificar_estados_mismo_tiempo():
            self.tipo_automata = "NFA"
        else:
            self.tipo_automata = "DFA"
        
        return self.tipo_automata

    def automata_a_dot(self):

        lineas = [
            "digraph {",
            '  rankdir=LR; bgcolor="transparent";',
            '  node [fontname="Inter", fontsize=14, style=filled, fillcolor="#F3F0FB", color="#7B5CE6", fontcolor="#1F1F1F", penwidth=1.6];',
            '  edge [fontname="Inter", fontsize=13, color="#7B5CE6", fontcolor="#1F1F1F"];',
            '  __inicio [shape=point, width=0.1, color="#1F1F1F"];',
        ]

        for e in sorted(self.estados):

            if e in self.estados_finales:
                lineas.append(
                    f'  "{e}" [shape=doublecircle, color="#F5B700", penwidth=2.5];'
                )
            else:
                lineas.append(
                    f'  "{e}" [shape=circle];'
                )

        lineas.append(
            f'  __inicio -> "{self.estado_inicial}";'
        )

        aristas = {}

        for (origen, simbolo), destinos in self.transiciones.items():

            for destino in destinos:
                aristas.setdefault(
                    (origen, destino),
                    []
                ).append(simbolo or "ε")

        for (origen, destino), simbolos in aristas.items():

            etiqueta = ", ".join(sorted(simbolos))

            lineas.append(
                f'  "{origen}" -> "{destino}" [label="{etiqueta}"];'
            )

        lineas.append("}")

        return "\n".join(lineas)
    
    def cerradura_epsilon(self,estados):
        if isinstance(estados,str):
            estados = {estados}
        cerradura = set(estados)
        pendientes = list(estados)
        while pendientes:
            estado = pendientes.pop()
            for destino in self.transiciones.get((estado,EPSILON),set()):
                if destino not in cerradura:
                    cerradura.add(destino)
                    pendientes.append(destino)
        return cerradura
    
    def calcular_cerraduras(self):
        self.cerraduras = {}
        for estado in self.estados:
            self.cerraduras[estado] = self.cerradura_epsilon(estado)
    
    def mover(self,estados,simbolo):
        resultado = set()
        for e in estados:
            resultado |= self.transiciones.get((e,simbolo), set())
        
        return resultado
    
    def convertir_nfa_dfa(self):
        def nombre(conjunto):
            return "{" + ", ".join(sorted(conjunto)) + "}" if conjunto else "∅"
        
        inicial = frozenset(
            self.cerradura_epsilon(self.estado_inicial)
        )
        por_visitar = [inicial]
        visitados = {inicial}
        transiciones = {}
        
        while por_visitar:
            actual = por_visitar.pop(0)
            for simbolo in sorted(self.alfabeto):
                destino = frozenset(
                    self.cerradura_epsilon(self.mover(actual,simbolo))
                )
                transiciones[(nombre(actual),simbolo)] = {nombre(destino)}
                
                if destino not in visitados:
                    visitados.add(destino)
                    por_visitar.append(destino)
                    
        dfa = Automata(
            estados={nombre(c) for c in visitados},
            alfabeto=set(self.alfabeto),
            transiciones=transiciones,
            estado_inicial=nombre(inicial),
            estados_finales={nombre(c) for c in visitados if c & self.estados_finales},
        )
        return dfa        
    
    @staticmethod
    def _tamano(nombre):
        """Cuántos estados del NFA contiene el nombre: '{A, B}' -> 2, '∅' -> 0."""
        if nombre == "∅":
            return 0
        if nombre.startswith("{") and nombre.endswith("}"):
            return len([x for x in nombre[1:-1].split(",") if x.strip()])
        return 1

    def fusionar_equivalentes(self):
        estados = set(self.estados)
        transiciones = {k: set(v) for k, v in self.transiciones.items()}
        finales = set(self.estados_finales)
        inicial = self.estado_inicial
        alfabeto = sorted(self.alfabeto)
        fusiones = [] 

        while True:
            def firma(e):
                return tuple(
                    next(iter(transiciones.get((e, s), set())), None) for s in alfabeto
                )
            grupos = {}
            for e in sorted(estados):
                grupos.setdefault((firma(e), e in finales), []).append(e)

            reemplazo = {}
            for grupo in grupos.values():
                if len(grupo) < 2:
                    continue
                if inicial in grupo:
                    representante = inicial
                else:
                    representante = min(grupo, key=lambda e: (self._tamano(e), e))
                for e in grupo:
                    if e != representante:
                        reemplazo[e] = representante
                fusiones.append((grupo, representante))

            if not reemplazo:
                break

            # Quita los estados repetidos y redirige las flechas hacia el que se queda
            estados -= set(reemplazo)
            finales -= set(reemplazo)
            transiciones = {
                (e, s): {reemplazo.get(d, d) for d in destinos}
                for (e, s), destinos in transiciones.items()
                if e in estados
            }

        minimo = Automata(estados, set(self.alfabeto), transiciones, inicial, finales)
        return minimo, fusiones
        
    def renombrar_estados(self, nuevos_nombres):
        ordenados = sorted(self.estados, key=lambda e: (e != self.estado_inicial, e))
        mapa = dict(zip(ordenados, nuevos_nombres))

        transiciones = {
            (mapa[origen], simbolo): {mapa[d] for d in destinos}
            for (origen, simbolo), destinos in self.transiciones.items()
        }

        renombrado = Automata(
            estados={mapa[e] for e in self.estados},
            alfabeto=set(self.alfabeto),
            transiciones=transiciones,
            estado_inicial=mapa[self.estado_inicial],
            estados_finales={mapa[e] for e in self.estados_finales},
        )
        return renombrado, mapa
    
    def equivalencia_0(self):
        no_finales = self.estados - self.estados_finales
        finales = set(self.estados_finales)

        particion = []

        if no_finales:
            particion.append(no_finales)

        if finales:
            particion.append(finales)

        return particion
    
    def buscar_conjunto(self, estado, particion):
        for i, conjunto in enumerate(particion):

            if estado in conjunto:
                return i

        return None
    
    def firma_estado(self, estado, particion):

        firma = []

        for simbolo in sorted(self.alfabeto):

            destinos = self.transicion(
                estado,
                simbolo
            )

            destino = next(iter(destinos), None)

            if destino is None:
                firma.append(None)
            else:
                grupo = self.buscar_conjunto(
                    destino,
                    particion
                )

                firma.append(grupo)

        return tuple(firma)
    
    def siguiente_particion(self, particion):
        nueva_particion = []

        for conjunto in particion:

            grupos = {}

            for estado in conjunto:

                firma = self.firma_estado(
                    estado,
                    particion
                )

                grupos.setdefault(
                    firma,
                    set()
                ).add(estado)

            nueva_particion.extend(
                grupos.values()
            )

        return nueva_particion
    
    @staticmethod
    def normalizar_particion(particion):
        return {
            frozenset(conjunto)
            for conjunto in particion
        }
    
    def obtener_particiones(self):
        paticiones = []
        anterior = self.equivalencia_0()
        paticiones.append(anterior)
        while True:

            actual = self.siguiente_particion(
                anterior
            )
            
            anterior_normalizada = self.normalizar_particion(
                anterior
            )
            
            actual_normalizada = self.normalizar_particion(
                actual
            )

            if actual_normalizada == anterior_normalizada:
                break
            
            paticiones.append(actual)
            anterior = actual
        return paticiones
    
    def construir_dfa_minimo(self, particion, visibles=None):
        def nombre_de(conjunto):
            miembros = set(conjunto)
            if visibles is not None:
                    miembros = (miembros & visibles) or miembros
            return "{" + ",".join(sorted(miembros)) + "}"

        mapa = {}
        for conjunto in particion:
            nombre = nombre_de(conjunto)
            for estado in conjunto:
                mapa[estado] = nombre

        estados_minimos = set(mapa.values())
        estado_inicial = mapa[self.estado_inicial]
        estados_finales = {mapa[e] for e in self.estados_finales}

        transiciones = {}
        for conjunto in particion:
            representante = next(iter(conjunto))
            estado_nuevo = mapa[representante]

            for simbolo in sorted(self.alfabeto):
                destinos = self.transicion(representante, simbolo)
                if destinos:
                    destino = next(iter(destinos))
                    transiciones[(estado_nuevo, simbolo)] = {mapa[destino]}

        return Automata(
            estados=estados_minimos,
            alfabeto=set(self.alfabeto),
            transiciones=transiciones,
            estado_inicial=estado_inicial,
            estados_finales=estados_finales,
        )
        
    def estados_alcanzables(self):
        alcanzables = {self.estado_inicial}
        pendientes = [self.estado_inicial]

        while pendientes:
            estado = pendientes.pop()
            for simbolo in self.alfabeto:
                for destino in self.transicion(estado, simbolo):
                    if destino not in alcanzables:
                        alcanzables.add(destino)
                        pendientes.append(destino)

        return alcanzables

    def eliminar_inalcanzables(self):

        alcanzables = self.estados_alcanzables()

        transiciones = {
            (origen, simbolo): set(destinos)
            for (origen, simbolo), destinos in self.transiciones.items()
            if origen in alcanzables
        }

        limpio = Automata(
            estados=set(alcanzables),
            alfabeto=set(self.alfabeto),
            transiciones=transiciones,
            estado_inicial=self.estado_inicial,
            estados_finales=set(self.estados_finales) & alcanzables,
        )
        return limpio, set(self.estados) - alcanzables
    
    def aplicar_mapa(self, mapa):
        transiciones = {
            (mapa[origen], simbolo): {mapa[d] for d in destinos}
            for (origen, simbolo), destinos in self.transiciones.items()
        }
        return Automata(
            estados={mapa[e] for e in self.estados},
            alfabeto=set(self.alfabeto),
            transiciones=transiciones,
            estado_inicial=mapa[self.estado_inicial],
            estados_finales={mapa[e] for e in self.estados_finales},
        )
    
    def ecuaciones_entrantes(self):
        orden = sorted(self.estados, key=lambda e: (e != self.estado_inicial, e))
        ecuaciones = {
            e: {"epsilon": e == self.estado_inicial, "terminos": []} for e in orden
        }

        for (origen, simbolo), destinos in self.transiciones.items():
            for destino in destinos:
                ecuaciones[destino]["terminos"].append((origen, simbolo))

        for eq in ecuaciones.values():
            eq["terminos"].sort()

        return ecuaciones

    @staticmethod
    def _romano(n):
        valores = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
                   (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
                   (5, "V"), (4, "IV"), (1, "I")]
        resultado = ""
        for valor, letras in valores:
            while n >= valor:
                resultado += letras
                n -= valor
        return resultado
    
    def formatear_ecuaciones(self, epsilon="ε"):
        lineas = []
        for i, (estado, eq) in enumerate(self.ecuaciones_entrantes().items(), start=1):
            partes = []
            if eq["epsilon"]:
                partes.append(epsilon)
            partes += [f"{origen}[{simbolo}]" for origen, simbolo in eq["terminos"]]

            derecho = " + ".join(partes) if partes else "∅"
            lineas.append(f"({self._romano(i)}) {estado} = {derecho}")

        return lineas