import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import io

st.set_page_config(page_title="Gestión ODM - Gurum Café", layout="wide", page_icon="☕")

# Conexión usando los Secrets configurados
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    # ttl=0 para que siempre traiga los datos más frescos del Sheets
    return conn.read(ttl=0)

df_raw = cargar_datos()

# --- ENCABEZADO ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try: st.image("gurumcafe.jpg", width=130)
    except: st.subheader("☕")
with col_titulo:
    st.title("Sistema de Gestión de Oportunidades de Mejora")

st.divider()

# --- TABS CON TODOS LOS REQUERIMIENTOS ---
tab_gestion, tab_nuevo = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

with tab_gestion:
    # Filtros y Estadísticas
    with st.expander("📊 Ver Estadísticas y Filtros", expanded=True):
        f1, f2, f3 = st.columns([2, 2, 1])
        with f1: f_resp = st.selectbox("Responsable", ["Todos", "Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"])
        with f2: f_prio = st.selectbox("Prioridad", ["Todas", "Baja", "Media", "Alta"])
        with f3:
            st.write(" ")
            if st.button("♻️ Refrescar"): st.rerun()
            
    dff = df_raw.copy()
    if f_resp != "Todos": dff = dff[dff["Responsable"] == f_resp]
    if f_prio != "Todas": dff = dff[dff["Prioridad"] == f_prio]

    st.subheader("Listado de ODMs")
    # Selección interactiva para editar
    sel = st.dataframe(dff, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

    if len(sel.selection.rows) > 0:
        idx = sel.selection.rows[0]
        row = dff.iloc[idx]
        
        st.markdown(f"### 🛠️ Editando ODM #{row['ID']}")
        with st.form("edit"):
            c1, c2 = st.columns(2)
            with c1:
                new_est = st.selectbox("Estado", ["Abierta", "En Curso", "Cerrada"], index=["Abierta", "En Curso", "Cerrada"].index(row['Estado']))
            with c2:
                new_com = st.text_area("Comentarios", value=row['Comentarios'])
            
            if st.form_submit_button("💾 Guardar Cambios"):
                # Actualizamos en el DF y mandamos al Sheets
                df_raw.loc[df_raw['ID'] == row['ID'], 'Estado'] = new_est
                df_raw.loc[df_raw['ID'] == row['ID'], 'Comentarios'] = new_com
                conn.update(data=df_raw)
                st.success("¡Datos actualizados en la nube!")
                st.rerun()

with tab_nuevo:
    with st.form("alta", clear_on_submit=True):
        st.subheader("📝 Registrar Nueva Oportunidad")
        col1, col2 = st.columns(2)
        with col1:
            t = st.text_input("Título *")
            r = st.selectbox("Responsable *", ["Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"])
            desc = st.text_area("Descripción")
        with col2:
            p = st.select_slider("Prioridad *", ["Baja", "Media", "Alta"])
            f_sol = st.date_input("Fecha Est. Solución")
            com_i = st.text_area("Comentarios Iniciales")
            
        if st.form_submit_button("🚀 Guardar en Sheets"):
            if t:
                nuevo_id = int(df_raw["ID"].max() + 1) if not df_raw.empty else 1
                nueva_fila = pd.DataFrame([{
                    "ID": nuevo_id, "Título": t, "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Descripción": desc, "Responsable": r, "Prioridad": p,
                    "Fecha Est. Solución": f_sol.strftime("%d/%m/%Y"), "Estado": "Abierta", "Comentarios": com_i
                }])
                df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                # EL MOMENTO DE LA VERDAD: Escritura automática
                conn.update(data=df_final)
                st.balloons()
                st.success(f"ODM #{nuevo_id} guardada con éxito.")
                st.rerun()