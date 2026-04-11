import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
# Este link permite leer los datos de forma estable
URL_RAW = "https://docs.google.com/spreadsheets/d/1_nN-L9C44kkI-v-KmPwfdwjCg78N5m4juvIGW1XFB9c/export?format=csv&gid=0"
# Este link es el que usaremos para que el usuario vaya a editar
URL_EDIT = "https://docs.google.com/spreadsheets/d/1_nN-L9C44kkI-v-KmPwfdwjCg78N5m4juvIGW1XFB9c/edit"

LISTA_RESPONSABLES = ["Seleccionar...", "Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"]

st.set_page_config(page_title="Panel ODM - Gurum Café", layout="wide", page_icon="☕")

# --- CARGA DE DATOS ---
@st.cache_data(ttl=5) # Se actualiza muy rápido
def cargar_datos():
    try:
        # Forzamos la lectura limpia del CSV de Google
        df = pd.read_csv(URL_RAW)
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df_raw = cargar_datos()

# --- ENCABEZADO ---
col_logo, col_titulo = st.columns([1, 5]) 
with col_logo:
    if os.path.exists("gurumcafe.jpg"):
        st.image("gurumcafe.jpg", width=150)
with col_titulo:
    st.title("☕ Oportunidades de Mejora Gurum Café")

st.divider()

if df_raw.empty:
    st.warning("⚠️ No hay datos o la planilla está vacía. Si acabas de crear el Sheets, cargá al menos una fila de prueba.")
else:
    tab_gestion, tab_nuevo = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

    with tab_gestion:
        # FILTROS
        c1, c2, c3 = st.columns([2,2,1])
        with c1:
            f_resp = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES[1:])
        with c2:
            f_prio = st.selectbox("Prioridad", ["Todas", "Baja", "Media", "Alta"])
        with c3:
            st.write("") # Espacio
            if st.button("♻️ Refrescar"):
                st.cache_data.clear()
                st.rerun()

        # Aplicar Filtros
        dff = df_raw.copy()
        if f_resp != "Todos": dff = dff[dff["Responsable"] == f_resp]
        if f_prio != "Todas": dff = dff[dff["Prioridad"] == f_prio]

        st.subheader("📋 Listado de ODMs")
        # Mostramos la tabla. El on_select es lo que causaba el error antes con la otra librería.
        # Aquí lo mostramos para lectura clara.
        st.dataframe(dff, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🛠️ Acciones de Edición")
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            st.info("Para **Editar** una ODM existente o **Eliminarla**:")
            st.link_button("📝 Abrir Editor en Google Sheets", URL_EDIT)
        with col_ed2:
            st.write("Cualquier cambio que hagas en el Sheets se verá reflejado acá al presionar el botón **Refrescar**.")

    with tab_nuevo:
        st.subheader("➕ Cargar Nueva ODM")
        with st.form("form_nueva"):
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                t = st.text_input("Título")
                r = st.selectbox("Responsable", LISTA_RESPONSABLES)
                desc = st.text_area("Descripción detallada")
            with col_n2:
                p = st.select_slider("Prioridad", ["Baja", "Media", "Alta"])
                f_sol = st.date_input("Fecha Est. Solución")
                com = st.text_area("Comentarios Iniciales")
            
            if st.form_submit_button("Generar ODM"):
                if t and r != "Seleccionar...":
                    prox_id = len(df_raw) + 1
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                    # Creamos la fila formateada para Sheets
                    fila_nueva = f"{prox_id},{t},{fecha_hoy},{desc},{r},{p},{f_sol.strftime('%d/%m/%Y')},Abierto,{com}"
                    
                    st.success("✅ ¡Fila generada! Seguí estos pasos:")
                    st.markdown(f"""
                    1. Copiá el código de abajo.
                    2. Hacé clic en el botón 'Ir al Sheets'.
                    3. Pegalo en la primera fila vacía al final.
                    """)
                    st.code(fila_nueva)
                    st.link_button("🏃 Ir al Sheets a pegar", URL_EDIT)
                else:
                    st.error("Faltan datos obligatorios (Título o Responsable)")