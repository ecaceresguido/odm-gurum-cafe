import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import io

# Configuración de página
st.set_page_config(page_title="Gestión ODM - Gurum Café", layout="wide", page_icon="☕")

# Conexión automática (usa los Secrets que ya configuraste)
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar():
    return conn.read(ttl=0)

try:
    df = cargar()
except:
    st.error("Error cargando la base de datos. Verificá los Secrets.")
    st.stop()

# Título y Estilo
st.title("☕ Gestión de Mejoras - Gurum Café")
st.divider()

tab1, tab2 = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

# --- TAB 1: LISTADO, FILTROS Y EDICIÓN ---
with tab1:
    # Dashboard rápido
    with st.expander("📊 Ver Estadísticas"):
        if not df.empty:
            fig = px.pie(df, names='Estado', title='Estado de las ODMs',
                         color='Estado', color_discrete_map={'Abierta':'#ef553b', 'En Curso':'#636efa', 'Cerrada':'#00cc96'})
            st.plotly_chart(fig, use_container_width=True)

    # Filtros y Descarga
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: f_resp = st.selectbox("Responsable", ["Todos", "Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"])
    with c2: f_prio = st.selectbox("Prioridad", ["Todas", "Baja", "Media", "Alta"])
    with c3:
        st.write(" ")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Descargar Excel", output.getvalue(), "ODMs_Gurum.xlsx")

    dff = df.copy()
    if f_resp != "Todos": dff = dff[dff["Responsable"] == f_resp]
    if f_prio != "Todas": dff = dff[dff["Prioridad"] == f_prio]

    st.subheader("Listado Actual")
    sel = st.dataframe(dff, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

    if len(sel.selection.rows) > 0:
        idx = sel.selection.rows[0]
        fila = dff.iloc[idx]
        idx_original = df.index[df['ID'] == fila['ID']].tolist()[0]

        with st.form("editor"):
            st.markdown(f"### 🛠️ Editando ODM #{fila['ID']}")
            if fila['Estado'] == "Cerrada":
                st.warning("Esta ODM está cerrada.")
            
            new_est = st.selectbox("Estado", ["Abierta", "En Curso", "Cerrada"], index=["Abierta", "En Curso", "Cerrada"].index(fila['Estado']))
            new_com = st.text_area("Comentarios", value=fila['Comentarios'])
            
            if st.form_submit_button("💾 Guardar Cambios"):
                df.at[idx_original, 'Estado'] = new_est
                df.at[idx_original, 'Comentarios'] = new_com
                conn.update(data=df)
                st.success("✅ ¡Cambios guardados!")
                st.rerun()

# --- TAB 2: REGISTRO NUEVO ---
with tab_nuevo:
    st.subheader("Registrar Nueva ODM")
    with st.form("alta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            t = st.text_input("Título *")
            r = st.selectbox("Responsable", ["Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"])
            desc = st.text_area("Descripción")
        with col2:
            p = st.select_slider("Prioridad", ["Baja", "Media", "Alta"])
            f = st.date_input("Fecha Est. Solución")
            ci = st.text_area("Comentarios Iniciales")
        
        if st.form_submit_button("🚀 Guardar ODM"):
            if t:
                new_id = int(df['ID'].max() + 1) if not df.empty else 1
                nueva = pd.DataFrame([{
                    "ID": new_id, "Título": t, "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Descripción": desc, "Responsable": r, "Prioridad": p,
                    "Fecha Est. Solución": f.strftime("%d/%m/%Y"), "Estado": "Abierta", "Comentarios": ci
                }])
                df_final = pd.concat([df, nueva], ignore_index=True)
                conn.update(data=df_final)
                st.balloons()
                st.success(f"✅ ¡Guardado con éxito! ODM #{new_id} registrada.")
                st.rerun()
            else:
                st.error("El título es obligatorio.")