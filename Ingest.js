/*
 * ingest.js (MODIFIED)
 * Bypasses langchain/community for embeddings
 * Usage: node ingest.js
 */

import { Chroma } from '@langchain/community/vectorstores/chroma';
import { promises as fs } from 'fs';
import path from 'path';
// --- NEW IMPORT ---
// We now import 'pipeline' and 'env' from the package we know works
import { pipeline, env } from '@xenova/transformers';

// --- Configuration ---
const FILE_PATH = path.join(process.cwd(), 'my-document.txt');
const COLLECTION_NAME = 'my_txt_collection';
const CHROMA_URL = 'http://localhost:8000';
const MODEL_NAME = 'Xenova/all-MiniLM-L6-v2';

// Allows models to be loaded locally
env.allowLocalModels = true;

// --- 1. OUR NEW EMBEDDING CLASS ---
/**
 * A wrapper class to mimic LangChain's Embeddings
 * using @xenova/transformers directly.
 */
class XenovaEmbeddings {
  constructor(modelName) {
    this.modelName = modelName;
    // The pipeline is loaded once and reused
    this.pipe = null; 
  }

  // Helper to load the pipeline on first use
  async _getPipeline() {
    if (this.pipe === null) {
      console.log('Loading embedding model for the first time...');
      this.pipe = await pipeline('feature-extraction', this.modelName);
      console.log('Embedding model loaded.');
    }
    return this.pipe;
  }

  // Creates vectors for all document chunks
  async embedDocuments(texts) {
    console.log(`Embedding ${texts.length} document chunks...`);
    const embedder = await this._getPipeline();
    const results = [];
    for (const text of texts) {
      // Create the embedding
      const output = await embedder(text, { pooling: 'mean', normalize: true });
      // Convert the 'data' (a Float32Array) into a standard array
      results.push(Array.from(output.data));
    }
    return results;
  }

  // Creates a vector for a single query
  async embedQuery(text) {
    const embedder = await this._getPipeline();
    const output = await embedder(text, { pooling: 'mean', normalize: true });
    return Array.from(output.data);
  }
}

// --- 2. Initialize our new Embedding Model ---
const embeddings = new XenovaEmbeddings(MODEL_NAME);

// --- 3. Our Manual Text Splitter (from before) ---
function manualTextSplitter(text, chunkSize, chunkOverlap) {
  // ... (This function is the same as in the previous step)
  const chunks = [];
  let i = 0;
  if (chunkOverlap >= chunkSize) chunkOverlap = 0;
  while (i < text.length) {
    chunks.push(text.slice(i, i + chunkSize));
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
    // --- 4. Read Text ---
    console.log('Reading text file...');
    const text = await fs.readFile(FILE_PATH, 'utf-8');
    if (!text) throw new Error('File is empty.');
    console.log(`Read ${text.length} characters.`);

    // --- 5. Split Text ---
    console.log('Splitting text into chunks...');
    const textChunks = manualTextSplitter(text, 500, 50);
    const docs = textChunks.map(chunk => ({
      pageContent: chunk,
      metadata: { source: FILE_PATH }
    }));
    console.log(`Created ${docs.length} document chunks.`);

    // --- 6. Initialize Chroma ---
    const chromaStore = new Chroma(embeddings, {
      collectionName: COLLECTION_NAME,
      url: CHROMA_URL,
    });

    // --- 7. Store in ChromaDB ---
    console.log('Deleting old collection and adding new documents...');
    await chromaStore.addDocuments(docs);
    
    console.log('✅ Ingestion complete!');

  } catch (error) {
    console.error('--- Ingestion Failed ---');
    console.error(error.message);
  }
}

ingestDocument();
