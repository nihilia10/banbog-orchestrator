import pandas as pd
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_documents():
    data = []
    
    # 1. Bank Products Portfolio (Tag: "products", per page)
    print("Processing Products Portfolio...")
    loader_products = PyPDFLoader("portafolio_productos_bancarios_v2-1 (1).pdf")
    docs_products = loader_products.load()
    for doc in docs_products:
        data.append({
            "text": doc.page_content,
            "source_tag": "products",
            "metadata": json.dumps({
                "source": "portafolio_productos_v2",
                "page": doc.metadata.get("page", 0)
            })
        })
        
    # 2. Bank Reviews Colombia (Tag: "reviews", per row)
    print("Processing Bank Reviews...")
    try:
        df_reviews = pd.read_excel("bank_reviews_colombia (1).xlsx")
        for index, row in df_reviews.iterrows():
            # Converting the entire row into a text string
            row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
            data.append({
                "text": row_text,
                "source_tag": "reviews",
                "metadata": json.dumps({
                    "source": "bank_reviews",
                    "row": index
                })
            })
    except Exception as e:
        print(f"Error processing Bank Reviews: {e}")

    # 3. Technical Document BRE B (Tag: "bre-b", recursive split)
    print("Processing Technical Document BRE B...")
    loader_breb = PyPDFLoader("documento-tecnico-bre-b-febrero-2026.pdf")
    docs_breb = loader_breb.load()
    
    # Safe text chunking with ~1000 characters and ~200 overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks_breb = text_splitter.split_documents(docs_breb)
    
    for chunk in chunks_breb:
        data.append({
            "text": chunk.page_content,
            "source_tag": "bre-b",
            "metadata": json.dumps({
                "source": "documento_tecnico_bre-b",
                "page": chunk.metadata.get("page", 0)
            })
        })
        
    # Save to CSV
    print(f"\nTotal chunks generated: {len(data)}")
    df_output = pd.DataFrame(data)
    df_output.to_csv("vector_dataset.csv", index=False, encoding='utf-8')
    print("CSV file generated successfully: vector_dataset.csv")

if __name__ == "__main__":
    process_documents()
