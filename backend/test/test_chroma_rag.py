import pytest
import os
from unittest.mock import MagicMock
from app.chroma_rag import init_rag_system, query_rag_db, CHROMA_DB_DIR, DOC_DIR
from langchain.docstore.document import Document

# --- Tests for init_rag_system ---

def test_init_rag_system_success(fs, mocker, capsys):
    """
    Tests successful initialization with documents.
    """
    # Mock the embedding model and ChromaDB to prevent network/disk access
    mocker.patch('app.chroma_rag.SentenceTransformerEmbeddings')
    mock_chroma_class = mocker.patch('app.chroma_rag.Chroma')
    
    # Configure the mock to create the directory on the fake filesystem
    mock_chroma_class.from_documents.side_effect = lambda *args, **kwargs: fs.create_dir(CHROMA_DB_DIR)

    # Arrange: Create a fake docs directory and a document file
    fs.create_dir(DOC_DIR)
    fs.create_file(os.path.join(DOC_DIR, "doc1.txt"), contents="This is a test document.")

    # Action
    init_rag_system()

    # Assertions
    mock_chroma_class.from_documents.assert_called_once()
    assert fs.exists(CHROMA_DB_DIR)

def test_init_rag_system_empty_docs_dir(fs, mocker, capsys):
    """
    Tests that init_rag_system handles an empty docs directory gracefully.
    """
    # Mock the embedding model and ChromaDB
    mocker.patch('app.chroma_rag.SentenceTransformerEmbeddings')
    mock_chroma_class = mocker.patch('app.chroma_rag.Chroma')
    
    # Arrange: Create an empty docs directory
    fs.create_dir(DOC_DIR)
    
    # Action
    init_rag_system()
    
    # Assertions
    mock_chroma_class.from_documents.assert_not_called()
    captured = capsys.readouterr()
    assert "Directory './docs' not found or is empty." in captured.out

def test_init_rag_system_cleans_up_existing_db(fs, mocker, capsys):
    """
    Tests that init_rag_system deletes the old ChromaDB directory.
    """
    # Mock the embedding model and ChromaDB
    mocker.patch('app.chroma_rag.SentenceTransformerEmbeddings')
    mock_chroma_class = mocker.patch('app.chroma_rag.Chroma')

    # Configure the mock to simulate creating the directory on the fake file system
    mock_chroma_class.from_documents.side_effect = lambda *args, **kwargs: fs.create_dir(CHROMA_DB_DIR)

    # Arrange: Create a fake ChromaDB directory and a docs directory
    fs.create_dir(CHROMA_DB_DIR)
    fs.create_file(os.path.join(DOC_DIR, "doc1.txt"), contents="...")

    # Action
    init_rag_system()

    # Assertions
    # The old directory should have been deleted, and a new one should have been created
    mock_chroma_class.from_documents.assert_called_once()
    assert fs.exists(CHROMA_DB_DIR)
    
    captured = capsys.readouterr()
    assert "Deleting existing ChromaDB data" in captured.out
    
# --- Tests for query_rag_db ---

def test_query_rag_db_success(fs, mocker):
    """
    Tests a successful query that returns relevant documents.
    """
    # Mock the embedding model and ChromaDB
    mocker.patch('app.chroma_rag.SentenceTransformerEmbeddings')
    mock_chroma_instance = MagicMock()
    mock_chroma_instance.similarity_search.return_value = [
        MagicMock(spec=Document, page_content="Relevant document 1."),
        MagicMock(spec=Document, page_content="Relevant document 2.")
    ]
    mocker.patch('app.chroma_rag.Chroma', return_value=mock_chroma_instance)
    
    # Arrange: Create a fake ChromaDB directory
    fs.create_dir(CHROMA_DB_DIR)
    
    # Action
    query = "test query"
    results = query_rag_db(query=query)
    
    # Assertions
    assert results is not None
    assert len(results) == 2
    assert "Relevant document 1." in results
    assert "Relevant document 2." in results

def test_query_rag_db_not_initialized(fs, mocker, capsys):
    """
    Tests that the function handles a non-existent database.
    """
    mocker.patch('app.chroma_rag.SentenceTransformerEmbeddings')
    mocker.patch('app.chroma_rag.Chroma')
    
    # Arrange: Ensure the ChromaDB directory does not exist
    if fs.exists(CHROMA_DB_DIR):
        fs.remove_dir(CHROMA_DB_DIR)
    
    # Action
    results = query_rag_db(query="test query")
    
    # Assertions
    assert results is None
    captured = capsys.readouterr()
    assert "ChromaDB not initialized" in captured.out

def test_query_rag_db_no_results(fs, mocker):
    """
    Tests that the function returns an empty list when no documents are found.
    """
    # Mock the embedding model and ChromaDB
    mocker.patch('app.chroma_rag.SentenceTransformerEmbeddings')
    mock_chroma_instance = MagicMock()
    mock_chroma_instance.similarity_search.return_value = []
    mocker.patch('app.chroma_rag.Chroma', return_value=mock_chroma_instance)
    
    # Arrange: Create a fake ChromaDB directory
    fs.create_dir(CHROMA_DB_DIR)
    
    # Action
    results = query_rag_db(query="unlikely query")
    
    # Assertions
    assert results == []