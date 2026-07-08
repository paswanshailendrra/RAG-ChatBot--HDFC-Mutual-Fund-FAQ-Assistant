"""
Phase 2c: Text Chunker

Reads cleaned text files, splits them into semantic chunks using LangChain's
RecursiveCharacterTextSplitter, and attaches metadata (URL, Scheme Name) to each chunk.
"""
import os
import json
import re
from typing import List, Dict

from langchain.text_splitter import RecursiveCharacterTextSplitter

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import CHUNK_SIZE, CHUNK_OVERLAP


CLEANED_TEXT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cleaned_text')
CHUNKS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'chunks.json')


def parse_cleaned_file(filepath: str) -> Dict:
    """Parse a cleaned text file to extract metadata and individual text blocks."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split header from content
    parts = content.split("============================================================", 1)
    if len(parts) < 2:
        return {}

    header = parts[0]
    body = parts[1]

    # Extract metadata
    metadata = {}
    for line in header.strip().split('\n'):
        if line.startswith('Source URL:'):
            metadata['source_url'] = line.replace('Source URL:', '').strip()
        elif line.startswith('Scheme Name:'):
            metadata['scheme_name'] = line.replace('Scheme Name:', '').strip()
        elif line.startswith('Scraped At:'):
            metadata['scraped_at'] = line.replace('Scraped At:', '').strip()

    # Extract blocks
    # Splitting by "--- Block X ---"
    block_pattern = re.compile(r'--- Block \d+ ---')
    blocks_raw = block_pattern.split(body)
    
    blocks = [b.strip() for b in blocks_raw if b.strip()]

    return {
        "metadata": metadata,
        "blocks": blocks
    }


def chunk_text() -> List[Dict]:
    """Read all cleaned files, chunk the blocks, and return a list of chunk dictionaries."""
    print("=" * 60)
    print("🧩 Starting Chunking Process")
    print(f"   Settings: chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}")
    print("=" * 60)

    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " | ", " ", ""],
        length_function=len,
    )

    all_chunks = []
    
    if not os.path.exists(CLEANED_TEXT_DIR):
        print(f"❌ Cleaned text directory not found: {CLEANED_TEXT_DIR}")
        return []

    files = [f for f in os.listdir(CLEANED_TEXT_DIR) if f.endswith('.txt')]
    
    for i, filename in enumerate(files, 1):
        filepath = os.path.join(CLEANED_TEXT_DIR, filename)
        parsed_data = parse_cleaned_file(filepath)
        
        if not parsed_data or "metadata" not in parsed_data:
            print(f"  ⚠️ Skipping {filename}: Could not parse metadata.")
            continue
            
        metadata = parsed_data["metadata"]
        blocks = parsed_data["blocks"]
        
        print(f"\n[{i}/{len(files)}] {metadata.get('scheme_name', filename)}")
        print(f"  Found {len(blocks)} blocks to chunk.")

        scheme_chunks = []
        for block in blocks:
            # LangChain returns a list of strings
            splits = text_splitter.split_text(block)
            
            for split in splits:
                chunk_dict = {
                    "text": split,
                    "metadata": {
                        "source": metadata.get("source_url", ""),
                        "scheme_name": metadata.get("scheme_name", ""),
                    }
                }
                scheme_chunks.append(chunk_dict)

        all_chunks.extend(scheme_chunks)
        print(f"  ✅ Generated {len(scheme_chunks)} chunks.")

    print("\n" + "=" * 60)
    print(f"📊 Chunking Complete: {len(all_chunks)} total chunks created.")
    print("=" * 60)

    return all_chunks


def save_chunks(chunks: List[Dict]):
    """Save the list of chunks to a JSON file."""
    os.makedirs(os.path.dirname(CHUNKS_FILE), exist_ok=True)
    with open(CHUNKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved chunks to {CHUNKS_FILE}")


if __name__ == "__main__":
    chunks = chunk_text()
    if chunks:
        save_chunks(chunks)
        
        print("\n📋 Sample Chunk:")
        sample = chunks[0]
        print(f"  Scheme: {sample['metadata']['scheme_name']}")
        print(f"  Source: {sample['metadata']['source']}")
        print(f"  Text: {sample['text'][:200]}...")
