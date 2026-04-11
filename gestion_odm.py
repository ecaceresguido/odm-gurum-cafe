import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from PIL import Image
import os

# --- CONFIGURACIÓN ---
ruta_logo = "gurumcafe.jpg" 
# URL directa de tu Google Sheets
URL_SHEET = "https://docs.google.com/spreadsheets/d/1_nN-L9C44kkI-v-KmPwfdwjCg78N5m4juvIGW1XFB9c/edit?gid=0#gid=0"

LISTA_RESPONSABLES = [
    "Seleccionar...", "Ezequiel Caceres", "Micaela Cardozo", 
    "Federico Kong", "Aldana Molina"
]

# --- INTERFAZ ---
st.set_page_config(page_title="Panel ODM - Gurum Café", layout="wide", page_icon="☕")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_gsheets():
    # ttl="0" para que siempre traiga datos frescos de la nube
    return conn.read(spreadsheet=URL_SHEET, ttl="0")

# Inicialización de estados para refrescar componentes
if 'tabla_key' not in st.session_state:
    st.session_state.tabla_key = 0
if 'filtro_key' not in st.session_state:
    st.session_state.filtro_key = 0

# --- ENCABEZADO ---
col_logo, col_titulo = st.columns([1, 5]) 
with col_logo:
    if os.path.exists(ruta_logo):
        st.image(Image.open(ruta_logo), width=150)
    else:
        st.write("☕ **Gurum Café**")
with col_titulo:
    st.title("☕ Oportunidades de Mejora Gurum Café")

st.divider() 

# Carga de datos
df_raw = cargar_datos_gsheets()

tab_gestion, tab_nuevo = st.tabs(["📋 Gestión y Edición", "➕ Nueva ODM"])

# --- TAB 1: GESTIÓN Y EDICIÓN ---
with tab_gestion:
    if not df_raw.empty:
        # --- FILTROS ---
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            filtro_resp = st.selectbox("Filtrar por Responsable", ["Todos"] + LISTA_RESPONSABLES[1:], key=f"r_{st.session_state.filtro_key}")
        with col_f2:
            filtro_prio = st.selectbox("Filtrar por Prioridad", ["Todas", "Baja", "Media", "Alta"], key=f"p_{st.session_state.filtro_key}")
        with col_f3:
            st.write(" ")
            if st.button("♻️ Limpiar Filtros", use_container_width=True):
                st.session_state.filtro_key += 1
                st.rerun()

        # Aplicar filtros al DataFrame
        df_f = df_raw.copy()
        if filtro_resp != "Todos": 
            df_f = df_f[df_f["Responsable"] == filtro_resp]
        if filtro_prio != "Todas": 
            df_f = df_f[df_f["Prioridad"] == filtro_prio]

        # Solo mostrar las que no están finalizadas (o mostrar todas según prefieras)
        st.subheader("📋 ODMs Activas")
        st.info("Seleccioná una fila para editarla o eliminarla.")
        
        event = st.dataframe(
            df_f, 
            use_container_width=True, 
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row", 
            key=f"t_{st.session_state.tabla_key}"
        )

        # --- FORMULARIO DE EDICIÓN (Aparece al seleccionar una fila) ---
        if len(event.selection.rows) > 0:
            datos = df_f.iloc[event.selection.rows[0]]
            id_sel = datos['ID']
            
            st.markdown("---")
            with st.container():
                st.write(f"### 🛠️ Editando ODM #{id_sel}")
                
                with st.form("edit_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        n_tit = st.text_input("Título", value=datos["Título"])
                        n_resp = st.selectbox("Responsable", LISTA_RESPONSABLES[1:], index=LISTA_RESPONSABLES[1:].index(datos["Responsable"]))
                    with c2:
                        n_prio = st.select_slider("Prioridad", options=["Baja", "Media", "Alta"], value=datos["Prioridad"])
                        n_est = st.selectbox("Estado", ["Abierto", "En Curso", "Finalizado"], index=["Abierto", "En Curso", "Finalizado"].index(datos["Estado"]))
                    with c3:
                        # Convertir fecha de string a objeto datetime para el date_input
                        try:
                            fecha_dt = datetime.strptime(str(datos["Fecha Est. Solución"]), "%d/%m/%Y")
                        except:
                            fecha_dt = datetime.now()
                        n_fecha_est = st.date_input("Fecha Est. Solución", value=fecha_dt)

                    n_desc = st.text_area("Descripción", value=datos["Descripción"])
                    n_com = st.text_area("Comentarios", value=datos["Comentarios"])
                    
                    col_btn1, col_btn2 = st.columns([1, 4])
                    with col_btn1:
                        btn_guardar = st.form_submit_button("💾 Guardar Cambios")
                    
                # Botón de eliminar fuera del formulario de edición por seguridad
                if st.button("🗑️ Eliminar esta ODM", type="secondary"):
                    st.warning(f"¿Estás seguro de que querés eliminar la ODM #{id_sel}?")
                    if st.button("SÍ, ELIMINAR DEFINITIVAMENTE"):
                        df_final = df_raw[df_raw["ID"] != id_sel]
                        conn.update(spreadsheet=URL_SHEET, data=df_final)
                        st.success("ODM eliminada.")
                        st.session_state.tabla_key += 1
                        st.rerun()

                if btn_guardar:
                    # Actualizar los datos en el DataFrame original
                    df_raw.loc[df_raw["ID"] == id_sel, 
                               ["Título", "Responsable", "Prioridad", "Estado", "Descripción", "Fecha Est. Solución", "Comentarios"]] = \
                               [n_tit, n_resp, n_prio, n_est, n_desc, n_fecha_est.strftime("%d/%m/%Y"), n_com]
                    
                    conn.update(spreadsheet=URL_SHEET, data=df_raw)
                    st.success("¡Datos actualizados en Google Sheets!")
                    st.session_state.tabla_key += 1
                    st.rerun()
    else:
        st.warning("No se encontraron datos. Asegurate de tener los encabezados correctos en Google Sheets.")

# --- TAB 2: NUEVA ODM ---
with tab_nuevo:
    st.subheader("📝 Cargar nueva Oportunidad de Mejora")
    with st.form("nueva_odm", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            t = st.text_input("Título de la mejora")
            r = st.selectbox("Responsable asignado", LISTA_RESPONSABLES)
            desc = st.text_area("Descripción del problema/mejora")
        with c2:
            p = st.select_slider("Prioridad inicial", ["Baja", "Media", "Alta"])
            f_est = st.date_input("Fecha estimada de solución", datetime.now())
            com = st.text_area("Comentarios iniciales (opcional)")
        
        if st.form_submit_button("🚀 Crear ODM"):
            if t != "" and r != "Seleccionar...":
                # Calcular el próximo ID
                try:
                    prox_id = int(df_raw["ID"].astype(int).max() + 1)
                except:
                    prox_id = 1
                
                nueva_fila = pd.DataFrame([{
                    "ID": prox_id,
                    "Título": t,
                    "Fecha Creación": datetime.now().strftime("%d/%m/%Y"),
                    "Descripción": desc,
                    "Responsable": r,
                    "Prioridad": p,
                    "Fecha Est. Solución": f_est.strftime("%d/%m/%Y"),
                    "Estado": "Abierto",
                    "Comentarios": com
                }])
                
                df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, data=df_final)
                st.success(f"¡ODM #{prox_id} creada con éxito!")
                st.balloons()
                st.rerun()
            else:
                st.error("Por favor, completa el Título y selecciona un Responsable.")