import os
import json
import pandas as pd
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def build_faiss_and_sample():
    csv_file = "vector_dataset.csv"
    if not os.path.exists(csv_file):
        print(f"Error: Could not find the file {csv_file}. Run create_dataset.py first.")
        return

    # Verify OpenAI API KEY for embeddings
    if not os.environ.get("OPENAI_API_KEY"):
        print("\nWARNING: OPENAI_API_KEY was not found in environment variables.")
        print("Export your API KEY in the terminal before using this code, for example:")
        print("export OPENAI_API_KEY='sk-...'")
        
    print(f"Loading {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} chunks from the CSV.")
    
    documents = []
    print("Reconstructing LangChain Documents...")
    for _, row in df.iterrows():
        try:
            metadata = json.loads(str(row["metadata"]))
        except Exception:
            metadata = {}
            
        # Add tag to metadata to allow future filtering (metadata_filtering)
        metadata["source_tag"] = str(row["source_tag"])
        
        doc = Document(
            page_content=str(row["text"]),
            metadata=metadata
        )
        documents.append(doc)
        
    print("Generating embeddings and saving to FAISS...")
    try:
        # We suggest using text-embedding-3-small from OpenAI
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = FAISS.from_documents(documents, embeddings)
        
        # Save your database locally
        vectorstore.save_local("faiss_index")
        print("\nSuccess! FAISS Vector Database stored locally in ./faiss_index")
    except Exception as e:
        print(f"Error building FAISS (Check your API Key): {e}")
        return
        
    # --- Run a sample (quick test) ---
    print("\n" + "="*50)
    print("SAMPLE - DOCUMENTS STORED IN THE VECTOR STORE")
    print("="*50)
    query = "requisitos o problemas financieros con productos bancarios"
    print(f"Example similarity search for: '{query}'\n")
    
    try:
        results = vectorstore.similarity_search(query, k=3)
        for i, res in enumerate(results):
            print(f"--- Returned Document #{i+1} ---")
            print(f"Tag          : {res.metadata.get('source_tag')}")
            print(f"Metadata     : {res.metadata}")
            clean_content = res.page_content.replace('\n', ' ')
            print(f"Content      : {clean_content[:250]}...\n")
    except Exception as e:
        print(f"Error running the sample: {e}")

if __name__ == "__main__":
    build_faiss_and_sample()
