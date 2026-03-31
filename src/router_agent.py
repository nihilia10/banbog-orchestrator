"""
router_agent.py 
Este módulo define un agente que actúa como un enrutador (router) inteligente.
Su función principal es analizar la pregunta del usuario y determinar qué fuente de datos (source_tag)
es la más adecuada para responderla en el sistema RAG.

Fuentes disponibles:
- 'products': Información sobre portafolios, beneficios de tarjetas de crédito y cuentas.
- 'reviews': Opiniones, quejas y comentarios de clientes.
- 'bre-b': Documentación técnica y arquitectura del sistema BRE-B.
"""

import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_community.callbacks import get_openai_callback

load_dotenv()
# ---------------------------------------------------------------------------
# Fuentes de datos y sus descripciones
# ---------------------------------------------------------------------------
SOURCES = {
    "products": "Información sobre productos bancarios, beneficios de tarjetas, tipos de cuentas y servicios generales del banco.",
    "reviews": "Feedback de clientes, opiniones sobre el servicio, quejas y comentarios sobre la experiencia del usuario.",
    "bre-b": "Especificaciones técnicas, arquitectura de software, diagramas, componentes y reglas de negocio del sistema BRE-B.",
    "clarify": "Se usa cuando la pregunta es ambigua, insuficiente, fuera de contexto o no se puede decidir con confianza a qué base de datos mandarla."
}

# ---------------------------------------------------------------------------
# Estructura de salida del Router
# ---------------------------------------------------------------------------
class RouterDecision(BaseModel):
    source_tag: str = Field(description="El tag de la fuente de datos elegida (products, reviews, bre-b o clarify)")
    next_agent: str = Field(description="El agente que procesará la consulta: 'sql' (solo para reviews estructurado), 'rag' (para conceptual) o 'none' (solo si source_tag es clarify)")
    reasoning: str = Field(description="Explicación breve de por qué se eligió esta fuente y estrategia")

