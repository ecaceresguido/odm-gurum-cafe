import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
from PIL import Image
import io
import os

# --- CONFIGURACIÓN ---
ruta_logo = "gurumcafe.jpg" 
URL_SHEET = "https://docs.google.com/spreadsheets/d/1_nN-L9C44kkI-v-KmPwfdwjCg78N5m4juvIGW1XFB9c/edit?gid=0#gid=0" # <--- PEGA TU LINK ACÁ

LISTA_RESPONSABLES = [
    "Seleccionar...", "Ezequiel Caceres", "Micaela Cardozo", 
    "Federico Kong", "Aldana Molina"
]

# --- INTERFAZ ---
st.set_page_config(page_title="Panel ODM - Gurum Café", layout="wide", page_icon="☕")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_gsheets():
    return conn.read(spreadsheet=URL_SHEET, ttl="0")

if 'tabla_key' not in st.session_state:
    st.session_state.tabla_key = 0
if 'filtro_key' not in st.session_state:
    st.session_state.filtro_key = 0

# --- ENCABEZADO ---
col_logo, col_titulo = st.columns([1, 5]) 
with col_logo:
    if os.path.exists(ruta_logo):
        st.image(Image.open(ruta_logo), width=150)
with col_titulo:
    st.title("☕ Oportunidades de Mejora Gurum Café")

st.divider() 

# Carga inicial de datos
df_raw = cargar_datos_gsheets()

tab_gestion, tab_nuevo = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

with tab_gestion:
    if not df_raw.empty:
        # Filtros
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            filtro_resp = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES[1:], key=f"r_{st.session_state.filtro_key}")
        with col_f2:
            filtro_prio = st.selectbox("Prioridad", ["Todas", "Baja", "Media", "Alta"], key=f"p_{st.session_state.filtro_key}")
        with col_f3:
            st.write(" ")
            if st.button("♻️ Limpiar", use_container_width=True):
                st.session_state.filtro_key += 1
                st.rerun()

        df_f = df_raw.copy()
        if filtro_resp != "Todos": df_f = df_f[df_f["Responsable"] == filtro_resp]
        if filtro_prio != "Todas": df_f = df_f[df_f["Prioridad"] == filtro_prio]

        df_activas = df_f[df_f["Estado"] != "Finalizado"].reset_index(drop=True)
        
        st.subheader("📋 ODMs Activas")
        event = st.dataframe(df_activas, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"t_{st.session_state.tabla_key}")

        if len(event.selection.rows) > 0:
            datos = df_activas.iloc[event.selection.rows[0]]
            id_sel = datos['ID']
            
            with st.form("edit_form"):
                st.write(f"### Editando ODM #{id_sel}")
                c1, c2 = st.columns(2)
                with c1:
                    n_tit = st.text_input("Título", value=datos["Título"])
                    n_est = st.selectbox("Estado", ["Abierto", "En Curso", "Finalizado"], index=["Abierto", "En Curso", "Finalizado"].index(datos["Estado"]))
                with c2:
                    n_com = st.text_area("Comentarios", value=datos["Comentarios"])
                
                if st.form_submit_button("Guardar Cambios"):
                    df_raw.loc[df_raw["ID"] == id_sel, ["Título", "Estado", "Comentarios"]] = [n_tit, n_est, n_com]
                    conn.update(spreadsheet=URL_SHEET, data=df_raw)
                    st.success("Actualizado en Google Sheets")
                    st.session_state.tabla_key += 1
                    st.rerun()

with tab_nuevo:
    with st.form("nueva_odm"):
        t = st.text_input("Título")
        r = st.selectbox("Responsable", LISTA_RESPONSABLES)
        p = st.select_slider("Prioridad", ["Baja", "Media", "Alta"])
        if st.form_submit_button("Crear"):
            prox_id = str(int(df_raw["ID"].astype(int).max() + 1)) if not df_raw.empty else "1"
            nueva = pd.DataFrame([{"ID": prox_id, "Título": t, "Fecha Creación": datetime.now().strftime("%d/%m/%Y"), "Responsable": r, "Prioridad": p, "Estado": "Abierto", "Comentarios": ""}])
            df_final = pd.concat([df_raw, nueva], ignore_index=True)
            conn.update(spreadsheet=URL_SHEET, data=df_final)
            st.success("¡ODM Creada!")
            st.rerun()