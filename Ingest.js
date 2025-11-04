/*
 * ingest.js (MODIFIED - NO LANGCHAIN)
 * Uses chromadb-client directly.
 * Usage: node ingest.js
 */

import { ChromaClient } from 'chromadb-client'; // Using the client directly
import { promises as fs } from 'fs';
import path from 'path';
import { pipeline, env } from '@xenova/transformers';

// --- Configuration ---
const FILE_PATH = path.join(process.cwd(), 'my-document.txt');
const COLLECTION_NAME = 'my_txt_collection';
const CHROMA_URL = 'http://localhost:8000';
const MODEL_NAME = 'Xenova/all-MiniLM-L6-v2';

env.allowLocalModels = true;

// --- 1. OUR EMBEDDING CLASS (Same as before) ---
class XenovaEmbeddings {
  constructor(modelName) {
    this.modelName = modelName;
    this.pipe = null;
  }
  async _getPipeline() {
    if (this.pipe === null) {
      this.pipe = await pipeline('feature-extraction', this.modelName);
    }
    return this.pipe;
  }
  async embedDocuments(texts) {
    const embedder = await this._getPipeline();
    const results = [];
    for (const text of texts) {
      const output = await embedder(text, { pooling: 'mean', normalize: true });
      results.push(Array.from(output.data));
    }
    return results;
  }
  async embedQuery(text) {
    const embedder = await this._getPipeline();
    const output = await embedder(text, { pooling: 'mean', normalize: true });
    return Array.from(output.data);
  }
}

// --- 2. Our Manual Text Splitter (Same as before) ---
function manualTextSplitter(text, chunkSize, chunkOverlap) {
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
  console.log('Starting ingestion...');
  
  try {
    // --- Initialize Client and Embedder ---
    const client = new ChromaClient({ path: CHROMA_URL });
    const embeddings = new XenovaEmbeddings(MODEL_NAME);

    // --- 3. Read and Split Text ---
    const text = await fs.readFile(FILE_PATH, 'utf-8');
    const chunks = manualTextSplitter(text, 500, 50);
    console.log(`Created ${chunks.length} text chunks.`);

    // --- 4. Embed all chunks ---
    console.log('Creating embeddings for all chunks...');
    const embeddedChunks = await embeddings.embedDocuments(chunks);
    console.log('Embeddings created.');

    // --- 5. Prepare documents for ChromaDB ---
    const documents = chunks.map((chunk, index) => ({
      id: `doc_${index}`, // Chroma requires a unique ID for each item
      embedding: embeddedChunks[index],
      metadata: { source: FILE_PATH },
      document: chunk, // This is the original text content
    }));

    // --- 6. Get or Create Collection ---
    console.log(`Getting or creating collection: ${COLLECTION_NAME}`);
    // This will delete the collection if it exists and create a new one
    try {
      await client.deleteCollection({ name: COLLECTION_NAME });
      console.log('Deleted old collection.');
    } catch (e) {
      // Ignore error if collection didn't exist
    }
    
    const collection = await client.createCollection({ 
      name: COLLECTION_NAME,
      metadata: { "hnsw:space": "cosine" } // Use cosine distance for similarity
    });

    // --- 7. Add Documents to Collection ---
    console.log('Adding documents to collection...');
    await collection.add({
      ids: documents.map(d => d.id),
      embeddings: documents.map(d => d.embedding),
      metadatas: documents.map(d => d.metadata),
      documents: documents.map(d => d.document),
    });

    console.log('✅ Ingestion complete!');

  } catch (error) {
    console.error('--- Ingestion Failed ---');
    console.error(error.message);
  }
}

ingestDocument();
