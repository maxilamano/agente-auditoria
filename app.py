import streamlit as st
import sqlite3
import os
import ia_engine  # Importamos tu motor de IA corregido

# ==========================================
# 1. CONFIGURACIÓN DE BASE DE DATOS (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    # Aseguramos la estructura completa con origen_tipo incluido
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
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. INTERFAZ DE USUARIO (Streamlit)
# ==========================================
st.set_page_config(page_title="Auditor IA", layout="wide")

st.title("🛡️ Planificador de Auditoría de Software Inteligente")
st.markdown("Genera informes completos basados en estándares internacionales (**ISO 25040, 12207, 14764**) desde repositorios locales o GitHub.")

col_form, col_historial = st.columns([2, 1])

with col_form:
    st.subheader("📝 Configuración de la Auditoría")
    
    with st.form("formulario_auditoria"):
        nombre_proyecto = st.text_input("Nombre del Software / Proyecto a auditar:", placeholder="Ej. Sistema de Gestión Escolar")
        
        metodo_auditoria = st.selectbox(
            "Selecciona el Método de Auditoría principal:",
            [
                "Análisis Estático de Código", 
                "Pruebas de Caja Negra (Funcionales)", 
                "Evaluación de Arquitectura e Infraestructura",
                "Inspecciones y Recorridos Formales"
            ]
        )
        
        st.write("---")
        tipo_origen = st.radio(
            "Selecciona el origen del código fuente:",
            ["Carpeta Local", "Repositorio GitHub"],
            horizontal=True
        )
        
        if tipo_origen == "Carpeta Local":
            origen_input = st.text_input(
                "Ruta absoluta de la carpeta en tu computadora:", 
                placeholder="Ej. C:\\Users\\tu_usuario\\Documents\\mi_codigo"
            )
        else:
            origen_input = st.text_input(
                "URL pública del repositorio de GitHub:", 
                placeholder="Ej. https://github.com/usuario/proyecto.git"
            )
            st.caption("⚠️ Nota: El repositorio de GitHub debe ser público para que la IA lo pueda clonar sin credenciales.")
            
        boton_generar = st.form_submit_button(label="🚀 Automatizar y Generar Auditoría")

    # ==========================================
    # 3. ACCIÓN AL PRESIONAR EL BOTÓN
    # ==========================================
    if boton_generar:
        if not nombre_proyecto or not origen_input:
            st.error("❌ Por favor, completa todos los campos del formulario.")
        elif tipo_origen == "Carpeta Local" and not os.path.exists(origen_input):
            st.error("❌ La ruta de la carpeta de código provista no existe en tu computadora.")
        elif tipo_origen == "Repositorio GitHub" and not origen_input.startswith("http"):
            st.error("❌ Por favor, ingresa una URL de GitHub válida.")
        else:
            with st.spinner("🧠 Procesando código y consultando el RAG local... Esto tomará un momento."):
                try:
                    # Enviamos los parámetros correspondientes al engine
                    informe_final = ia_engine.generar_auditoria_completa(
                        nombre_proyecto, 
                        metodo_auditoria, 
                        tipo_origen,
                        origen_input
                    )
                    
                    # Guardar en SQLite de forma automatizada
                    guardar_plan(nombre_proyecto, metodo_auditoria, tipo_origen, origen_input, informe_final)
                    
                    st.success("🎉 ¡Auditoría generada con éxito y almacenada de forma persistente!")
                    st.markdown("### 📋 Informe Técnico Generado")
                    st.markdown(informe_final)
                    
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar con la IA: {str(e)}")

# ==========================================
# 4. PANEL LATERAL: HISTORIAL
# ==========================================
with col_historial:
    st.subheader("📁 Historial (SQLite)")
    
    if st.button("🔄 Sincronizar / Actualizar RAG de Normas"):
        with st.spinner("Re-indexando documentos..."):
            msg = ia_engine.indexar_normativas()
            st.success(msg)
            
    st.divider()
    
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, proyecto, metodo, origen_tipo FROM planes ORDER BY id DESC")
    registros = cursor.fetchall()
    conn.close()
    
    if registros:
        for reg in registros:
            icono = "💻" if reg[3] == "Carpeta Local" else "🐙"
            with st.expander(f"ID {reg[0]}: {icono} {reg[1]}"):
                st.write(f"**Método:** {reg[2]}")
                st.write(f"**Origen:** {reg[3]}")
                
                conn_view = sqlite3.connect("auditorias.db")
                cur_view = conn_view.cursor()
                cur_view.execute("SELECT plan_generado FROM planes WHERE id = ?", (reg[0],))
                plan_txt = cur_view.fetchone()[0]
                conn_view.close()
                st.markdown(plan_txt[:500] + "...\n\n*(Vista previa)*")
    else:
        st.info("No hay auditorías previas registradas.")