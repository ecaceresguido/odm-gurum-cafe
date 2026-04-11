import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import io

# --- CONFIGURACIÓN ---
URL_SHEET = "https://docs.google.com/spreadsheets/d/1_nN-L9C44kkI-v-KmPwfdwjCg78N5m4juvIGW1XFB9c/edit?gid=0#gid=0"
LISTA_RESPONSABLES = ["Seleccionar...", "Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"]

st.set_page_config(page_title="Gestión ODM - Gurum Café", layout="wide", page_icon="☕")

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    return conn.read(spreadsheet=URL_SHEET, ttl="0")

df_raw = cargar_datos()

# --- INTERFAZ: ENCABEZADO ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try:
        st.image("gurumcafe.jpg", width=140)
    except:
        st.subheader("☕ Gurum Café")
with col_titulo:
    st.title("Oportunidades de Mejora (ODM)")

st.divider()

# --- DASHBOARD (GRÁFICOS) ---
with st.expander("📊 Ver Estadísticas (Gráfico de Tortas)"):
    if not df_raw.empty:
        fig = px.pie(df_raw, names='Estado', title='Distribución de Estados de ODM',
                     color='Estado', color_discrete_map={'Abierta':'#ef553b', 'En Curso':'#636efa', 'Cerrada':'#00cc96'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No hay datos para mostrar gráficos.")

# --- TABS PRINCIPALES ---
tab_gestion, tab_nuevo = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

with tab_gestion:
    if not df_raw.empty:
        # Filtros y Botón Limpiar
        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 1, 1])
        with col_f1:
            f_resp = st.selectbox("Filtrar Responsable", ["Todos"] + LISTA_RESPONSABLES[1:])
        with col_f2:
            f_prio = st.selectbox("Filtrar Prioridad", ["Todas", "Baja", "Media", "Alta"])
        with col_f3:
            st.write(" ")
            if st.button("♻️ Limpiar Filtros"):
                st.rerun()
        with col_f4:
            st.write(" ")
            # Descarga a Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_raw.to_excel(writer, index=False, sheet_name='ODMs')
            st.download_button(label="📥 Descargar Excel", data=output.getvalue(), file_name="ODMs_Gurum_Cafe.xlsx")

        # Aplicar Filtros
        dff = df_raw.copy()
        if f_resp != "Todos": dff = dff[dff["Responsable"] == f_resp]
        if f_prio != "Todas": dff = dff[dff["Prioridad"] == f_prio]

        st.subheader("📋 Listado de ODMs")
        event = st.dataframe(dff, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

        if len(event.selection.rows) > 0:
            index_sel = event.selection.rows[0]
            datos = dff.iloc[index_sel]
            id_real = datos['ID']

            st.markdown(f"#### 🛠️ Editando ODM #{id_real}")
            
            # REGLA: Si está cerrada, no se edita
            if str(datos["Estado"]).strip() == "Cerrada":
                st.warning("⚠️ Esta ODM está **Cerrada** y no puede modificarse.")
                st.json(datos.to_dict())
            else:
                with st.form("form_edit"):
                    c1, c2 = st.columns(2)
                    with c1:
                        ne_tit = st.text_input("Título", value=datos["Título"])
                        ne_est = st.selectbox("Estado", ["Abierta", "En Curso", "Cerrada"], index=["Abierta", "En Curso", "Cerrada"].index(datos["Estado"]))
                    with c2:
                        ne_com = st.text_area("Comentarios / Avances", value=datos["Comentarios"])
                    
                    if st.form_submit_button("Guardar Cambios"):
                        df_raw.loc[df_raw["ID"] == id_real, ["Título", "Estado", "Comentarios"]] = [ne_tit, ne_est, ne_com]
                        conn.update(spreadsheet=URL_SHEET, data=df_raw)
                        st.success("Cambios guardados.")
                        st.rerun()

        st.divider()
        # --- SECCIÓN DE BORRADO ---
        with st.expander("🗑️ Zona de Peligro: Borrar ODM"):
            id_borrar = st.number_input("Ingresar ID de la ODM a eliminar", min_value=1, step=1)
            if st.button("Eliminar ODM"):
                if id_borrar in df_raw["ID"].values:
                    st.session_state.confirmar_borrado = id_borrar
                    st.warning(f"¿Confirmas que deseas eliminar permanentemente la ODM #{id_borrar}?")
                    if st.button("SÍ, ELIMINAR AHORA"):
                        df_final = df_raw[df_raw["ID"] != id_borrar]
                        conn.update(spreadsheet=URL_SHEET, data=df_final)
                        st.success("ODM eliminada correctamente.")
                        st.rerun()
                else:
                    st.error("El ID ingresado no existe.")
    else:
        st.warning("No hay datos cargados.")

with tab_nuevo:
    st.subheader("➕ Cargar Nueva Oportunidad de Mejora")
    with st.form("form_nueva", clear_on_submit=True):
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            t = st.text_input("Título *")
            r = st.selectbox("Responsable *", LISTA_RESPONSABLES)
            desc = st.text_area("Descripción detallada")
        with col_n2:
            p = st.select_slider("Prioridad *", ["Baja", "Media", "Alta"])
            f_est = st.date_input("Fecha Est. Solución", datetime.now())
            com = st.text_area("Comentarios Iniciales")
        
        if st.form_submit_button("🚀 Crear y Guardar"):
            # VALIDACIÓN OBLIGATORIA
            if t == "" or r == "Seleccionar...":
                st.error("Faltan campos obligatorios: Título y Responsable.")
            else:
                prox_id = int(df_raw["ID"].max() + 1) if not df_raw.empty else 1
                nueva = pd.DataFrame([{
                    "ID": prox_id, "Título": t, "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Descripción": desc, "Responsable": r, "Prioridad": p, 
                    "Fecha Est. Solución": f_est.strftime("%d/%m/%Y"), "Estado": "Abierta", "Comentarios": com
                }])
                df_final = pd.concat([df_raw, nueva], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, data=df_final)
                st.success(f"¡ODM #{prox_id} guardada exitosamente!")
                st.balloons()
                st.rerun()