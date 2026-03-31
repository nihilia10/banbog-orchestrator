import pandas as pd
import tiktoken

def report_data_balance():
    csv_file = "vector_dataset.csv"
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: {csv_file} not found. Run create_dataset.py first.")
        return

    # We use 'cl100k_base' which is the tokenizer used by text-embedding-3 and GPT-4
    encoding = tiktoken.get_encoding("cl100k_base")

    # Calculate Character and Token sizes for every row/chunk
    df['char_count'] = df['text'].fillna("").apply(len)
    df['token_count'] = df['text'].fillna("").apply(lambda x: len(encoding.encode(str(x))))
    
    print("\n" + "="*60)
    print("  📊 VECTOR DATABASE DISTRIBUTION REPORT")
    print("="*60)

    # Group data by source_tag
    grouped = df.groupby('source_tag')
    
    # Calculate database totals for percentages
    total_chunks = len(df)
    total_chars = df['char_count'].sum()
    total_tokens = df['token_count'].sum()
    
    # Print statistics for each source
    for tag, group in grouped:
        tag_chunks = len(group)
        tag_chars = group['char_count'].sum()
        tag_tokens = group['token_count'].sum()
        
        chunk_pct = (tag_chunks / total_chunks) * 100
        token_pct = (tag_tokens / total_tokens) * 100 if total_tokens > 0 else 0
        
        print(f"\n🏷️  Source Tag: '{tag.upper()}'")
        print(f"  - Total Chunks:     {tag_chunks:,} ({chunk_pct:.1f}% of total DB chunks)")
        print(f"  - Total Characters: {tag_chars:,}")
        print(f"  - Total Tokens:     {tag_tokens:,} ({token_pct:.1f}% of total DB tokens)")
        print(f"  - Avg Tokens/Chunk: {tag_tokens / tag_chunks:.1f}")
        
    print("\n" + "-"*60)
    print("📈 OVERALL DATABASE SUMMARY")
    print(f"  - Total Chunks:     {total_chunks:,}")
    print(f"  - Total Characters: {total_chars:,}")
    print(f"  - Total Tokens:     {total_tokens:,}")
    print("="*60 + "\n")

if __name__ == "__main__":
    report_data_balance()
