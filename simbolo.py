import string
import pandas as pd
import re
EPSILON = "ε"
VACIO = "∅"

def leer_alfabeto(texto):
    simbolos = [c for c in texto if not c.isspace()]
    alfabeto = []
    for i in simbolos:
        if i != ",":
            alfabeto.append(i)
    return alfabeto  

def crear_estados(n, modo):
    if modo == "Con q":
        return [f"q{i}" for i in range(n)]
    nombres = []
    for i in range(n):
        k, s = i, ""
        while True:
            s = string.ascii_uppercase[k % 26] + s
            k = k // 26 - 1
            if k < 0:
                break
        nombres.append(s)
    return nombres    

def crear_tabla_transiciones(simbolos, estados):
    tabla = pd.DataFrame(
        {
            "Inicial": [i==0 for i in range(len(estados))],
            "Final": False,
            "Estado": estados,
        }
    ) 
    for s in simbolos + [EPSILON]:
        tabla[s] = VACIO
    return tabla

def leer_tabla(tabla, simbolos):
    inicial = tabla.loc[tabla["Inicial"], "Estado"].tolist()
    inicial = inicial[0] if inicial else None

    finales = set(tabla.loc[tabla["Final"], "Estado"])
    estados_existentes = set(tabla["Estado"])
    transiciones = {}
    for _, fila in tabla.iterrows():
        for col in list(simbolos) + [EPSILON]:
            celda = str(fila[col] or "").strip()
            if celda in ("", VACIO, "None"):
                continue                     
            destinos = {d for d in re.split(r"[,\s]+", celda.strip()) if d}
            invalidos = destinos - estados_existentes
            if invalidos:
                raise ValueError(
                    f"Los estados {', '.join(sorted(invalidos))} "
                    f"no existen en la lista de estados."
                )
            clave = col   
            transiciones[(fila["Estado"], clave)] = destinos

    return inicial, finales, transiciones

def tabla_dfa(dfa):
    filas = []
    for estado in sorted(dfa.estados, key=lambda e: (e != dfa.estado_inicial, e)):
        fila = {
                "Inicial": "→" if estado == dfa.estado_inicial else "",
                "Final": "*" if estado in dfa.estados_finales else "",
                "Estado": estado,
        }
        for s in sorted(dfa.alfabeto):
            fila[s] = ", ".join(sorted(dfa.transiciones.get((estado, s), {"∅"})))
        filas.append(fila)
    
    return pd.DataFrame(filas)

