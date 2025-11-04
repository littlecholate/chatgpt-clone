/*
 * query.js
 * Run this script to ask questions about your document.
 * Usage: node query.js "What is RAG?"
 */

import { HuggingFaceTransformersEmbeddings } from '@langchain/community/embeddings/hf';
import { Chroma } from '@langchain/community/vectorstores/chroma';
import axios from 'axios';

// --- Configuration ---
const COLLECTION_NAME = 'my_txt_collection'; // Must match your ingest script
const CHROMA_URL = 'http://localhost:8000';
const YOUR_LLM_ENDPOINT = 'http://your-llm-api-endpoint.com/v1/chat'; // Your LLM API
const YOUR_API_KEY = 'YOUR_SECRET_API_KEY'; // Your LLM API key

// --- 1. Initialize Embedding Model (Must be the same as ingestion) ---
const embeddings = new HuggingFaceTransformersEmbeddings({
  modelName: 'Xenova/all-MiniLM-L6-v2',
});

// --- 2. Initialize Chroma Vector Store for retrieval ---
const vectorStore = new Chroma(embeddings, {
  collectionName: COLLECTION_NAME,
  url: CHROMA_URL,
});

/**
 * Main query function
 * @param {string} userQuery The user's question
 */
async function queryRAG(userQuery) {
  console.log(`User Query: "${userQuery}"`);
  
  try {
    // --- 3. Retrieve Relevant Documents ---
    // This searches ChromaDB and returns the 2 most similar chunks
    console.log('Searching for relevant context in ChromaDB...');
    const relevantDocs = await vectorStore.similaritySearch(userQuery, 2);

    // --- 4. Format the Context ---
    const context = relevantDocs
      .map((doc) => doc.pageContent)
      .join('\n\n---\n\n'); // Join docs with a separator

    console.log('Context retrieved. Building prompt...');
    
    // --- 5. Build the Prompt for the LLM ---
    const systemPrompt = `You are a helpful assistant. Answer the user's question based *only* on the following context. If the answer is not in the context, say "I do not know".`;

    const finalPrompt = `
      **Context:**
      ${context}

      ---

      **User Question:** ${userQuery}
    `;
    
    // --- 6. Send to Your LLM Endpoint (Your Axios Logic) ---
    console.log('Sending request to LLM...');
    
    const payload = {
      model: 'your-llm-model-name', // e.g., 'gpt-4'
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

    // --- 7. Return the Answer ---
    // This assumes a standard OpenAI-like response structure
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

// Run the query
queryRAG(userQuery);
