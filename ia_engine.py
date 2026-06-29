import os
import shutil
import tempfile
import stat
from git import Repo
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS Y MODELOS LOCALES
# ==========================================
DOCS_DIR = "./documentos_normas"
CHROMA_DIR = "./chroma_db"
MODEL_NAME = "qwen2.5-coder:7b"

print("[INFO] Cargando modelo de embeddings local...")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5") 
llm = OllamaLLM(model=MODEL_NAME, temperature=0.2)

# ==========================================
# 2. FUNCIÓN PARA ACTUALIZAR EL RAG
# ==========================================
def indexar_normativas():
    if not os.path.exists(DOCS_DIR) or not os.listdir(DOCS_DIR):
        return "La carpeta de normativas está vacía o no existe."
    if os.path.exists(CHROMA_DIR):
        try:
            shutil.rmtree(CHROMA_DIR)
        except Exception as e:
            return f"Error al limpiar la base de datos antigua: {str(e)}"
        
    print("[INFO] Leyendo y extrayendo texto de los PDFs de normativas...")
    loader = DirectoryLoader(DOCS_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documentos = loader.load()
    
    if not documentos:
        return "No se pudo extraer texto de los documentos."
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=250)
    fragmentos = text_splitter.split_documents(documentos)
    
    Chroma.from_documents(fragmentos, embeddings, persist_directory=CHROMA_DIR)
    return f"Sincronización exitosa. Se indexaron {len(fragmentos)} fragmentos."

# ==========================================
# 3. LÓGICA PARA LEER CÓDIGO FUENTE
# ==========================================
def leer_codigo_fuente(ruta_carpeta):
    codigo_consolidado = ""
    extensiones_validas = ('.py', '.js', '.ts', '.cs', '.java', '.cpp', '.c', '.h', '.html', '.css', '.gml', '.php')
    
    if not os.path.exists(ruta_carpeta):
        return "Ruta de código no válida o inexistente."
        
    for raiz, _, archivos in os.walk(ruta_carpeta):
        for archivo in archivos:
            if archivo.endswith(extensiones_validas):
                ruta_completa = os.path.join(raiz, archivo)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        codigo_consolidado += f"\n\n--- ARCHIVO: {archivo} ---\n"
                        codigo_consolidado += f.read()
                except Exception:
                    continue
                    
    return codigo_consolidado

# ==========================================
# 4. FLUJO PRINCIPAL AUDITORÍA
# ==========================================
def generar_auditoria_completa(nombre_proyecto, metodo, origen_tipo, ruta_o_url):
    # 1. RAG
    contexto_normas = ""
    if os.path.exists(CHROMA_DIR):
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        docs_relevantes = db.similarity_search(metodo, k=3)
        contexto_normas = "\n".join([doc.page_content for doc in docs_relevantes])
    else:
        contexto_normas = "No hay normas ISO indexadas en el sistema actualmente."

    # 2. Obtener el código fuente según la opción elegida
    directorio_a_leer = ruta_o_url
    carpeta_temporal = None

    if origen_tipo == "Repositorio GitHub":
        print(f"[INFO] Clonando repositorio remoto: {ruta_o_url}")
        carpeta_temporal = tempfile.mkdtemp(prefix="auditoria_git_")
        try:
            Repo.clone_from(ruta_o_url, carpeta_temporal, depth=1)
            directorio_a_leer = carpeta_temporal
        except Exception as e:
            if carpeta_temporal and os.path.exists(carpeta_temporal):
                shutil.rmtree(carpeta_temporal)
            return f"Error crítico al intentar clonar desde GitHub: {str(e)}. Verifica que el repositorio sea público y la URL sea correcta."

    # Procesar la lectura de archivos
    codigo_proyecto = leer_codigo_fuente(directorio_a_leer)
    
    # Limpieza inmediata si usamos GitHub para liberar espacio
    if carpeta_temporal and os.path.exists(carpeta_temporal):
        shutil.rmtree(carpeta_temporal)

    if not codigo_proyecto or len(codigo_proyecto.strip()) == 0:
        return "No se detectó código fuente analizable (revisa las extensiones de tus archivos)."

    # Configurar el texto que se inyectará en el prompt
    origen_texto = f"Repositorio Remoto de GitHub ({ruta_o_url})" if origen_tipo == "Repositorio GitHub" else f"Directorio Local ({ruta_o_url})"

    # Prompt técnico e imperativo riguroso
    template = """
    Actúa como un Auditor de Software e Ingeniero de Calidad de Código Senior. Tu único objetivo es inspeccionar el código provisto de forma crítica y severa.
    
    PROYECTO A AUDITAR: {proyecto}
    ORIGEN DEL SOFTWARE: {origen}
    MÉTODO DE AUDITORÍA: {metodo}
    
    CONTEXTO NORMATIVO (RAG):
    {normas}
    
    CÓDIGO FUENTE REAL A ANALIZAR (Inspecciona la sintaxis, funciones y lógica aquí descritas):
    {codigo}
    
    INSTRUCCIONES CRÍTICAS: 
    - No te limites a describir qué hace el programa. Debes evaluar su calidad técnica real.
    - Debes buscar activamente bugs, malas prácticas, vulnerabilidades o áreas de mejora en el código provisto.
    - Es obligatorio citar nombres de funciones, variables o tablas reales del código analizado para demostrar que lo leíste de verdad.
    
    Genera el informe técnico estructurado estrictamente en ESPAÑOL bajo las siguientes secciones:
    
    ## 1. FASES EN EL PROCESO DE AUDITORÍA DE SOFTWARE
    (Establece un cronograma real de cómo aplicarías la Planificación, Ejecución y Dictamen específicamente sobre este código usando el método {metodo}).
    
    ## 2. REQUERIMIENTO DE EVALUACIÓN
    (Menciona características específicas de las normas ISO del RAG, por ejemplo, Mantenibilidad, Seguridad o Portabilidad, y evalúa cómo puntúa el código fuente provisto en ellas. Identifica fallas tangibles).
    
    ## 3. DISEÑO DE EVALUACIÓN
    (Presenta un diseño de pruebas técnicas aplicables a ESTE código fuente. Si elegiste Análisis Estático, detalla qué herramientas de software como Linters o SonarQube usarías, y qué funciones específicas del código deberían ser vigiladas de cerca).
    """
    
    prompt = PromptTemplate.from_template(template)
    
    # CORRECCIÓN AQUÍ: Se mapea 'origen' directamente a la variable 'origen_texto'
    prompt_final = prompt.format(
        proyecto=nombre_proyecto,
        origen=origen_texto,
        metodo=metodo,
        normas=contexto_normas,
        codigo=codigo_proyecto[:30000]
    )
    
    respuesta = llm.invoke(prompt_final)
    return respuesta

if __name__ == "__main__":
    print("--- INICIANDO PRUEBA LOCAL DEL MOTOR DE IA ---")
    resultado = indexar_normativas()
    print(resultado)