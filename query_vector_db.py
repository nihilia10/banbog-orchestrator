import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def print_results(results):
    """Helper function to cleanly print the search results."""
    if not results:
        print("No results found.\n")
        return
        
    for i, res in enumerate(results):
        print(f"Result #{i+1}:")
        print(f"  Tag:      {res.metadata.get('source_tag', 'N/A')}")
        print(f"  Metadata: {res.metadata}")
        # Clean up newlines for cleaner terminal output
        content_preview = res.page_content.replace('\n', ' ')
        print(f"  Content:  {content_preview[:200]}...")
    print("\n" + "="*60 + "\n")

def main():
    db_path = "faiss_index"
    
    # 1. Check if the database folder exists
    if not os.path.exists(db_path):
        print(f"Error: Vector database not found at '{db_path}'. Please run build_vector_db.py first.")
        return

    # 2. Verify API KEY
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY was not found in environment variables.")
        print("Export your API KEY in the terminal before using this code.")
        print("Example: export OPENAI_API_KEY='sk-...'")
        return

    print("Loading existing FAISS Vector Database...")
    # Initialize the same embeddings model used to build the DB
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    try:
        # Load the index. 'allow_dangerous_deserialization' is required in recent langchain 
        # versions when loading pickled FAISS files locally.
        vectorstore = FAISS.load_local(
            folder_path=db_path, 
            embeddings=embeddings, 
            allow_dangerous_deserialization=True
        )
        print("Database loaded successfully!\n")
        print("="*60)
    except Exception as e:
        print(f"Error loading FAISS database: {e}")
        return

    # -------------------------------------------------------------------
    # TEST 1: General Semantic Search across the entire database
    # -------------------------------------------------------------------
    query_general = "what are the requirements for a credit card?"
    print(f"--- 1. General Search (No filters) ---")
    print(f"Query: '{query_general}'\n")
    results_general = vectorstore.similarity_search(query_general, k=2)
    print_results(results_general)

    # -------------------------------------------------------------------
    # TEST 2: Filter by 'products' (Bank Portfolio PDF)
    # -------------------------------------------------------------------
    query_products = "tarjeta de crédito beneficios" # Kept in Spanish since your docs are in ES
    print(f"--- 2. Search Filtering ONLY 'products' ---")
    print(f"Query: '{query_products}'\n")
    # We apply the filter using the 'source_tag' we injected in the metadata
    results_products = vectorstore.similarity_search(
        query_products, 
        k=2, 
        filter={"source_tag": "products"}
    )
    print_results(results_products)

    # -------------------------------------------------------------------
    # TEST 3: Filter by 'reviews' (Excel User Reviews)
    # -------------------------------------------------------------------
    query_reviews = "mal servicio al cliente demoras bloqueos"
    print(f"--- 3. Search Filtering ONLY 'reviews' ---")
    print(f"Query: '{query_reviews}'\n")
    results_reviews = vectorstore.similarity_search(
        query_reviews, 
        k=2, 
        filter={"source_tag": "reviews"}
    )
    print_results(results_reviews)

    # -------------------------------------------------------------------
    # TEST 4: Filter by 'bre-b' (Technical Document)
    # -------------------------------------------------------------------
    query_tech = "arquitectura técnica y componentes del sistema interoperabilidad"
    print(f"--- 4. Search Filtering ONLY 'bre-b' ---")
    print(f"Query: '{query_tech}'\n")
    results_bre = vectorstore.similarity_search(
        query_tech, 
        k=2, 
        filter={"source_tag": "bre-b"}
    )
    print_results(results_bre)

if __name__ == "__main__":
    main()
