import streamlit as st
import sqlite3
import os
import ia_engine

# ==========================================
# 0. INICIALIZAR ESTADOS DE SESIÓN (UX)
# ==========================================
# Esto controla si mostramos el formulario ("nueva") o una auditoría ("id_del_historial")
if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "nueva"

def cambiar_vista(vista):
    """Función rápida para los botones que cambian la pantalla"""
    st.session_state.vista_actual = vista

# ==========================================
# 1. CONFIGURACIÓN DE BASE DE DATOS
# ==========================================
def init_db():
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS planes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto TEXT,
            metodo TEXT,
            origen_tipo TEXT,
            ruta_codigo TEXT,
            plan_generado TEXT
        )
    ''')
    conn.commit()
    conn.close()

def guardar_plan(proyecto, metodo, origen_tipo, ruta_codigo, plan):
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO planes (proyecto, metodo, origen_tipo, ruta_codigo, plan_generado) VALUES (?, ?, ?, ?, ?)", 
        (proyecto, metodo, origen_tipo, ruta_codigo, plan)
    )
    nuevo_id = cursor.lastrowid # Guardamos el ID recién creado para poder visualizarlo inmediatamente
    conn.commit()
    conn.close()
    return nuevo_id

init_db()

# ==========================================
# 2. INTERFAZ DE USUARIO: BARRA SUPERIOR
# ==========================================
st.set_page_config(page_title="Auditor IA", layout="wide")

# Construimos la barra superior con columnas
top_col1, top_col2 = st.columns([4, 1])

with top_col1:
    st.title("🛡️ Planificador de Auditoría de Software")
    st.markdown("Basado en estándares internacionales **ISO 25040, 12207, 14764**")

with top_col2:
    # Alinear el botón verticalmente para que quede bien posicionado
    st.write("") 
    st.write("")
    if st.button("🔄 Sincronizar RAG (Normas)", use_container_width=True):
        with st.spinner("Re-indexando documentos..."):
            msg = ia_engine.indexar_normativas()
            st.toast(msg, icon="✅") # st.toast muestra un mensaje sutil estilo notificación

st.divider() # Línea delimitadora superior

# ==========================================
# 3. ESTRUCTURA PRINCIPAL (Centro y Derecha)
# ==========================================
# Columna principal (3/4 partes) y Columna lateral derecha (1/4 parte)
col_principal, col_derecha = st.columns([3, 1], gap="large")

# ------------------------------------------
# LATERAL DERECHO (Historial / Menú)
# ------------------------------------------
with col_derecha:
    # Botón principal para volver al formulario
    st.button("➕ Nueva Auditoría", type="primary", use_container_width=True, on_click=cambiar_vista, args=("nueva",))
    
    st.markdown("### 📁 Historial de Auditorías")
    
    # Consultamos solo los datos necesarios para los botones
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, proyecto FROM planes ORDER BY id DESC")
    registros = cursor.fetchall()
    conn.close()
    
    # Creamos un botón por cada auditoría guardada
    if registros:
        for reg in registros:
            id_registro = reg[0]
            nombre = reg[1]
            
            # Botón en lista. Si se presiona, cambia 'vista_actual' al ID correspondiente
            st.button(f"📄 {nombre}", key=f"btn_historial_{id_registro}", use_container_width=True, on_click=cambiar_vista, args=(id_registro,))
    else:
        st.caption("Aún no hay auditorías registradas.")

# ------------------------------------------
# ÁREA PRINCIPAL (Formulario o Resultados)
# ------------------------------------------
with col_principal:
    
    # CASO A: EL USUARIO QUIERE CREAR UNA NUEVA AUDITORÍA
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

        # Lógica al presionar "Generar"
        if boton_generar:
            if not nombre_proyecto or not origen_input:
                st.error("❌ Completa todos los campos.")
            else:
                with st.spinner("🧠 Procesando código e IA..."):
                    try:
                        informe_final = ia_engine.generar_auditoria_completa(
                            nombre_proyecto, metodo_auditoria, tipo_origen, origen_input
                        )
                        # Guardamos y capturamos el nuevo ID
                        nuevo_id = guardar_plan(nombre_proyecto, metodo_auditoria, tipo_origen, origen_input, informe_final)
                        
                        # Cambiamos la vista inmediatamente a la auditoría recién creada
                        st.session_state.vista_actual = nuevo_id
                        st.rerun() # Fuerza a recargar la pantalla
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # CASO B: EL USUARIO QUIERE VER UNA AUDITORÍA PASADA
    else:
        # Recuperamos la información usando el ID almacenado en la sesión
        id_actual = st.session_state.vista_actual
        
        conn = sqlite3.connect("auditorias.db")
        cursor = conn.cursor()
        cursor.execute("SELECT proyecto, metodo, origen_tipo, ruta_codigo, plan_generado FROM planes WHERE id = ?", (id_actual,))
        datos = cursor.fetchone()
        conn.close()
        
        if datos:
            st.subheader(f"📌 Informe: {datos[0]}")
            st.caption(f"**Método:** {datos[1]} | **Origen:** {datos[2]} ({datos[3]})")
            st.divider()
            st.markdown(datos[4]) # Mostramos el informe markdown
        else:
            st.warning("No se pudo cargar la auditoría solicitada.")