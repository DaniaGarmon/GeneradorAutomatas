import streamlit as st
import simbolo
import automata
import re
import pandas as pd
import exp_regular
import thompson
import exp_regular_prueba

EPSILON = "ε"
VACIO = "∅"

st.set_page_config(page_title="Generador de autómatas", page_icon="🟣", layout="wide")

# ---------------------------------------------------------------- estilos
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, .stApp * { font-family: 'Inter', sans-serif; }
.stApp { background: #FFFFFF; }
.block-container { max-width: 1100px; padding-top: 2rem; }
header[data-testid="stHeader"] { background: transparent; }

/* tarjetas (contenedores con key que empieza con in_) */

.topbar { display: flex; gap: 8px; margin-bottom: 28px; flex-wrap: wrap; }
.pill { padding: 10px 20px; border-radius: 999px; font-weight: 500; font-size: 14px; color: #1F1F1F; }
.pill-dark { background: #1F1F1F; color: #FFFFFF; }
.titulo { font-size: 40px; font-weight: 600; color: #1F1F1F; margin: 0; line-height: 1.1; }
.sub { color: #8A8799; font-size: 14px; margin: 6px 0 24px 0; }

.card-title { font-size: 16px; font-weight: 500; color: #1F1F1F; margin-bottom: 8px; }
.hint { color: #8A8799; font-size: 13px; margin-top: 4px; }

/* inputs redondeados */
.stTextInput div[data-baseweb="input"],
.stNumberInput div[data-baseweb="input"] {
    background: #FFFFFF; border: none; border-radius: 999px;
}
.stTextInput input, .stNumberInput input { background: transparent; padding-left: 18px; color: #1F1F1F; }

/* botón oscuro tipo píldora */
.stButton > button {
    background: #1F1F1F; border: none; border-radius: 999px;
    padding: 0.6rem 1.8rem; font-weight: 600;
}
.stButton > button p { color: #FFFFFF; }
.stButton > button:hover { background: #7B5CE6; }
.stButton > button:focus-visible { outline: 2px solid #7B5CE6; outline-offset: 2px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 class="titulo">Generador de autómatas</h1>',
    unsafe_allow_html=True,
)

tab_tabla, tab_er = st.tabs(["Por tabla de transición", "Por ER"])

with tab_tabla:
    c1, c2, c3 = st.columns([1.3, 1, 1.2], gap="medium")

    with c1:
        with st.container(key="in_alfabeto"):
            st.markdown('<div class="card-title">Alfabeto</div>', unsafe_allow_html=True)
            texto_alfabeto = st.text_input(
                "Alfabeto",
                placeholder="Ej: 0 1  o  a, b, c",
                label_visibility="collapsed",
            )

    with c2:
        with st.container(key="in_estados"):
            st.markdown('<div class="card-title">Cantidad de estados</div>', unsafe_allow_html=True)
            cantidad = st.number_input(
                "Cantidad de estados",
                min_value=1,
                max_value=50,
                value=3,
                step=1,
                label_visibility="collapsed",
            )

    with c3:
        with st.container(key="in_nombres"):
            st.markdown('<div class="card-title">Nombre de los estados</div>', unsafe_allow_html=True)
            modo = st.segmented_control(
                "Nombre de los estados",
                options=["Con q", "Con letras"],
                default="Con q",
                label_visibility="collapsed",
            ) or "Con q"

    st.write("")


    alfabeto = simbolo.leer_alfabeto(texto_alfabeto)
    estados = simbolo.crear_estados(cantidad,modo)

    if st.button("Continuar", disabled=not alfabeto):
        config = (tuple(alfabeto), tuple(estados))
        if st.session_state.get("config") != config:
            st.session_state["config"] = config
            st.session_state["tabla_base"] = simbolo.crear_tabla_transiciones(alfabeto, estados)
            st.session_state["tabla_v"] = st.session_state.get("tabla_v", 0) + 1
            st.session_state["inicial_prev"] = estados[0]
        st.rerun()
        
    if "config" in st.session_state:
        simbolos_t, _ = st.session_state["config"]
        columnas_destino = list(simbolos_t) + [EPSILON]
    
        st.write("")
        with st.container(key="in_tabla"):
            st.markdown('<div class="card-title">Tabla de transiciones</div>', unsafe_allow_html=True)
    
            config_cols = {
                "Inicial": st.column_config.CheckboxColumn(
                    "Inicial", width="small", help="Solo un estado puede ser inicial"
                ),
                "Final": st.column_config.CheckboxColumn("Final", width="small"),
                "Estado": st.column_config.TextColumn("Estado", width="small"),
            }
            for c in columnas_destino:
                config_cols[c] = st.column_config.TextColumn(
                    c,
                    default=VACIO,
                    help=f"Estados destino separados por comas. {VACIO} = sin transición",
                )
    
            tabla = st.data_editor(
                st.session_state["tabla_base"],
                key=f"editor_{st.session_state['tabla_v']}",
                column_config=config_cols,
                disabled=["Estado"],
                hide_index=True,
            )
    
            marcados = tabla.loc[tabla["Inicial"], "Estado"].tolist()
            if len(marcados) > 1:
                previo = st.session_state.get("inicial_prev")
                nuevo = next((m for m in marcados if m != previo), marcados[-1])
                corregida = tabla.copy()
                corregida["Inicial"] = corregida["Estado"] == nuevo
                st.session_state["tabla_base"] = corregida
                st.session_state["tabla_v"] += 1 
                st.session_state["inicial_prev"] = nuevo
                st.rerun()
            st.session_state["inicial_prev"] = marcados[0] if marcados else None
            
            if st.button("Construir autómata", key="btn_construir"):
                try:
                    inicial, finales, transiciones = simbolo.leer_tabla(tabla, simbolos_t)

                    if inicial is None:
                        st.error("Elige un estado inicial.")
                    else:
                        for clave in ("dfa", "dfa_min", "dfa_limpio", "fusiones", "eliminados"):
                            st.session_state.pop(clave, None)

                        st.session_state["automata"] = automata.Automata(
                            estados=set(tabla["Estado"]),
                            alfabeto=set(simbolos_t),
                            transiciones=transiciones,
                            estado_inicial=inicial,
                            estados_finales=finales,
                        )

                        if st.session_state["automata"].tipo() == "NFA":
                            st.session_state["automata"].calcular_cerraduras()

                except ValueError as e:
                    st.error(str(e))

            if "automata" in st.session_state:
                automata_actual = st.session_state["automata"]
                
                st.write("")
                with st.container(key="in_grafo"):
                    st.markdown('<div class="card-title">Autómata</div>', unsafe_allow_html=True)
                    st.graphviz_chart(automata_actual.automata_a_dot())

                st.write("Tipo detectado:", automata_actual.tipo())

                if automata_actual.tipo() == "NFA":

                    if automata_actual.cerraduras:
                        st.subheader("Cerraduras ε")
                        filas_cerr = [
                            {
                                "Estado": estado,
                                "ε-cerradura": "{" + ", ".join(sorted(cerradura)) + "}",
                            }
                            for estado, cerradura in sorted(automata_actual.cerraduras.items())
                        ]
                        st.dataframe(pd.DataFrame(filas_cerr), hide_index=True)

                    if st.button("Convertir a DFA", key="btn_dfa"):
                        st.session_state["dfa"] = automata_actual.convertir_nfa_dfa()

                    if "dfa" in st.session_state:
                        dfa = st.session_state["dfa"]

                        st.subheader("DFA equivalente")
                        st.dataframe(simbolo.tabla_dfa(dfa), hide_index=True)
                        st.graphviz_chart(dfa.automata_a_dot())

                # ---------------- Base para minimizar ----------------
                if automata_actual.tipo() == "DFA":
                    base_dfa = automata_actual
                else:
                    base_dfa = st.session_state.get("dfa")

                if base_dfa is not None:

                    if st.button("Minimizar DFA", key="btn_dfa_min"):
                        dfa_limpio, eliminados = base_dfa.eliminar_inalcanzables()
                        st.session_state["dfa_limpio"] = dfa_limpio
                        st.session_state["eliminados"] = eliminados

                    if "dfa_limpio" in st.session_state:

                        dfa_limpio = st.session_state["dfa_limpio"]

                        st.subheader("DFA para minimizar")

                        renombrar = st.toggle(
                            "Renombrar estados",
                            key="renombrar_min"
                        )

                        

                        if renombrar:

                            modo_renombrado = st.radio(
                                "¿Cómo renombrar los estados?",
                                ["Con q", "Con letras"],
                                horizontal=True,
                                key="modo_renombrado"
                            )

                            nombres_nuevos = simbolo.crear_estados(
                                len(dfa_limpio.estados),
                                modo_renombrado
                            )

                            dfa_mostrar, mapa = dfa_limpio.renombrar_estados(
                                nombres_nuevos
                            )
                            
                            with st.expander("Ver equivalencias de nombres"):
                                
                                equivalencias = pd.DataFrame(
                                    {
                                        "Estado original": list(mapa.keys()),
                                        "Estado renombrado": list(mapa.values())
                                    }
                                )

                                st.dataframe(
                                    equivalencias,
                                    hide_index=True,
                                    width="stretch"
                                )


                        else:

                            dfa_mostrar = dfa_limpio
                            
                        st.dataframe(
                            simbolo.tabla_dfa(dfa_mostrar),
                            hide_index=True
                        )

                        st.graphviz_chart(
                            dfa_mostrar.automata_a_dot()
                        )

                            
                        st.subheader("Proceso de minimización")

                        particiones = dfa_mostrar.obtener_particiones()

                        for numero, particion in enumerate(particiones):

                            grupos = []

                            for conjunto in particion:

                                estados = ",".join(sorted(conjunto))

                                grupos.append(
                                    "{" + estados + "}"
                                )

                            particion_texto = (
                                "{" + ",".join(grupos) + "}"
                            )

                            st.markdown(
                                f"### {numero}-equivalencias = `{particion_texto}`"
                            )
                        
                        ultima_particion = particiones[-1]

                        
                        
                        dfa_minimo = dfa_mostrar.construir_dfa_minimo(
                            ultima_particion
                        )

                        st.subheader("DFA mínimo")
                        renombrar_minimo = st.toggle(
                            "Renombrar estados", key="renombrar_minimo"
                        )
                        dfa_minimo_mostrar = dfa_minimo
                        if renombrar_minimo:
                            modo_minimo = st.radio(
                                "¿Cómo renombrar los estados?",
                                ["Con q", "Con letras"],
                                horizontal=True,
                                key="modo_renombrado_minimo",
                            )
                            nombres_minimo = simbolo.crear_estados(
                                len(dfa_minimo.estados), modo_minimo
                            )
                            dfa_minimo_mostrar, mapa_minimo = dfa_minimo.renombrar_estados(
                                nombres_minimo
                            )
                            with st.expander("Equivalencias de nombres"):
                                st.dataframe(
                                    pd.DataFrame(
                                        {
                                            "Antes": list(mapa_minimo.keys()),
                                            "Después": list(mapa_minimo.values()),
                                        }
                                    ),
                                    hide_index=True,
                                )

                        st.dataframe(
                            simbolo.tabla_dfa(dfa_minimo_mostrar),
                            hide_index=True
                        )

                        st.graphviz_chart(
                            dfa_minimo_mostrar.automata_a_dot()
                        )
                        
                        st.subheader("Ecuaciones de transiciones entrantes")
                        st.code("\n".join(dfa_minimo_mostrar.formatear_ecuaciones()), language=None)
                        
                        
                  
                        
                        st.subheader("Expresión regular")

                        expresion = exp_regular_prueba.automata_a_regex(
                            dfa_minimo_mostrar
                        )

                        
                        
                        st.code(str(expresion))

with tab_er:
    with st.container(key="in_er"):
        st.markdown('<div class="card-title">Expresión regular</div>', unsafe_allow_html=True)
        texto_er = st.text_input(
            "Expresión regular",
            placeholder="Ej: (0+1)*1",
            label_visibility="collapsed",
            key="texto_er",
        )
        st.markdown(
            '<div class="hint">Usa + para la unión y * para la estrella.</div>',
            unsafe_allow_html=True,
        )

    st.write("")
    if st.button("Generar autómata", key="btn_er", disabled=not texto_er):
        for clave in ("nfa_er", "pasos_er","dfa_er","dfa_limpio_er","eliminados_er"):
            st.session_state.pop(clave, None)
        try:
            st.session_state["nfa_er"], st.session_state["pasos_er"] = thompson.er_a_nfa(
                texto_er, extremos_en_concatenacion=False
            )
        except ValueError as e:
            st.error(str(e))

    if "nfa_er" in st.session_state:
        st.subheader("NFA (método de Thompson)")
        st.graphviz_chart(st.session_state["nfa_er"].automata_a_dot())

        with st.expander("Ver construcción paso a paso"):
            for i, paso in enumerate(st.session_state["pasos_er"], start=1):
                st.markdown(f"**{i}. {paso['operacion']}:** `{paso['expresion']}`")
                st.graphviz_chart(paso["automata"].automata_a_dot())
        
        nfa_er = st.session_state["nfa_er"]
        # ---------------- NFA -> DFA ----------------
        if nfa_er.tipo() == "NFA":

            if st.button("Convertir a DFA", key="btn_dfa_er"):
                st.session_state["dfa_er"] = nfa_er.convertir_nfa_dfa()

            # fuera del botón: si no, desaparece con la siguiente interacción
            if "dfa_er" in st.session_state:
                dfa_er = st.session_state["dfa_er"]

                st.subheader("DFA equivalente")
                st.dataframe(simbolo.tabla_dfa(dfa_er), hide_index=True)
                st.graphviz_chart(dfa_er.automata_a_dot())
        
        if nfa_er.tipo() == "DFA":
            base_dfa = nfa_er
        else:
            base_dfa = st.session_state.get("dfa_er")

        if base_dfa is not None:

            if st.button("Minimizar DFA", key="btn_dfa_min_er"):
                dfa_limpio, eliminados = base_dfa.eliminar_inalcanzables()
                st.session_state["dfa_limpio_er"] = dfa_limpio
                st.session_state["eliminados_er"] = eliminados

            if "dfa_limpio_er" in st.session_state:

                dfa_limpio = st.session_state["dfa_limpio_er"]

                st.subheader("DFA para minimizar")

                renombrar = st.toggle("Renombrar estados", key="renombrar_min_er")

                if renombrar:
                    modo_renombrado = st.radio(
                        "¿Cómo renombrar los estados?",
                        ["Con q", "Con letras"],
                        horizontal=True,
                        key="modo_renombrado_er",
                    )

                    nombres_nuevos = simbolo.crear_estados(
                        len(dfa_limpio.estados), modo_renombrado
                    )

                    dfa_mostrar, mapa = dfa_limpio.renombrar_estados(nombres_nuevos)

                    with st.expander("Ver equivalencias de nombres"):
                        equivalencias = pd.DataFrame(
                            {
                                "Estado original": list(mapa.keys()),
                                "Estado renombrado": list(mapa.values()),
                            }
                        )
                        st.dataframe(equivalencias, hide_index=True, width="stretch")

                else:
                    dfa_mostrar = dfa_limpio

                st.dataframe(simbolo.tabla_dfa(dfa_mostrar), hide_index=True)
                st.graphviz_chart(dfa_mostrar.automata_a_dot())

                # ---------------- Proceso de minimización ----------------
                st.subheader("Proceso de minimización")

                particiones = dfa_mostrar.obtener_particiones()

                for numero, particion in enumerate(particiones):
                    grupos = []
                    for conjunto in particion:
                        grupos.append("{" + ",".join(sorted(conjunto)) + "}")
                    particion_texto = "{" + ",".join(grupos) + "}"

                    st.markdown(f"### {numero}-equivalencias = `{particion_texto}`")

                dfa_minimo = dfa_mostrar.construir_dfa_minimo(particiones[-1])

                # ---------------- DFA mínimo ----------------
                st.subheader("DFA mínimo")

                renombrar_minimo = st.toggle(
                    "Renombrar estados", key="renombrar_minimo_er"
                )

                dfa_minimo_mostrar = dfa_minimo

                if renombrar_minimo:
                    modo_minimo = st.radio(
                        "¿Cómo renombrar los estados?",
                        ["Con q", "Con letras"],
                        horizontal=True,
                        key="modo_renombrado_minimo_er",
                    )

                    nombres_minimo = simbolo.crear_estados(
                        len(dfa_minimo.estados), modo_minimo
                    )

                    dfa_minimo_mostrar, mapa_minimo = dfa_minimo.renombrar_estados(
                        nombres_minimo
                    )

                    with st.expander("Equivalencias de nombres"):
                        st.dataframe(
                            pd.DataFrame(
                                {
                                    "Antes": list(mapa_minimo.keys()),
                                    "Después": list(mapa_minimo.values()),
                                }
                            ),
                            hide_index=True,
                        )

                st.dataframe(simbolo.tabla_dfa(dfa_minimo_mostrar), hide_index=True)
                st.graphviz_chart(dfa_minimo_mostrar.automata_a_dot())

                # ---------------- Ecuaciones y expresión regular ----------------
                st.subheader("Ecuaciones de transiciones entrantes")
                st.code("\n".join(dfa_minimo_mostrar.formatear_ecuaciones()), language=None)

                st.subheader("Expresión regular")

                expresion = exp_regular_prueba.automata_a_regex(dfa_minimo_mostrar)

                st.code(str(expresion))
      
        