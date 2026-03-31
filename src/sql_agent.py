import os
import pandas as pd
import sqlite3
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.callbacks import get_openai_callback

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EXCEL_FILE = "bank_reviews_colombia (1).xlsx"
if not os.path.exists(EXCEL_FILE) and os.path.exists(os.path.join("..", EXCEL_FILE)):
    EXCEL_FILE = os.path.join("..", EXCEL_FILE)

DB_FILE = "bank_reviews.db"
if not os.path.exists(DB_FILE) and os.path.exists(os.path.join("..", DB_FILE)):
    DB_FILE = os.path.join("..", DB_FILE)
TABLE_NAME = "reviews"
LLM_MODEL = "gpt-4.1-mini"
DATA_DICTIONARY = """
DICCIONARIO DE DATOS (TABLA 'reviews'):
- branch_id (TEXT): Código identificador único de la sucursal bancaria. Ejemplo: 'BOG-CHAPINERO-01'. 'MED-POBLADO-01'
- user_id (TEXT): Código identificador único del usuario que realizó la reseña. Ejemplo: 'user_1'.
- comment (TEXT): Comentario o reseña en LENGUAJE NATURAL sobre el servicio. Ejemplo: 'Muy demorado el servicio en caja.'.
"""

# ---------------------------------------------------------------------------
# Database Setup
# ---------------------------------------------------------------------------
def setup_database():
    """
    Convierte el archivo Excel a una base de datos SQLite.
    """
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: No se encontró el archivo {EXCEL_FILE}")
        return

    # Leer el archivo Excel
    df = pd.read_excel(EXCEL_FILE)
    
    # Limpiar nombres de columnas (si es necesario)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Guardar en SQLite
    conn = sqlite3.connect(DB_FILE)
    df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.close()
    print(f"Base de datos {DB_FILE} creada exitosamente desde {EXCEL_FILE}")

# ---------------------------------------------------------------------------
# SQLAgent Class
# ---------------------------------------------------------------------------
class SQLAgent:
    def __init__(self, db_path: str = DB_FILE, llm_model: str = LLM_MODEL):
        """
        Inicializa el agente experto en SQL.
        """
        if not os.environ.get("OPENAI_API_KEY"):
            raise EnvironmentError("OPENAI_API_KEY no se encuentra en las variables de entorno.")

        # Asegurar que la DB existe
        if not os.path.exists(db_path):
            setup_database()

        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        self.llm = ChatOpenAI(model=llm_model, temperature=0)

        # Definir la estructura de datos para que la clase sea "consciente"
        self.data_dictionary = DATA_DICTIONARY
        
        # Prompt personalizado para guiar al agente con conocimiento de la estructura
        custom_suffix = f"""
            {self.data_dictionary}

            INSTRUCCIONES CRÍTICAS:
            - Si el usuario pregunta por 'usuarios', 'sucursales' o 'comentarios', busca siempre en la tabla 'reviews'.
            - La tabla 'reviews' es la única fuente de datos. No intentes buscar en tablas como 'users' o 'branches'.
            - La columna 'comment' contiene lenguaje natural; usa LIKE o filtros de texto cuando sea útil para búsquedas textuales.
            - Antes de afirmar que algo es 'el que más', 'el único', 'el mejor', 'el peor', o cualquier superlativo, verifica si hay empates.
            - No respondas con falsa certeza si varias entidades comparten el mismo valor máximo o mínimo.
            - Si hay empate en el primer lugar, indícalo explícitamente.
            - Si todos los valores relevantes son iguales, indícalo explícitamente.
            - Evita usar `ORDER BY ... LIMIT 1` por sí solo cuando la pregunta implique liderazgo, ranking o máximos, porque puede ocultar empates.
            - Para preguntas como 'quién es el usuario con más reviews', primero calcula el conteo por `user_id` y luego verifica cuántos usuarios comparten el máximo.
            - Si el resultado no permite identificar un único ganador, responde diciendo que hay empate o que no existe uno solo.
            - La respuesta final debe ser fiel a los datos y expresar incertidumbre cuando corresponda.

            GUÍA DE INTERPRETACIÓN:
            - Si una consulta devuelve una sola fila por uso de `LIMIT 1`, no asumas automáticamente que esa fila representa un único máximo global sin verificar empates.
            - Si varias filas tienen el mismo conteo máximo, responde con lenguaje como:
            'Hay un empate entre ...'
            'No hay un único usuario con más reseñas.'
            'Todos los usuarios tienen la misma cantidad de reseñas.'
            - Si todos los usuarios tienen exactamente 1 reseña, no digas 'el usuario con más reseñas es X'; di que no hay un único usuario con más reseñas porque todos tienen 1.

            PATRONES RECOMENDADOS:
            - Para máximos con posible empate, prefiere consultas del tipo:
            WITH counts AS (
                SELECT user_id, COUNT(*) AS review_count
                FROM reviews
                GROUP BY user_id
            )
            SELECT user_id, review_count
            FROM counts
            WHERE review_count = (SELECT MAX(review_count) FROM counts);

            - Para mínimos con posible empate, usa la misma lógica con MIN(...).

            """

        # Crear el agente de SQL con instrucciones extra
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="openai-tools",
            verbose=True,
            suffix=custom_suffix
        )

    def query(self, config: dict) -> str:
        """
        Ejecuta una consulta en lenguaje natural sobre la base de datos de reviews.
        Compatible con el formato del orquestador.
        """
        question = config.get("question", "")
        if not question:
            return "No se proporcionó ninguna pregunta."

        try:
            # El agente maneja la lógica de generar SQL, ejecutarlo y responder con monitoreo
            with get_openai_callback() as cb:
                response = self.agent_executor.invoke({"input": question})
                
                # Log tokens (try file, fallback to console if read-only)
                try:
                    with open("token_usage.txt", "a") as f:
                        f.write(f"--- SQL AGENT ---\n")
                        f.write(f"Question: {question[:50]}...\n")
                        f.write(f"Total Tokens: {cb.total_tokens}\n")
                        f.write(f"Prompt Tokens: {cb.prompt_tokens}\n")
                        f.write(f"Completion Tokens: {cb.completion_tokens}\n")
                        f.write(f"Total Cost (USD): ${cb.total_cost:.6f}\n\n")
                except (IOError, OSError):
                    print(f"--- SQL AGENT ---")
                    print(f"Question: {question[:50]}...")
                    print(f"Total Tokens: {cb.total_tokens}")
                    print(f"Prompt Tokens: {cb.prompt_tokens}")
                    print(f"Completion Tokens: {cb.completion_tokens}")
                    print(f"Total Cost (USD): ${cb.total_cost:.6f}")

            return response["output"]
        except Exception as e:
            return f"Hubo un error al procesar tu consulta SQL: {str(e)}"

# ---------------------------------------------------------------------------
# CLI Usage Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = SQLAgent()
    
    test_questions = [
        # "¿Quién es el usuario que más reviews ha realizado?",
        "Qué dicen las reseñas sobre el tiempo de espera?",
        # "¿Cuántas reviews hay en total?",
        # "Dime el comentario que hizo el usuario 'user_5' sobre la sucursal 'BOG-SUBA-02'"
    ]
    
    for q in test_questions:
        print(f"\nPregunta: {q}")
        answer = agent.query({"question": q})
        print(f"Respuesta:\n{answer}")
