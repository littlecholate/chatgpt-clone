/*
 * ingest.js
 * Run this script once to "teach" ChromaDB your document.
 * Usage: node ingest.js
 */

import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter';
import { HuggingFaceTransformersEmbeddings } from '@langchain/community/embeddings/hf';
import { Chroma } from '@langchain/community/vectorstores/chroma';
import { promises as fs } from 'fs'; // Node.js File System module
import path from 'path';

// --- Configuration ---
const FILE_PATH = path.join(process.cwd(), 'my-document.txt'); // Path to your .txt file
const COLLECTION_NAME = 'my_txt_collection'; // A unique name for your collection
const CHROMA_URL = 'http://localhost:8000'; // URL for your running Chroma server

// --- 1. Initialize Embedding Model ---
// This downloads a model (e.g., 'all-MiniLM-L6-v2') the first time it runs.
const embeddings = new HuggingFaceTransformersEmbeddings({
  modelName: 'Xenova/all-MiniLM-L6-v2',
});

// --- 2. Initialize Text Splitter ---
const textSplitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500,  // Smaller chunk size for this small doc
  chunkOverlap: 50,
});

/**
 * Main ingestion function
 */
async function ingestDocument() {
  console.log(`Starting ingestion for: ${FILE_PATH}`);
  
  try {
    // --- 3. Read Text from .txt file ---
    console.log('Reading text file...');
    const text = await fs.readFile(FILE_PATH, 'utf-8');
    
    if (!text || text.trim().length === 0) {
      throw new Error('File is empty or could not be read.');
    }
    console.log(`Read ${text.length} characters.`);

    // --- 4. Split Text into Chunks ---
    console.log('Splitting text into chunks...');
    // createDocuments splits text and adds metadata
    const docs = await textSplitter.createDocuments(
      [text],
      [{ source: FILE_PATH }] // Add metadata
    );
    console.log(`Created ${docs.length} document chunks.`);

    // --- 5. Initialize Chroma Vector Store ---
    const chromaStore = new Chroma(embeddings, {
      collectionName: COLLECTION_NAME,
      url: CHROMA_URL,
    });

    // --- 6. Store Chunks in ChromaDB ---
    // This will delete any existing collection with the same name.
    console.log('Deleting old collection (if any) and adding new documents...');
    await chromaStore.addDocuments(docs);
    
    console.log('✅ Ingestion complete!');
    console.log(`Your data is now in the "${COLLECTION_NAME}" collection in ChromaDB.`);

  } catch (error) {
    console.error('--- Ingestion Failed ---');
    console.error(error.message);
  }
}

// Run the ingestion
ingestDocument();
