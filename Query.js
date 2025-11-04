/*
 * query.js (MODIFIED - NO LANGCHAIN)
 * Uses chromadb-client directly.
 * Usage: node query.js "What is RAG?"
 */

import { ChromaClient } from 'chromadb-client'; // Using the client directly
import axios from 'axios';
import { pipeline, env } from '@xenova/transformers';

// --- Configuration ---
const COLLECTION_NAME = 'my_txt_collection';
const CHROMA_URL = 'http://localhost:8000';
const MODEL_NAME = 'Xenova/all-MiniLM-L6-v2';
const YOUR_LLM_ENDPOINT = 'http://your-llm-api-endpoint.com/v1/chat';
const YOUR_API_KEY = 'YOUR_SECRET_API_KEY';

env.allowLocalModels = true;

// --- 1. OUR EMBEDDING CLASS (Must be identical to ingest.js) ---
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
  async embedQuery(text) {
    const embedder = await this._getPipeline();
    const output = await embedder(text, { pooling: 'mean', normalize: true });
    return Array.from(output.data);
  }
}

/**
 * Main query function
 */
async function queryRAG(userQuery) {
  console.log(`User Query: "${userQuery}"`);
  
  try {
    // --- Initialize Client and Embedder ---
    const client = new ChromaClient({ path: CHROMA_URL });
    const embeddings = new XenovaEmbeddings(MODEL_NAME);

    // --- 2. Get the Collection ---
    console.log(`Accessing collection: ${COLLECTION_NAME}`);
    const collection = await client.getCollection({ name: COLLECTION_NAME });

    // --- 3. Create Embedding for the Query ---
    console.log('Embedding user query...');
    const queryEmbedding = await embeddings.embedQuery(userQuery);

    // --- 4. Query ChromaDB ---
    console.log('Querying ChromaDB for relevant context...');
    const results = await collection.query({
      queryEmbeddings: [queryEmbedding],
      nResults: 2, // Get the top 2 most relevant chunks
    });

    // --- 5. Format the Context ---
    // The results are in results.documents[0]
    const context = results.documents[0].join('\n\n---\n\n');

    console.log('Context retrieved. Building prompt...');
    
    // --- 6. Build the Prompt for the LLM ---
    const systemPrompt = `You are a helpful assistant. Answer the user's question based *only* on the following context. If the answer is not in the context, say "I do not know".`;
    const finalPrompt = `
      **Context:**
      ${context}

      ---

      **User Question:** ${userQuery}
    `;
    
    // --- 7. Send to Your LLM Endpoint (Your Axios Logic) ---
    console.log('Sending request to LLM...');
    
    const payload = {
      model: 'your-llm-model-name',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: finalPrompt },
      ],
    };

    const response = await axios.post(YOUR_LLM_ENDPOINT, payload, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${YOUR_API_KEY}`,
      },
    });

    const answer = response.data.choices[0].message.content;
    console.log('\n--- LLM Answer ---');
    console.log(answer);
    
    return answer;

  } catch (error) {
    console.error('--- Query Failed ---');
    if (error.response) {
      console.error('Error Data:', error.response.data);
    } else {
      console.error(error.message);
    }
  }
}

// --- Get query from command line arguments ---
const userQuery = process.argv[2];
if (!userQuery) {
  console.log('Please provide a query. Usage: node query.js "Your question here"');
  process.exit(1);
}

queryRAG(userQuery);

