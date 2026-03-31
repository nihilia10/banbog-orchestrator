import os
import argparse
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

def query_db(vectorstore, query, tag=None, k=2):
    """Performs a search in the vector database with optional filtering."""
    print(f"Querying: '{query}'" + (f" (Filter: {tag})" if tag else " (No filters)"))
    
    filter_dict = {"source_tag": tag} if tag else None
    
    results = vectorstore.similarity_search(
        query, 
        k=k, 
        filter=filter_dict
    )
    print_results(results)

def main():
    parser = argparse.ArgumentParser(description="Query the FAISS Vector Database.")
    parser.add_argument("--query", type=str, help="The question to ask the database.")
    parser.add_argument("--tag", type=str, help="Optional filter by source_tag (e.g., 'products', 'reviews', 'bre-b').")
    parser.add_argument("--k", type=int, default=2, help="Number of results to return (default: 2).")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode.")
    
    args = parser.parse_args()

    db_path = "faiss_index"
    
    # 1. Check if the database folder exists
    if not os.path.exists(db_path):
        print(f"Error: Vector database not found at '{db_path}'. Please run build_vector_db.py first.")
        return

    # 2. Verify API KEY
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY was not found in environment variables.")
        return

    # Initialize the same embeddings model used to build the DB
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    try:
        vectorstore = FAISS.load_local(
            folder_path=db_path, 
            embeddings=embeddings, 
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        print(f"Error loading FAISS database: {e}")
        return

    # Decision Logic:
    # 1. Specific CLI query provided
    if args.query:
        query_db(vectorstore, args.query, args.tag, args.k)
    
    # 2. Interactive Mode
    elif args.interactive:
        print("--- Interactive Mode (type 'exit' to quit) ---")
        while True:
            try:
                user_query = input("\nAsk a question: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break
                
            if user_query.lower() in ("exit", "quit", "q"):
                break
            if not user_query:
                continue
            
            user_tag = input("Filter by tag (leave empty for none): ").strip() or None
            query_db(vectorstore, user_query, user_tag, args.k)

    # 3. Default Demo (if no args)
    else:
        print("--- Default Demo Search ---")
        # Reuse one of the original questions the user had in the file
        demo_query = "what are the requirements for a credit card?"
        query_db(vectorstore, demo_query)
        print("\nTIP: Run with --help to see all options or use --interactive for a live chat.")

if __name__ == "__main__":
    main()