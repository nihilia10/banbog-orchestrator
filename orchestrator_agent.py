"""
orchestrator_agent.py

This module implements the "Orchestrator Agent" for the BanBog system.
It uses LangChain Expression Language (LCEL) to chain a Router Agent 
with a RAG (Retrieval-Augmented Generation) Agent.

Workflow:
1. Receive user question.
2. Route the question to the appropriate data source (products, reviews, or bre-b).
3. Retrieve context from the selected source and generate a grounded answer.
"""

import os
from langchain_core.runnables import RunnableLambda
from router_agent import RouterAgent
from llm import RAGAgent
from sql_agent import SQLAgent

def create_orchestrator():
    """
    Creates the Orchestrator Chain using LCEL.
    """
    # Initialize our specialized agents
    router = RouterAgent()
    rag = RAGAgent()
    sql_agent = SQLAgent()

    # Step 1: Routing
    routing_step = RunnableLambda(lambda x: router.route(x))

    # Step 2: Agent Selection & Query
    def unified_query(config: dict):
        next_agent = config.get("next_agent", "rag")
        source_tag = config.get("source_tag")

        if next_agent == "sql":
            print(f">>> Usando SQLAgent para fuente: {source_tag}")
            return sql_agent.query(config)
        else:
            print(f">>> Usando RAGAgent para fuente: {source_tag}")
            return rag.query(config)

    query_step = RunnableLambda(lambda x: unified_query(x))

    # Define the full LCEL chain
    orchestrator_chain = routing_step | query_step
    
    return orchestrator_chain

def main():
    # Setup the orchestrator
    print("Initializing Orchestrator Agent (LCEL)...")
    orchestrator = create_orchestrator()
    
    # Sample user questions
    test_questions = [
        # "¿Cuáles son los beneficios de la tarjeta de crédito?",
        "¿Quién es el usuario que más reseñas ha realizado en el banco?",
        "¿Qué dicen los clientes sobre las demoras en las oficinas?"
    ]

    print("\n" + "="*80)
    print("  ORCHESTRATOR AGENT: ROUTER + RAG SYSTEM (LCEL)")
    print("="*80 + "\n")

    for q in test_questions:
        print(f"USER: {q}")
        
        try:
            # Invoke the LCEL chain
            answer = orchestrator.invoke(q)
            print(f"AGENT:\n{answer}")
        except Exception as e:
            print(f"AGENT ERROR: {e}")
            
        print("-" * 80 + "\n")

if __name__ == "__main__":
    # Ensure API Key is available
    if not os.environ.get("OPENAI_API_KEY"):
        print("CRITICAL ERROR: OPENAI_API_KEY environment variable not found.")
    else:
        main()
