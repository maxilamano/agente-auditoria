import streamlit as st
import sqlite3
import os
# Supongamos que usas LangChain para el RAG
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
# Nota: Configura tu proveedor de IA (OpenAI, Ollama, etc.) aquí

# ==========================================
# 1. CONFIGURACIÓN DE BASE DE DATOS (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS planes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto TEXT,
            metodo TEXT,
            plan_generado TEXT
        )
    ''')
    conn.commit()
    conn.close()

def guardar_plan(proyecto, metodo, plan):
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO planes (proyecto, metodo, plan_generado) VALUES (?, ?, ?)", (proyecto, metodo, plan))
    conn.commit()
    conn.close()

# Inicializar la BD al arrancar
init_db()

# ==========================================
# 2. INTERFAZ DE USUARIO (Streamlit)
# ==========================================
st.set_page_config(page_title="Auditor IA", layout="centered")

st.title("🛡️ Planificador de Auditoría de Software Inteligente")
st.markdown("Genera planes de auditoría basados en estándares internacionales (**ISO 25040, 12207, 14764**).")

# Formulario de entrada (Accesible y Responsivo automáticamente)
with st.form("formulario_auditoria"):
    nombre_proyecto = st.text_input("Nombre del Software / Proyecto a auditar:", placeholder="Ej. Sistema de Inventario Hospitalario")
    
    metodo_auditoria = st.selectbox(
        "Selecciona el Método de Auditoría principal:",
        ["Análisis Estático de Código", "Pruebas de Caja Negra (Funcionales)", "Evaluación de Arquitectura e Infraestructura"]
    )
    
    detalles = st.text_area("Requerimientos específicos o contexto adicional:")
    
    boton_generar = st.form_submit_button(label="Automatizar y Generar Plan")

# ==========================================
# 3. LÓGICA DE AUTOMATIZACIÓN + RAG + IA
# ==========================================
if boton_generar:
    if not nombre_proyecto:
        st.error("Por favor, introduce el nombre del proyecto.")
    else:
        with st.spinner("Consultando normativas y automatizando el diseño del plan..."):
            
            # --- PASO 1: DEMOSTRACIÓN DE RAG ---
            # En un entorno real, aquí cargarías tu FAISS index pré-entrenado con los PDFs de las ISO.
            # db = FAISS.load_local("faiss_index_normas", embeddings)
            # contexto_normas = db.similarity_search(metodo_auditoria, k=2)
            contexto_mock = "Norma ISO 12207 (Procesos del ciclo de vida), ISO 25040 (Evaluación de calidad de software) e ISO 14764 (Mantenimiento)."
            
            # --- PASO 2: AUTOMATIZACIÓN Y PROMPT PARA CUMPLIR LA RÚBRICA ---
            prompt = f"""
            Actúa como un Auditor de Software Senior. Genera un plan detallado para el proyecto: '{nombre_proyecto}'.
            
            Debes basarte estrictamente en este contexto normativo obtenido por RAG: {contexto_mock}
            Utiliza obligatoriamente el método: {metodo_auditoria}.
            Contexto del usuario: {detalles}
            
            Estructura el reporte incluyendo estrictamente:
            1. FASES DEL PROCESO DE AUDITORÍA (Planificación, Ejecución, Dictamen).
            2. REQUERIMIENTO DE EVALUACIÓN (Qué se va a medir y bajo qué criterios de las ISO).
            3. DISEÑO DE EVALUACIÓN (Herramientas, técnicas y pasos exactos para aplicar el método {metodo_auditoria}).
            """
            
            # --- PASO 3: LLAMADA AL SERVICIO DE IA ---
            # Aquí invocarías a tu LLM. Para la demo usaremos una simulación del output:
            plan_final = f"### Plan de Auditoría para {nombre_proyecto}\n\n**1. Estándares Aplicados:** Basado en {contexto_mock}\n\n**2. Fases de la Auditoría:** ... \n\n**3. Requerimiento y Diseño de Evaluación usando {metodo_auditoria}:** ..."
            
            # --- PASO 4: DEMOSTRACIÓN DE BASE DE DATOS (Guardado automático) ---
            guardar_plan(nombre_proyecto, metodo_auditoria, plan_final)
            
            # Mostrar resultado en pantalla
            st.success("¡Plan generado y almacenado con éxito en la Base de Datos!")
            st.markdown(plan_final)

# Historial almacenado en la BD para demostrar su uso en la demo en clase
st.divider()
st.subheader("📁 Historial de Planes Guardados (Base de Datos)")
conn = sqlite3.connect("auditorias.db")
cursor = conn.cursor()
cursor.execute("SELECT id, proyecto, metodo FROM planes ORDER BY id DESC")
registros = cursor.fetchall()
conn.close()

for reg in registros:
    st.write(f"ID {reg[0]} | **Proyecto:** {reg[1]} | **Método:** {reg[2]}")

#comentario de prueba