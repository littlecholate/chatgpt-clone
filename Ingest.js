/*
 * ingest.js (MODIFIED)
 * No longer uses @langchain/text_splitter
 * Usage: node ingest.js
 */

// --- We NO LONGER import RecursiveCharacterTextSplitter ---
import { HuggingFaceTransformersEmbeddings } from '@langchain/community/embeddings/hf';
import { Chroma } from '@langchain/community/vectorstores/chroma';
import { promises as fs } from 'fs'; // Node.js File System module
import path from 'path';

// --- Configuration ---
const FILE_PATH = path.join(process.cwd(), 'my-document.txt');
const COLLECTION_NAME = 'my_txt_collection';
const CHROMA_URL = 'http://localhost:8000';

// --- 1. Initialize Embedding Model ---
const embeddings = new HuggingFaceTransformersEmbeddings({
  modelName: 'Xenova/all-MiniLM-L6-v2',
});

// --- 2. OUR NEW MANUAL TEXT SPLITTER ---
/**
 * A simple function to split text into overlapping chunks.
 * @param {string} text The full text to split.
 * @param {number} chunkSize The max size of each chunk.
 * @param {number} chunkOverlap The overlap between chunks.
 * @returns {string[]} An array of text chunks.
 */
function manualTextSplitter(text, chunkSize, chunkOverlap) {
  const chunks = [];
  let i = 0;
  
  // Ensure overlap is smaller than chunk size
  if (chunkOverlap >= chunkSize) {
    console.warn("Overlap is >= chunk size, setting overlap to 0");
    chunkOverlap = 0;
  }

  while (i < text.length) {
    // Get the end of the chunk
    let end = i + chunkSize;
    
    // Add the chunk to the array
    chunks.push(text.slice(i, end));
    
    // Move the start of the next chunk
    i += chunkSize - chunkOverlap;
  }
  return chunks;
}


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

    // --- 4. Split Text into Chunks (using our new function) ---
    console.log('Splitting text into chunks...');
    const textChunks = manualTextSplitter(text, 500, 50); // (text, chunkSize, chunkOverlap)
    
    // Manually format them into "Document" objects
    const docs = textChunks.map(chunk => ({
      pageContent: chunk,
      metadata: { source: FILE_PATH }
    }));
    
    console.log(`Created ${docs.length} document chunks.`);

    // --- 5. Initialize Chroma Vector Store ---
    const chromaStore = new Chroma(embeddings, {
      collectionName: COLLECTION_NAME,
      url: CHROMA_URL,
    });

    // --- 6. Store Chunks in ChromaDB ---
    console.log('Deleting old collection (if any) and adding new documents...');
    await chromaStore.addDocuments(docs);
    
    console.log('✅ Ingestion complete!');
    console.log(`Your data is in the "${COLLECTION_NAME}" collection.`);

  } catch (error) {
    console.error('--- Ingestion Failed ---');
    console.error(error.message);
  }
}

// Run the ingestion
ingestDocument();
