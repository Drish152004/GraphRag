# Apple Supply Chain Intelligence — Hybrid GraphRAG Platform

## Overview

An enterprise-style Hybrid GraphRAG platform focused on Apple supply chain intelligence.

The system combines:

- Graph Retrieval (Neo4j)
- Vector Retrieval (Semantic Search)
- FastAPI Backend
- React Frontend
- Redis-based Distributed Rate Limiting
- JWT Authentication
- Groq LLM Integration

The architecture is designed around retrieval orchestration rather than simple chatbot generation.

---

# Core Features

## Hybrid Retrieval Pipeline

```text
User Query
↓
Security Layer
↓
Query Cleaning
↓
Entity Detection
↓
Parallel Retrieval
    ├── Graph Retrieval (Neo4j)
    └── Vector Retrieval (Neo4j Vector Index)
↓
Context Fusion
↓
Groq LLM
↓
Frontend Response
```

### Retrieval Features

- Hybrid Graph + Vector Retrieval
- Entity-aware graph grounding
- Semantic vector search
- Context fusion pipeline
- Dynamic Cypher-based graph retrieval
- Neo4j vector index retrieval
- Query cleaning and normalization
- Prompt injection detection
- Toxicity filtering
- Domain guardrails

---

# Dynamic Graph Retrieval

The platform performs dynamic graph retrieval by:

- detecting entities from user queries
- grounding entities against graph nodes
- dynamically constructing graph retrieval logic
- retrieving connected relationships from Neo4j

Example graph retrieval pattern:

```cypher
MATCH (a)-[r]->(b)
WHERE ANY(e IN $entities WHERE
    toLower(coalesce(a.label, '')) CONTAINS toLower(e)
    OR toLower(coalesce(b.label, '')) CONTAINS toLower(e)
)
RETURN DISTINCT
    coalesce(a.label, '') AS source,
    type(r) AS relation,
    coalesce(b.label, '') AS target
```

The retrieval layer dynamically adapts graph retrieval based on:
- detected entities
- query intent
- graph grounding
- semantic relevance

---

# Tech Stack

## Frontend

- React
- Vite
- Tailwind CSS
- Glassmorphism UI
- ChatGPT-style conversational interface

## Backend

- FastAPI
- JWT Authentication
- PostgreSQL (Neon)
- Neo4j
- Redis Cloud
- Groq API
- SentenceTransformers

## Infrastructure

- Redis Cloud for scalable rate limiting
- Neo4j vector index for semantic retrieval
- Environment-based configuration

---

# Vector Retrieval

Semantic retrieval uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Features:

- chunk deduplication
- top-k filtering
- compact context formatting
- relevance-based retrieval

---

# Context Fusion

Fused context format:

```text
[GRAPH CONTEXT]
...

[VECTOR CONTEXT]
...
```

Fusion prioritizes:

- high precision
- low noise
- compact context windows
- deduplicated retrieval

---

# Security Layer

The backend includes:

- prompt injection detection
- toxicity filtering
- domain guardrails
- authenticated user sessions
- Redis-based rate limiting

---

# Redis-Based Rate Limiting

Distributed rate limiting is implemented using:

- Redis Cloud
- fastapi-limiter
- per-user JWT-based limits

Current policy:

```text
20 requests/minute per authenticated user
```

Fallback behavior:

- user ID → preferred
- IP address → fallback

---
# Environment Variables

## Backend `.env`

```env
GROQ_API_KEY=your_groq_key
HF_TOKEN=your_hf_token
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password
DATABASE_URL=your_postgres_url
REDIS_URL=your_redis_cloud_url
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Frontend `.env`

```env
VITE_API_URL=http://localhost:8001
```

---

# Installation

```bash
pip install -r requirements.txt
```

Run backend:

```bash
python -m uvicorn backend.main:app --reload --port 8001
```

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

# API Endpoints

## Authentication

```http
POST /api/auth/signup
POST /api/auth/login
```

## Chat Endpoint

```http
POST /api/chat
```

## Health Check

```http
GET /health
```

---

# Current Capabilities

- Hybrid Graph + Vector Retrieval
- Dynamic Cypher graph querying
- Entity-aware graph grounding
- Semantic chunk retrieval
- JWT Authentication
- Redis distributed rate limiting
- React conversational UI
- Groq-powered responses
- Retrieval debugging logs
- Compact context fusion

---

# Future Roadmap

- Retrieval evaluation framework
- Token usage tracking
- User quotas
- Retrieval reranking
- Lexical/BM25 retrieval
- Advanced graph ranking
- Observability and monitoring
- Retrieval analytics dashboard

---

# Design Philosophy

This project prioritizes:

- retrieval quality over LLM complexity
- precision-focused retrieval
- modular architecture
- scalable infrastructure
- enterprise-style orchestration

The system is designed to evolve incrementally while maintaining retrieval stability and response quality.

---

# Disclaimer

GraphRAG responses may contain inaccuracies.

Always verify important supply chain, sustainability, and operational decisions using trusted sources.
