import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión ODM - Gurum Café", layout="wide", page_icon="☕")

# URL de tu Sheets (Asegurate que termine en /edit?usp=sharing)
URL_SHEET = "https://docs.google.com/spreadsheets/d/1_nN-L9C44kkI-v-KmPwfdwjCg78N5m4juvIGW1XFB9c/edit?usp=sharing"
LISTA_RESPONSABLES = ["Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"]

# Conexión Directa
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    return conn.read(spreadsheet=URL_SHEET, ttl=0)

df_raw = cargar_datos()

# --- ENCABEZADO ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try: st.image("gurumcafe.jpg", width=130)
    except: st.subheader("☕")
with col_titulo:
    st.title("Sistema de Gestión de Oportunidades de Mejora")

st.divider()

# --- DASHBOARD ---
with st.expander("📊 Estadísticas de Cumplimiento", expanded=False):
    if not df_raw.empty:
        fig = px.pie(df_raw, names='Estado', title='Distribución por Estado',
                     color='Estado', color_discrete_map={'Abierta':'#ef553b', 'En Curso':'#636efa', 'Cerrada':'#00cc96'})
        st.plotly_chart(fig, use_container_width=True)

# --- TABS ---
tab_gestion, tab_nuevo = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

# --- TAB 1: GESTIÓN ---
with tab_gestion:
    # Filtros
    f1, f2, f3, f4 = st.columns([2, 2, 1, 1])
    with f1: f_resp = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES)
    with f2: f_prio = st.selectbox("Prioridad", ["Todas", "Baja", "Media", "Alta"])
    with f3: 
        st.write(" ")
        if st.button("♻️ Limpiar Filtros", use_container_width=True): st.rerun()
    with f4:
        st.write(" ")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_raw.to_excel(writer, index=False)
        st.download_button("📥 Descargar Excel", output.getvalue(), "ODMs_Gurum.xlsx", use_container_width=True)

    dff = df_raw.copy()
    if f_resp != "Todos": dff = dff[dff["Responsable"] == f_resp]
    if f_prio != "Todas": dff = dff[dff["Prioridad"] == f_prio]

    st.subheader("Listado de ODMs")
    st.info("💡 Seleccioná una fila para editar sus detalles.")
    # Selección de fila
    event = st.dataframe(dff, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

    if len(event.selection.rows) > 0:
        idx_filtrado = event.selection.rows[0]
        datos_fila = dff.iloc[idx_filtrado]
        id_original = datos_fila['ID']
        # Buscamos el índice real en el dataframe original para actualizar correctamente
        idx_real = df_raw.index[df_raw['ID'] == id_original].tolist()[0]

        st.markdown(f"### 🛠️ Editando ODM #{id_original}")
        
        if str(datos_fila["Estado"]) == "Cerrada":
            st.warning("⚠️ Esta ODM está Cerrada. No se permiten más modificaciones.")
        else:
            with st.form("form_edicion"):
                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    e_titulo = st.text_input("Título", value=datos_fila["Título"])
                    e_estado = st.selectbox("Estado", ["Abierta", "En Curso", "Cerrada"], 
                                          index=["Abierta", "En Curso", "Cerrada"].index(datos_fila["Estado"]))
                with c_e2:
                    e_coment = st.text_area("Comentarios / Avances", value=datos_fila["Comentarios"])
                
                if st.form_submit_button("💾 Guardar Cambios"):
                    df_raw.at[idx_real, "Título"] = e_titulo
                    df_raw.at[idx_real, "Estado"] = e_estado
                    df_raw.at[idx_real, "Comentarios"] = e_coment
                    conn.update(spreadsheet=URL_SHEET, data=df_raw)
                    st.success("¡Cambios actualizados automáticamente!")
                    st.rerun()

    st.divider()
    with st.expander("🗑️ Zona de Peligro (Eliminar)"):
        id_del = st.number_input("ID a borrar", min_value=1, step=1)
        if st.button("Confirmar Borrado"):
            df_final = df_raw[df_raw["ID"] != id_del]
            conn.update(spreadsheet=URL_SHEET, data=df_final)
            st.success(f"ODM #{id_del} eliminada.")
            st.rerun()

# --- TAB 2: NUEVA ODM ---
with tab_nuevo:
    with st.form("nuevo_registro", clear_on_submit=True):
        st.subheader("📝 Registrar Nueva Oportunidad")
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            n_tit = st.text_input("Título de la ODM *")
            n_resp = st.selectbox("Responsable Asignado *", LISTA_RESPONSABLES)
            n_desc = st.text_area("Descripción Detallada")
        with col_n2:
            n_prio = st.select_slider("Prioridad *", ["Baja", "Media", "Alta"])
            n_fecha_sol = st.date_input("Fecha Est. Solución")
            n_coment = st.text_area("Comentarios Iniciales")
        
        if st.form_submit_button("🚀 Guardar ODM"):
            if n_tit:
                proximo_id = int(df_raw["ID"].max() + 1) if not df_raw.empty else 1
                nueva_odm = pd.DataFrame([{
                    "ID": proximo_id,
                    "Título": n_tit,
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Descripción": n_desc,
                    "Responsable": n_resp,
                    "Prioridad": n_prio,
                    "Fecha Est. Solución": n_fecha_sol.strftime("%d/%m/%Y"),
                    "Estado": "Abierta",
                    "Comentarios": n_coment
                }])
                df_actualizado = pd.concat([df_raw, nueva_odm], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, data=df_actualizado)
                st.balloons()
                st.success(f"¡ODM #{proximo_id} creada y guardada automáticamente!")
                st.rerun()
            else:
                st.error("El título es obligatorio.")