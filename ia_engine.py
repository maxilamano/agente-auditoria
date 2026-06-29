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
    
    # Carpetas que no aportan a la auditoría core y solo consumen tokens
    carpetas_ignoradas = {'.git', 'node_modules', 'build', 'vendor', 'third_party', 'tests', 'docs', 'assets', 'public'}
    
    if not os.path.exists(ruta_carpeta):
        return "Ruta de código no válida o inexistente."
        
    for raiz, carpetas, archivos in os.walk(ruta_carpeta):
        # Filtrar carpetas basura en tiempo real para no entrar en ellas
        carpetas[:] = [d for d in carpetas if d not in carpetas_ignoradas]
        
        for archivo in archivos:
            if archivo.endswith(extensiones_validas):
                ruta_completa = os.path.join(raiz, archivo)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        
                        # Extraer solo una muestra representativa de cada archivo (ej. 2500 caracteres)
                        # Esto permite meter muchos más archivos diferentes en el contexto de la IA
                        if len(contenido) > 2500:
                            contenido = contenido[:2500] + "\n...[CÓDIGO TRUNCADO POR TAMAÑO]..."
                            
                        codigo_consolidado += f"\n\n--- ARCHIVO: {archivo} ---\n"
                        codigo_consolidado += contenido
                        
                        # Si ya tenemos un paneo general enorme, detenemos la extracción
                        if len(codigo_consolidado) > 35000:
                            return codigo_consolidado
                except Exception:
                    continue
                    
    return codigo_consolidado

# ==========================================
# 4. FLUJO PRINCIPAL AUDITORÍA
# ==========================================
def forzar_borrado(func, path, exc_info):
    """Función auxiliar para quitar el 'Solo lectura' de los archivos de Git en Windows."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

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
                # Usamos el fix de Windows en caso de error
                shutil.rmtree(carpeta_temporal, onerror=forzar_borrado)
            return f"Error crítico al intentar clonar desde GitHub: {str(e)}"

    # Procesar la lectura de archivos
    codigo_proyecto = leer_codigo_fuente(directorio_a_leer)
    
    # Limpieza inmediata si usamos GitHub para liberar espacio (FIX WINDOWS APLICADO)
    if carpeta_temporal and os.path.exists(carpeta_temporal):
        shutil.rmtree(carpeta_temporal, onerror=forzar_borrado)

    if not codigo_proyecto or len(codigo_proyecto.strip()) == 0:
        return "No se detectó código fuente analizable (revisa las extensiones de tus archivos)."

    # Configurar el texto que se inyectará en el prompt
    origen_texto = f"Repositorio Remoto de GitHub ({ruta_o_url})" if origen_tipo == "Repositorio GitHub" else f"Directorio Local ({ruta_o_url})"

    # Prompt técnico con reglas estrictas de Markdown y formato
    template = """
    Actúa como un Auditor de Software e Ingeniero de Calidad de Código Senior. Acabas de terminar de inspeccionar el código del proyecto.
    
    PROYECTO A AUDITAR: {proyecto}
    ORIGEN DEL SOFTWARE: {origen}
    MÉTODO DE AUDITORÍA: {metodo}
    
    CONTEXTO NORMATIVO (RAG):
    {normas}
    
    CÓDIGO FUENTE REAL ANALIZADO:
    {codigo}
    
    REGLAS DE FORMATO ESTRICTAS:
    1. Usa Markdown válido. Escribe los títulos con ## y usa viñetas (*) para listar elementos.
    2. Si vas a sugerir o mostrar código, DEBES usar bloques de código con saltos de línea correctos (ejemplo: ```cpp ... ```). No escribas código en una sola línea.
    3. Usa negritas (**) para destacar nombres de archivos, funciones o vulnerabilidades.
    4. HABLA EN PRESENTE O PASADO. Estás entregando los resultados, no proponiendo lo que vas a hacer.
    
    Genera el informe técnico estructurado estrictamente en ESPAÑOL bajo las siguientes secciones:
    
    ## 1. FASES EN EL PROCESO DE AUDITORÍA DE SOFTWARE
    * **Planificación Ejecutada:** Describe qué herramientas y enfoque utilizaste para procesar este código en específico bajo el método {metodo}.
    * **Ejecución:** Detalla qué partes del código (archivos/funciones que leíste) sometiste a evaluación.
    * **Dictamen Final:** Entrega un veredicto claro (Aprobado, Aprobado con Observaciones, o Rechazado) basándote en la calidad del código.
    
    ## 2. REQUERIMIENTO DE EVALUACIÓN
    Mapea características específicas de las normas ISO del RAG (ej. Mantenibilidad, Seguridad, Eficiencia) contra el código. Cita **obligatoriamente** variables, clases o funciones reales del código que demuestren fallos o aciertos tangibles.
    
    ## 3. DISEÑO DE EVALUACIÓN
    Presenta la metodología técnica usada. Detalla qué vulnerabilidades específicas se buscaron en ESTE código fuente. Si escribes un ejemplo de prueba unitaria para arreglar las funciones deficientes, formatea el bloque de código correctamente.
    """
    
    prompt = PromptTemplate.from_template(template)
    
    prompt_final = prompt.format(
        proyecto=nombre_proyecto,
        origen=origen_texto,
        metodo=metodo,
        normas=contexto_normas,
        codigo=codigo_proyecto 
    )
    
    respuesta = llm.invoke(prompt_final)
    return respuesta

if __name__ == "__main__":
    print("--- INICIANDO PRUEBA LOCAL DEL MOTOR DE IA ---")
    resultado = indexar_normativas()
    print(resultado)