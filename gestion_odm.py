import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import io

# --- CONFIGURACIÓN ---
SHEET_ID = "1_nN-L9C44kkI-v-KmPwfdwjCg78N5m4juvIGW1XFB9c"
# Usamos exportación CSV para lectura estable
URL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

LISTA_RESPONSABLES = ["Seleccionar...", "Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"]

st.set_page_config(page_title="Gestión ODM - Gurum Café", layout="wide", page_icon="☕")

# --- FUNCIONES DE DATOS ---
@st.cache_data(ttl=2)
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
    st.error("⚠️ No se pudieron cargar los datos. Verifica que el Sheets sea público como Editor.")
else:
    # --- DASHBOARD ---
    with st.expander("📊 Ver Estadísticas"):
        fig = px.pie(df_raw, names='Estado', title='Estado de las ODM',
                     color='Estado', color_discrete_map={'Abierta':'#ef553b', 'En Curso':'#636efa', 'Cerrada':'#00cc96'})
        st.plotly_chart(fig, use_container_width=True)

    tab_gestion, tab_nuevo = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

    with tab_gestion:
        # Filtros
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        with c1: f_resp = st.selectbox("Filtrar Responsable", ["Todos"] + LISTA_RESPONSABLES[1:])
        with c2: f_prio = st.selectbox("Filtrar Prioridad", ["Todas", "Baja", "Media", "Alta"])
        with c3:
            st.write(" ")
            if st.button("♻️ Limpiar Filtros"): st.rerun()
        with col_logo: # Usamos un espacio para el botón de descarga
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_raw.to_excel(writer, index=False)
            st.download_button("📥 Excel", output.getvalue(), "ODMs_Gurum.xlsx")

        dff = df_raw.copy()
        if f_resp != "Todos": dff = dff[dff["Responsable"] == f_resp]
        if f_prio != "Todas": dff = dff[dff["Prioridad"] == f_prio]

        st.subheader("📋 Listado de ODMs")
        # Selección de fila para editar
        event = st.dataframe(dff, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

        if len(event.selection.rows) > 0:
            idx = event.selection.rows[0]
            datos = dff.iloc[idx]
            id_sel = datos['ID']

            st.markdown(f"### 🛠️ Gestionar ODM #{id_sel}")
            
            if str(datos["Estado"]).strip() == "Cerrada":
                st.warning("🔒 Esta ODM está Cerrada y no permite más ediciones.")
            else:
                with st.form("edit_form"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        new_tit = st.text_input("Título", value=datos["Título"])
                        new_est = st.selectbox("Estado", ["Abierta", "En Curso", "Cerrada"], 
                                             index=["Abierta", "En Curso", "Cerrada"].index(datos["Estado"]))
                    with col_e2:
                        new_com = st.text_area("Comentarios / Avances", value=datos["Comentarios"])
                    
                    if st.form_submit_button("✅ Guardar Cambios en Sheets"):
                        st.info(f"Para guardar, copiá esta línea corregida y pegala sobre la fila #{id_sel} en tu Sheets.")
                        # Generamos la línea completa para que solo tengan que sobreescribir
                        linea_edit = f"{id_sel}\t{new_tit}\t{datos['Fecha']}\t{datos['Descripción']}\t{datos['Responsable']}\t{datos['Prioridad']}\t{datos['Fecha Est. Solución']}\t{new_est}\t{new_com}"
                        st.code(linea_edit)

        st.divider()
        with st.expander("🗑️ Borrar ODM"):
            id_borrar = st.number_input("ID a eliminar", min_value=1, step=1)
            if st.button("Confirmar Eliminación"):
                st.warning(f"Para eliminar, simplemente borra la fila #{id_borrar} directamente en el Google Sheets.")

    with tab_nuevo:
        with st.form("nueva_odm", clear_on_submit=True):
            st.subheader("📝 Nueva ODM")
            c_n1, c_n2 = st.columns(2)
            with c_n1:
                t = st.text_input("Título *")
                r = st.selectbox("Responsable *", LISTA_RESPONSABLES)
                desc = st.text_area("Descripción")
            with c_n2:
                p = st.select_slider("Prioridad *", ["Baja", "Media", "Alta"])
                f_est = st.date_input("Fecha Est. Solución", datetime.now())
                com_i = st.text_area("Comentarios Iniciales")
            
            if st.form_submit_button("🚀 Crear ODM"):
                if t and r != "Seleccionar...":
                    prox_id = int(df_raw["ID"].max() + 1) if not df_raw.empty else 1
                    f_crea = datetime.now().strftime("%d/%m/%Y")
                    f_sol = f_est.strftime("%d/%m/%Y")
                    # Generamos la fila para pegar
                    fila = f"{prox_id}\t{t}\t{f_crea}\t{desc}\t{r}\t{p}\t{f_sol}\tAbierta\t{com_i}"
                    st.success(f"✅ ¡ODM #{prox_id} lista! Copiá y pegá esto al final del Sheets:")
                    st.code(fila)
                else:
                    st.error("Título, Responsable y Prioridad son obligatorios.")