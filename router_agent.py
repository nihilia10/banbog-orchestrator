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
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_community.callbacks import get_openai_callback

# ---------------------------------------------------------------------------
# Fuentes de datos y sus descripciones
# ---------------------------------------------------------------------------
SOURCES = {
    "products": "Información sobre productos bancarios, beneficios de tarjetas, tipos de cuentas y servicios generales del banco.",
    "reviews": "Feedback de clientes, opiniones sobre el servicio, quejas y comentarios sobre la experiencia del usuario.",
    "bre-b": "Especificaciones técnicas, arquitectura de software, diagramas, componentes y reglas de negocio del sistema BRE-B."
}

# ---------------------------------------------------------------------------
# Estructura de salida del Router
# ---------------------------------------------------------------------------
class RouterDecision(BaseModel):
    source_tag: str = Field(description="El tag de la fuente de datos elegida (products, reviews o bre-b)")
    next_agent: str = Field(description="El agente que procesará la consulta: 'sql' (para datos estructurados/específicos) o 'rag' (para conceptual/sentimiento/totality)")
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
                "Eres un asistente de banca experto en enrutamiento de consultas. "
                "Tu objetivo es identificar cuál de las siguientes fuentes de datos es la mejor para responder la pregunta del usuario:\n\n"
                "{sources_description}\n\n"
                "Instrucciones:\n"
                "1. Analiza el contenido de la pregunta.\n"
                "2. Selecciona el 'source_tag' más relevante.\n"
                "3. Para reviews, decide el 'next_agent':\n"
                "   - 'sql': Si la pregunta requiere buscar datos específicos (contar registros, buscar un usuario, sucursal, datos exactos en la tabla).\n"
                "   - 'rag': Si la pregunta es conceptual, trata sobre la totalidad de los datos, pide opiniones generales o resúmenes de sentimientos.\n"
                "4. Para otras fuentes ('products', 'bre-b'), usa siempre 'rag'.\n"
                "5. Responde estrictamente en formato JSON con los campos 'source_tag', 'next_agent' y 'reasoning'.\n"
            )),
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
                    
                    # Log tokens to file
                    with open("token_usage.txt", "a") as f:
                        f.write(f"--- ROUTER AGENT ---\n")
                        f.write(f"Question: {question[:50]}...\n")
                        f.write(f"Total Tokens: {cb.total_tokens}\n")
                        f.write(f"Prompt Tokens: {cb.prompt_tokens}\n")
                        f.write(f"Completion Tokens: {cb.completion_tokens}\n")
                        f.write(f"Total Cost (USD): ${cb.total_cost:.6f}\n\n")

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
        "Teniendo en cuenta la tecnología de Bre-b a qué sucursal del banco me recomiendas ir?"
    ]
    
    print("\n--- PRUEBAS DEL ROUTER AGENT ---\n")
    for q in test_cases:
        filter_config = router.route(q, k=5)
        print(f"Pregunta: {q}")
        print(f"Configuración asignada: {filter_config}")
        print("-" * 50)
