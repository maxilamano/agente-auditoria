import streamlit as st
import os
import ia_engine
import database

# ==========================================
# 0. INICIALIZAR ESTADOS DE SESIÓN (UX)
# ==========================================
if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "nueva"

def cambiar_vista(vista):
    """Función rápida para los botones que cambian la pantalla"""
    st.session_state.vista_actual = vista

# ==========================================
# 1. INICIALIZAR BASE DE DATOS
# ==========================================
database.init_db()

# ==========================================
# 2. INTERFAZ DE USUARIO: BARRA SUPERIOR
# ==========================================
st.set_page_config(page_title="Auditor IA", layout="wide")

top_col1, top_col2 = st.columns([4, 1])

with top_col1:
    st.title("🛡️ Planificador de Auditoría de Software")
    st.markdown("Basado en estándares internacionales **ISO 25040, 12207, 14764**")

with top_col2:
    st.write("") 
    st.write("")
    if st.button("🔄 Sincronizar RAG (Normas)", use_container_width=True):
        with st.spinner("Re-indexando documentos..."):
            msg = ia_engine.indexar_normativas()
            st.toast(msg, icon="✅")

st.divider()

# ==========================================
# 3. ESTRUCTURA PRINCIPAL (Centro y Derecha)
# ==========================================
col_principal, col_derecha = st.columns([3, 1], gap="large")

# ------------------------------------------
# LATERAL DERECHO (Historial / Menú)
# ------------------------------------------
with col_derecha:
    st.button("➕ Nueva Auditoría", type="primary", use_container_width=True, on_click=cambiar_vista, args=("nueva",))
    
    st.markdown("### 📁 Historial de Auditorías")
    
    # Consultamos los datos usando nuestra función modular
    registros = database.obtener_historial_basico()
    
    if registros:
        for reg in registros:
            id_registro = reg[0]
            nombre = reg[1]
            st.button(f"📄 {nombre}", key=f"btn_historial_{id_registro}", use_container_width=True, on_click=cambiar_vista, args=(id_registro,))
    else:
        st.caption("Aún no hay auditorías registradas.")

# ------------------------------------------
# ÁREA PRINCIPAL (Formulario o Resultados)
# ------------------------------------------
with col_principal:
    
    if st.session_state.vista_actual == "nueva":
        st.subheader("📝 Configuración de Nueva Auditoría")
        
        tipo_origen = st.radio(
            "Selecciona el origen del código fuente:",
            ["Carpeta Local", "Repositorio GitHub"],
            horizontal=True
        )
        
        with st.form("formulario_auditoria"):
            nombre_proyecto = st.text_input("Nombre del Proyecto:", placeholder="Ej. Sistema de Gestión")
            metodo_auditoria = st.selectbox(
                "Método de Auditoría principal:",
                [
                    "Análisis Estático de Código", 
                    "Pruebas de Caja Negra (Funcionales)", 
                    "Evaluación de Arquitectura e Infraestructura",
                    "Inspecciones y Recorridos Formales"
                ]
            )
            
            if tipo_origen == "Carpeta Local":
                origen_input = st.text_input("Ruta absoluta de la carpeta:")
            else:
                origen_input = st.text_input("URL del repositorio público de GitHub:")
                
            boton_generar = st.form_submit_button(label="🚀 Procesar y Generar Informe")

        if boton_generar:
            if not nombre_proyecto or not origen_input:
                st.error("❌ Completa todos los campos.")
            else:
                # Actualicé el texto del spinner para reflejar la carga en el Acer
                with st.spinner("🧠 Procesando código e IA... Esto tomará un momento."):
                    try:
                        informe_final = ia_engine.generar_auditoria_completa(
                            nombre_proyecto, metodo_auditoria, tipo_origen, origen_input
                        )
                        # Guardamos llamando al módulo database
                        nuevo_id = database.guardar_plan(nombre_proyecto, metodo_auditoria, tipo_origen, origen_input, informe_final)
                        
                        st.session_state.vista_actual = nuevo_id
                        st.rerun() 
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    else:
        id_actual = st.session_state.vista_actual
        
        # Obtenemos los detalles de la auditoría llamando al módulo database
        datos = database.obtener_auditoria_por_id(id_actual)
        
        if datos:
            st.subheader(f"📌 Informe: {datos[0]}")
            st.caption(f"**Método:** {datos[1]} | **Origen:** {datos[2]} ({datos[3]})")
            st.divider()
            st.markdown(datos[4])
        else:
            st.warning("No se pudo cargar la auditoría solicitada.")