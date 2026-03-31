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
        - La columna 'comment' contiene lenguaje natural; usa LIKE o filtros de texto para búsquedas semánticas.
        - Para saber quién es el usuario con más reviews, agrupa por 'user_id'.
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
                
                # Log tokens to file
                with open("token_usage.txt", "a") as f:
                    f.write(f"--- SQL AGENT ---\n")
                    f.write(f"Question: {question[:50]}...\n")
                    f.write(f"Total Tokens: {cb.total_tokens}\n")
                    f.write(f"Prompt Tokens: {cb.prompt_tokens}\n")
                    f.write(f"Completion Tokens: {cb.completion_tokens}\n")
                    f.write(f"Total Cost (USD): ${cb.total_cost:.6f}\n\n")

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