# ---------------------------------------------------------------------------
# Clase RouterAgent
# ---------------------------------------------------------------------------
class RouterAgent:
    def __init__(self, model: str = "gpt-4.1-nano", temperature: float = 0):
        """
        Inicializa el Router Agent.
        """
        if not os.environ.get("OPENAI_API_KEY"):
            raise EnvironmentError("OPENAI_API_KEY no encontrada en las variables de entorno.")

        self.model_name = model
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.parser = JsonOutputParser(pydantic_object=RouterDecision)
        
        # Construimos el prompt para el enrutamiento
        sources_desc = "\n".join([f"- {tag}: {desc}" for tag, desc in SOURCES.items()])
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                    "Eres un asistente experto en enrutamiento de consultas para un sistema con tres fuentes: "
                    "'products', 'reviews' y 'bre-b'. "
                    "Tu tarea es decidir cuál fuente usar ('source_tag') y cuál agente debe continuar ('next_agent').\n\n"

                    "Fuentes disponibles:\n"
                    "{sources_description}\n\n"

                    "Reglas generales:\n"
                    "1. Analiza cuidadosamente la intención de la pregunta.\n"
                    "2. Selecciona el 'source_tag' más relevante.\n"
                    "3. El agente 'sql' SOLO puede usarse con la fuente 'reviews'.\n"
                    "4. Para 'products' y 'bre-b', usa SIEMPRE 'rag'.\n\n"

                    "Reglas específicas para 'reviews':\n"
                    "- Usa 'sql' si la pregunta requiere datos exactos, estructurados o agregados provenientes de la base de reseñas.\n"
                    "- Esto incluye preguntas sobre conteos, cantidades, rankings, existencia de registros, filtros por ciudad, sucursal, usuario, fecha, o búsquedas exactas.\n"
                    "- También incluye preguntas sobre entidades estructuradas presentes en reviews, aunque el usuario no mencione la palabra 'reseña' explícitamente, por ejemplo: sucursal, sede, ciudad, cantidad de opiniones, número de casos, top sucursales, etc.\n"
                    "- Usa 'rag' si la pregunta pide resumen, sentimiento, opinión general, temas frecuentes, conclusiones, explicación o síntesis de reseñas.\n\n"

                    "Heurísticas fuertes:\n"
                    "- Si la pregunta empieza con 'cuántos', 'cuántas', 'cuál es el número de', 'cuáles son', 'lista', 'dame', 'muéstrame', 'top', 'promedio', 'máximo', 'mínimo', 'existe', normalmente corresponde a 'sql' SI la fuente correcta es 'reviews'.\n"
                    "- Si la pregunta pide 'resumir', 'explicar', 'qué opinan', 'qué dicen', 'sentimiento', 'temas comunes', normalmente corresponde a 'rag'.\n"
                    "- No elijas 'products' solo porque aparezca una entidad de negocio como 'sucursal' o 'ciudad'. Si la intención es contar, filtrar o consultar registros estructurados y eso puede provenir de reviews, elige 'reviews' + 'sql'.\n\n"

                    "Ejemplos:\n"
                    "- '¿Cuántas sucursales hay en Medellín?' => "
                    "{{\"source_tag\": \"reviews\", \"next_agent\": \"sql\", \"reasoning\": \"Pregunta de conteo exacto por ciudad sobre datos estructurados de reviews.\"}}\n"
                    "- '¿Qué opinan los usuarios de las sucursales de Medellín?' => "
                    "{{\"source_tag\": \"reviews\", \"next_agent\": \"rag\", \"reasoning\": \"Pide resumen/opiniones generales de reseñas.\"}}\n"
                    "- '¿Cuál sucursal tiene más reseñas negativas?' => "
                    "{{\"source_tag\": \"reviews\", \"next_agent\": \"sql\", \"reasoning\": \"Requiere agregación/ranking exacto sobre la base de reviews.\"}}\n"
                    "- 'Resume el sentimiento de los clientes sobre la atención en Bogotá' => "
                    "{{\"source_tag\": \"reviews\", \"next_agent\": \"rag\", \"reasoning\": \"Pide síntesis semántica y sentimiento general.\"}}\n"
                    "- '¿Qué productos ofrecen para ahorro?' => "
                    "{{\"source_tag\": \"products\", \"next_agent\": \"rag\", \"reasoning\": \"Consulta descriptiva sobre documentos de productos.\"}}\n"
                    "- '¿Qué es BRE-B?' => "
                    "{{\"source_tag\": \"bre-b\", \"next_agent\": \"rag\", \"reasoning\": \"Consulta conceptual sobre documentos PDF.\"}}\n\n"

                    "Reglas de 'clarify':\n"
                    "1. Si la pregunta es demasiado vaga (ej: 'hola', 'ayuda', 'qué hago?').\n"
                    "2. Si la pregunta no tiene suficiente contexto para decidir entre las fuentes disponibles.\n"
                    "3. Si la pregunta no tiene NADA que ver con el banco o los temas disponibles.\n"
                    "4. En estos casos, usa 'source_tag': 'clarify' y 'next_agent': 'none'.\n\n"

                    "Salida obligatoria:\n"
                    "- Responde únicamente en JSON válido.\n"
                    "- Usa exactamente estas claves: 'source_tag', 'next_agent', 'reasoning'.\n"
                    "- 'next_agent' solo puede ser 'rag', 'sql' o 'none'.\n"
                    "- Si 'source_tag' es 'products' o 'bre-b', entonces 'next_agent' debe ser 'rag'.\n"
                    "- Si 'source_tag' es 'clarify', entonces 'next_agent' debe ser 'none'.\n"
                    "- El campo 'reasoning' debe ser breve y concreto."
                )
            ),
            ("user", "Pregunta: {question}")
        ]).partial(sources_description=sources_desc)
        
        self.chain = self.prompt | self.llm | self.parser

    def route(self, question: str, source_tag: Optional[str] = None, k: Optional[int] = None) -> Dict[str, Any]:
        """
        Determina la fuente de datos y retorna el diccionario de configuración para el RAG.
        
        Args:
            question: La pregunta del usuario.
            source_tag: (Opcional) Si se proporciona, se usará este en lugar de inferirlo.
            k: (Opcional) El número de fragmentos a recuperar.
            
        Returns:
            Dict con 'question', 'source_tag' y opcionalmente 'k'.
        """
        # Si ya me dan el source_tag, lo respeto
        final_source_tag = source_tag
        next_agent = "rag" # Default
        
        if not final_source_tag:
            try:
                # Invocamos al LLM para decidir con monitoreo de tokens
                with get_openai_callback() as cb:
                    decision = self.chain.invoke({"question": question})
                    
                    # Log tokens (try file, fallback to console if read-only)
                    try:
                        with open("token_usage.txt", "a") as f:
                            f.write(f"--- ROUTER AGENT ---\n")
                            f.write(f"Question: {question[:50]}...\n")
                            f.write(f"Total Tokens: {cb.total_tokens}\n")
                            f.write(f"Prompt Tokens: {cb.prompt_tokens}\n")
                            f.write(f"Completion Tokens: {cb.completion_tokens}\n")
                            f.write(f"Total Cost (USD): ${cb.total_cost:.6f}\n\n")
                    except (IOError, OSError):
                        print(f"--- ROUTER AGENT ---")
                        print(f"Question: {question[:50]}...")
                        print(f"Total Tokens: {cb.total_tokens}")
                        print(f"Prompt Tokens: {cb.prompt_tokens}")
                        print(f"Completion Tokens: {cb.completion_tokens}")
                        print(f"Total Cost (USD): ${cb.total_cost:.6f}")

                final_source_tag = decision.get("source_tag")
                next_agent = decision.get("next_agent", "rag")
                
                # Validamos que el tag sea uno de los conocidos
                if final_source_tag not in SOURCES:
                    raise ValueError(f"Tag de fuente inválido: {final_source_tag}")
            except Exception as e:
                print(f"Error en el router: {e}. Usando fallback 'products' y 'rag'.")
                final_source_tag = "products"
                next_agent = "rag"

        # Preparamos el payload que recibirá el RAG
        output = {
            "question": question,
            "source_tag": final_source_tag,
            "next_agent": next_agent
        }
        
        # Si la estrategia es RAG (conceptual/totalidad), usamos k=35 como máximo
        if next_agent == "rag" and final_source_tag == "reviews":
            output["k"] = 35
        elif k is not None:
            output["k"] = k
            
        return output

# ---------------------------------------------------------------------------
# Prueba del Router
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    router = RouterAgent()
    
    test_cases = [
        # "¿Cuáles son los beneficios de la tarjeta de crédito?",
        # "Tengo problemas con el cajero, se tragó mi tarjeta y no me dan solución.",
        # "¿Cómo funciona la conectividad API en el sistema BRE-B?",
        # "¿Qué tasa de interés tiene la cuenta de ahorros?",
        # "Qué dicen de la atención para el banco",
        # "Dame el top ed usuarios que mas opinaron",
        # "Qué dicen las reseñas sobre el tiempo de espera?",
        #"Cuántos usuarios han dejado reseñas?",
        #""
        "cuantas sucursales hay en medellin?",
        "hola que haces?"
    ]
    
    print("\n--- PRUEBAS DEL ROUTER AGENT ---\n")
    for q in test_cases:
        filter_config = router.route(q, k=5)
        print(f"Pregunta: {q}")
        print(f"Configuración asignada: {filter_config}")
        print("-" * 50)
