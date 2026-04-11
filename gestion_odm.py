import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión ODM - Gurum Café", layout="wide", page_icon="☕")

# URL de tu Google Sheets
URL_SHEET = "https://docs.google.com/spreadsheets/d/1_nN-L9C44kkI-v-KmPwfdwjCg78N5m4juvIGW1XFB9c/edit?usp=sharing"
LISTA_RESPONSABLES = ["Ezequiel Caceres", "Micaela Cardozo", "Federico Kong", "Aldana Molina"]

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    # ttl=0 para forzar la lectura de datos frescos
    return conn.read(spreadsheet=URL_SHEET, ttl=0)

try:
    df_raw = cargar_datos()
except Exception as e:
    st.error("Error de conexión. Asegurate de haber configurado los 'Secrets' en Streamlit Cloud.")
    st.stop()

# --- ENCABEZADO ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try:
        st.image("gurumcafe.jpg", width=130)
    except:
        st.subheader("☕ Gurum")
with col_titulo:
    st.title("Sistema de Gestión de Oportunidades de Mejora (ODM)")

st.divider()

# --- DASHBOARD (DESPLEGABLE) ---
with st.expander("📊 Ver Estadísticas (Gráfico de Tortas)"):
    if not df_raw.empty:
        fig = px.pie(df_raw, names='Estado', title='Distribución de Estados',
                     color='Estado', color_discrete_map={'Abierta':'#ef553b', 'En Curso':'#636efa', 'Cerrada':'#00cc96'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No hay datos para mostrar gráficos.")

# --- PESTAÑAS PRINCIPALES ---
tab_gestion, tab_nuevo = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

# --- TAB 1: GESTIÓN, FILTROS Y EDICIÓN ---
with tab_gestion:
    # FILTROS
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 1, 1])
    with col_f1:
        f_resp = st.selectbox("Filtrar por Responsable", ["Todos"] + LISTA_RESPONSABLES)
    with col_f2:
        f_prio = st.selectbox("Filtrar por Prioridad", ["Todas", "Baja", "Media", "Alta"])
    with col_f3:
        st.write(" ")
        if st.button("♻️ Limpiar Filtros", use_container_width=True):
            st.rerun()
    with col_f4:
        st.write(" ")
        # DESCARGA A EXCEL
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_raw.to_excel(writer, index=False)
        st.download_button("📥 Descargar Excel", output.getvalue(), "ODMs_Gurum_Cafe.xlsx", use_container_width=True)

    # Aplicar Filtros
    dff = df_raw.copy()
    if f_resp != "Todos": dff = dff[dff["Responsable"] == f_resp]
    if f_prio != "Todas": dff = dff[dff["Prioridad"] == f_prio]

    st.subheader("📋 Listado de ODMs")
    st.info("💡 Hacé clic en el círculo al inicio de una fila para editarla abajo.")
    
    # Tabla interactiva
    event = st.dataframe(dff, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

    # Lógica de Edición
    if len(event.selection.rows) > 0:
        idx_tabla = event.selection.rows[0]
        datos_fila = dff.iloc[idx_tabla]
        id_real = datos_fila['ID']
        # Obtener índice real en el dataframe original
        idx_original = df_raw.index[df_raw['ID'] == id_real].tolist()[0]

        st.markdown(f"### 🛠️ Editando ODM #{id_real}")
        
        # Regla: Si está cerrada, no se edita
        if str(datos_fila["Estado"]).strip() == "Cerrada":
            st.warning("🔒 Esta ODM ya está **Cerrada** y no se puede modificar.")
        else:
            with st.form("form_edicion"):
                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    edit_titulo = st.text_input("Título", value=datos_fila["Título"])
                    edit_estado = st.selectbox("Estado", ["Abierta", "En Curso", "Cerrada"], 
                                             index=["Abierta", "En Curso", "Cerrada"].index(datos_fila["Estado"]))
                with c_e2:
                    edit_coment = st.text_area("Comentarios / Avances", value=datos_fila["Comentarios"])
                
                if st.form_submit_button("💾 Guardar Cambios"):
                    df_raw.at[idx_original, "Título"] = edit_titulo
                    df_raw.at[idx_original, "Estado"] = edit_estado
                    df_raw.at[idx_original, "Comentarios"] = edit_coment
                    # Guardar automáticamente en el Sheets
                    conn.update(spreadsheet=URL_SHEET, data=df_raw)
                    st.success("✅ ¡Cambios guardados en Google Sheets!")
                    st.rerun()

    st.divider()
    # SECCIÓN DE BORRADO
    with st.expander("🗑️ Zona de Peligro: Borrar ODM"):
        id_a_borrar = st.number_input("Ingresar ID de la ODM a eliminar", min_value=1, step=1)
        if st.button("Confirmar Eliminación"):
            if id_a_borrar in df_raw["ID"].values:
                df_final = df_raw[df_raw["ID"] != id_a_borrar]
                conn.update(spreadsheet=URL_SHEET, data=df_final)
                st.success(f"ODM #{id_a_borrar} eliminada correctamente.")
                st.rerun()
            else:
                st.error("El ID ingresado no existe.")

# --- TAB 2: NUEVA ODM ---
with tab_nuevo:
    st.subheader("➕ Cargar Nueva Oportunidad de Mejora")
    with st.form("form_alta", clear_on_submit=True):
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            n_titulo = st.text_input("Título de la ODM *")
            n_resp = st.selectbox("Responsable *", ["Seleccionar..."] + LISTA_RESPONSABLES)
            n_desc = st.text_area("Descripción detallada")
        with col_n2:
            n_prio = st.select_slider("Prioridad *", ["Baja", "Media", "Alta"], value="Media")
            n_fecha_sol = st.date_input("Fecha Est. Solución", datetime.now())
            n_coment = st.text_area("Comentarios Iniciales")
        
        if st.form_submit_button("🚀 Guardar ODM"):
            # VALIDACIÓN
            if n_titulo == "" or n_resp == "Seleccionar...":
                st.error("Faltan campos obligatorios: Título y Responsable.")
            else:
                proximo_id = int(df_raw["ID"].max() + 1) if not df_raw.empty else 1
                nueva_fila = pd.DataFrame([{
                    "ID": proximo_id,
                    "Título": n_titulo,
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Descripción": n_desc,
                    "Responsable": n_resp,
                    "Prioridad": n_prio,
                    "Fecha Est. Solución": n_fecha_sol.strftime("%d/%m/%Y"),
                    "Estado": "Abierta",
                    "Comentarios": n_coment
                }])
                df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                # Guardado automático
                conn.update(spreadsheet=URL_SHEET, data=df_final)
                st.balloons()
                st.success(f"✅ ¡ODM #{proximo_id} guardada con éxito!")
                st.rerun()