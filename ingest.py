import os
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DATA_DIR = "data"
DB_DIR = "chroma_db"


def main():
    # 1. Load PDFs
    print("Loading PDFs...")
    docs = PyPDFDirectoryLoader(DATA_DIR).load()
    print(f"Loaded {len(docs)} pages")

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=250,
    
    )
    chunks = splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks")

    # 3. Embeddings (free, runs locally)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # 4. Rebuild the vector DB from scratch
    if os.path.exists(DB_DIR):
        shutil.rmtree(DB_DIR)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR,
    )
    print(f"Vector DB saved to '{DB_DIR}'")


if __name__ == "__main__":
    main()