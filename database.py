import sqlite3

def init_db():
    """Crea la base de datos y la tabla si no existen."""
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
    """Guarda una nueva auditoría y devuelve el ID generado."""
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO planes (proyecto, metodo, origen_tipo, ruta_codigo, plan_generado) VALUES (?, ?, ?, ?, ?)", 
        (proyecto, metodo, origen_tipo, ruta_codigo, plan)
    )
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return nuevo_id

def obtener_historial_basico():
    """Obtiene los IDs y nombres de proyecto para poblar la barra lateral."""
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, proyecto FROM planes ORDER BY id DESC")
    registros = cursor.fetchall()
    conn.close()
    return registros

def obtener_auditoria_por_id(id_auditoria):
    """Obtiene todos los detalles de una auditoría para mostrarla en pantalla."""
    conn = sqlite3.connect("auditorias.db")
    cursor = conn.cursor()
    cursor.execute("SELECT proyecto, metodo, origen_tipo, ruta_codigo, plan_generado FROM planes WHERE id = ?", (id_auditoria,))
    datos = cursor.fetchone()
    conn.close()
    return datos