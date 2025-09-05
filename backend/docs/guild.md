# Project Guide

This project is a chat application built with FastAPI for the backend
and Next.js for the frontend. The backend stores chat sessions and
messages in PostgreSQL. The frontend uses TailwindCSS and React
components.

## Features

-   Secure authentication
-   Streaming responses via Server-Sent Events (SSE)
-   Local Retrieval-Augmented Generation (RAG) using text files in the docs folder

## How to Use

1. Place your .txt or .md files in the `docs/` folder.
2. Start the backend server with `uvicorn app.main:app --reload`.
3. Ask a question in the chat UI. If your question is related to the content
   of the files, the assistant will use them as context.
