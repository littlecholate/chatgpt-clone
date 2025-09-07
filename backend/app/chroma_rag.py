import os
import shutil
from typing import List, Optional

# This assumes you have the following packages installed:
# You'll need to install the new package for Chroma.
# pip install -U langchain-chroma
# And the other necessary libraries:
# pip install langchain-community sentence-transformers

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma # Updated import
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Define the directory where the text documents are stored
DOC_DIR = "./docs"
# Define the directory for the ChromaDB persistent storage
CHROMA_DB_DIR = "./chroma_db"
# Define the ChromaDB collection name
COLLECTION_NAME = "local_docs"


def init_rag_system():
    """
    Initializes the RAG system by loading and chunking documents,
    and then creating a ChromaDB collection.
    """
    print("Initializing RAG system...")
    
    # Check if the docs directory exists and contains a file
    if not os.path.exists(DOC_DIR) or not os.listdir(DOC_DIR):
        print(f"Directory '{DOC_DIR}' not found or is empty. Please create it and add a .txt file.")
        return

    # Delete existing ChromaDB data to ensure a fresh index
    if os.path.exists(CHROMA_DB_DIR):
        print(f"Deleting existing ChromaDB data at '{CHROMA_DB_DIR}'...")
        shutil.rmtree(CHROMA_DB_DIR)

    # 1. Load documents from the specified directory
    # The `loader_cls_kwargs` is added to handle encoding issues by specifying utf-8
    loader = DirectoryLoader(
        DOC_DIR,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents.")
    
    # 2. Split documents into chunks for embedding
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    docs = text_splitter.split_documents(documents)
    print(f"Split documents into {len(docs)} chunks.")

    # 3. Create a ChromaDB collection with a local SentenceTransformer model
    # The model 'all-MiniLM-L6-v2' will be downloaded automatically the first time.
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    Chroma.from_documents(
        docs,
        embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DB_DIR
    )
    print(f"Documents stored in ChromaDB at '{CHROMA_DB_DIR}'.")
    

def query_rag_db(query: str, k: int = 4) -> Optional[List[str]]:
    """
    Queries the ChromaDB for relevant documents based on the user's query.
    
    Args:
        query (str): The user's query string.
        k (int): The number of top documents to retrieve.
    
    Returns:
        Optional[List[str]]: A list of relevant document contents, or None if the
                             database is not initialized.
    """
    # Check if the ChromaDB directory exists
    if not os.path.exists(CHROMA_DB_DIR):
        print("ChromaDB not initialized. Please run `init_rag_system()` first.")
        return None

    # Use the same local embedding model as used for indexing
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    # Perform a similarity search
    results = vectorstore.similarity_search(query, k=k)
    
    if not results:
        return []
    
    # Extract the content from the retrieved documents
    relevant_docs = [doc.page_content for doc in results]
    
    return relevant_docs


if __name__ == "__main__":
    # Example usage:
    # 1. Place a file named `my_document.txt` in a new `docs` folder.
    # 2. Run this file directly from your terminal: `python chroma_rag.py`
    # 3. Then, you can try querying it:
    
    init_rag_system()
    
    # Example query
    example_query = "What is the capital of Japan?"
    retrieved_docs = query_rag_db(example_query)
    
    print("\n--- Retrieved Documents ---")
    if retrieved_docs:
        for doc in retrieved_docs:
            print(doc)
            print("-" * 20)
    else:
        print("No relevant documents found.")
