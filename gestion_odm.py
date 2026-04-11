import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- CONFIGURACIÓN ---
SHEET_ID = "1_nN-L9C44kkI-v-KmPwfdwjCg78N5m4juvIGW1XFB9c"
URL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
URL_EDIT = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

LISTA_RESPONSABLES = ["Seleccionar...", "Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"]

st.set_page_config(page_title="Gestión ODM - Gurum Café", layout="wide", page_icon="☕")

# --- CARGA DE DATOS ---
@st.cache_data(ttl=5)
def cargar_datos():
    try:
        df = pd.read_csv(URL_CSV)
        return df
    except:
        return pd.DataFrame()

df_raw = cargar_datos()

# --- ENCABEZADO ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try: st.image("gurumcafe.jpg", width=140)
    except: st.subheader("☕")
with col_titulo:
    st.title("Oportunidades de Mejora (ODM)")

st.divider()

if df_raw.empty:
    st.error("⚠️ No se pudieron cargar los datos. Verifica el Sheets.")
else:
    # Gráficos
    with st.expander("📊 Ver Estadísticas"):
        if 'Estado' in df_raw.columns:
            fig = px.pie(df_raw, names='Estado', title='Estado de las ODM',
                         color='Estado', color_discrete_map={'Abierta':'#ef553b', 'En Curso':'#636efa', 'Cerrada':'#00cc96'})
            st.plotly_chart(fig, use_container_width=True)

    tab_gestion, tab_nuevo = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

    with tab_gestion:
        # Filtros
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1: f_resp = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES[1:])
        with c2: f_prio = st.selectbox("Prioridad", ["Todas", "Baja", "Media", "Alta"])
        with c3: 
            st.write("")
            if st.button("♻️ Refrescar"): st.rerun()

        dff = df_raw.copy()
        if f_resp != "Todos": dff = dff[dff["Responsable"] == f_resp]
        if f_prio != "Todas": dff = dff[dff["Prioridad"] == f_prio]

        st.dataframe(dff, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🛠️ Acciones")
        st.info("Para **Editar** o **Borrar** una fila, usa el botón de abajo para abrir el Excel directamente:")
        st.link_button("📝 Abrir Editor de Google Sheets", URL_EDIT)

    with tab_nuevo:
        with st.form("nueva_odm"):
            st.subheader("📝 Generar Nueva ODM")
            t = st.text_input("Título *")
            r = st.selectbox("Responsable *", LISTA_RESPONSABLES)
            p = st.select_slider("Prioridad *", ["Baja", "Media", "Alta"])
            desc = st.text_area("Descripción")
            
            if st.form_submit_button("🚀 Crear Fila"):
                if t and r != "Seleccionar...":
                    prox_id = int(df_raw["ID"].max() + 1) if not df_raw.empty else 1
                    fecha = datetime.now().strftime("%d/%m/%Y")
                    # Formato para copiar y pegar fácil
                    fila = f"{prox_id}, {t}, {fecha}, {desc}, {r}, {p}, , Abierta, "
                    st.success("✅ ¡Fila generada! Copiala y pegala al final del Google Sheets:")
                    st.code(fila)
                    st.link_button("Ir al Sheets", URL_EDIT)
                else:
                    st.error("Título y Responsable son obligatorios.")