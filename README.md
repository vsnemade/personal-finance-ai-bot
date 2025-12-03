# Personal Finance AI Bot

A local AI-powered assistant to analyze your bank statements and provide insights through natural language queries. This bot allows you to **query your financial data securely on your local machine** without uploading sensitive data to any website. Its all local and so complete private and safe.  

---

## Table of Contents
- [Overview](#overview)  
- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Architecture & Flow](#architecture--flow)  
- [How the Local LLM Works](#how-the-local-llm-works)  
- [FAISS Index Creation](#faiss-index-creation)  
- [Steps to Run](#steps-to-run)  
- [Example Queries](#example-queries)  
- [Project Structure](#project-structure)  
- [Notes](#notes)  

---

## Overview
This bot allows you to:

- Search transactions by description (e.g., "Amazon shopping")  
- Calculate aggregates like total spending or earnings  
- Perform semantic search over bank statements  
- Interact via a REST API on your local machine  

All computations, embeddings, and LLM reasoning happen **locally**, ensuring privacy and fast responses.

---

## Features
- **Local LLM**: Uses Llama 3 via Ollama for parsing user queries into structured JSON commands.  
- **Semantic Search**: FAISS vector index for embedding-based search of transaction descriptions.  
- **Safe Aggregations**: Python Pandas handles summation or filtered calculations.  
- **REST API**: Flask app provides `/chat` endpoint to query your data.  
- **Offline & Private**: No sensitive data leaves your machine.  

---

## Tech Stack
- **Python 3.13+**  
- **Flask** – REST API  
- **Pandas** – Data manipulation  
- **FAISS** – Vector search index  
- **Sentence-Transformers** – Embeddings (`all-MiniLM-L6-v2`)  
- **Ollama / Llama 3** – Local LLM for query understanding  

---

## Installation

1. Clone the repository:

Project structure:
```bash
git clone <your-repo-url>
cd personal-finance-ai-bot

personal-finance-ai-bot/
│
├─ data/
│   └─ transactions.pkl       # Bank statement
│
├─ config.py                  # MODEL_NAME, INDEX_FILE
├─ build_index.py             # Build FAISS index
├─ app.py                     # Flask API
├─ requirements.txt
└─ README.md
```
## Steps to Run & Example Queries

### 1. Install dependencies
Install all required Python packages using:

```bash
pip install -r requirements.txt
```
### 2. Build FAISS index
Create embeddings for your transactions and build the FAISS index:
```bash
python build_index.py
```

### 3. Run the app

Start the Flask API server:
```bash
python app.py
```
The app will run locally at:
```bash
http://127.0.0.1:5000
```
### 4. Send queries to the API

Use a POST request to /chat with JSON payload:
```bash 
POST http://127.0.0.1:5000/chat
Content-Type: application/json

{
  "query": "give me my total earnings for November"
}
```

### How the Local LLM Works

The local LLM (llama3.1 via Ollama) receives a prompt containing the user query and dataset schema.

The model converts natural language queries into structured JSON commands:
```json
{
  "action": "search",
  "keywords": ["Amazon"]
}
```
or
```json
{
  "action": "aggregate",
  "type": "sum",
  "field": "Withdrawal Amt",
  "filter": "Description.str.contains('pooja', case=False)"
}
```

## FAISS Index Creation

The `build_index.py` script is responsible for creating the FAISS vector index used for semantic search.

### How it works:
1. **Load transaction data**  
   The script reads your bank statement data (Pickle or CSV) using Pandas.

2. **Create embeddings**  
   Each transaction description is converted into a vector embedding using the `all-MiniLM-L6-v2` model from Sentence-Transformers.

3. **Build FAISS index**  
   These embeddings are stored in a FAISS index on disk (`INDEX_FILE`) for fast similarity search.

4. **Semantic search capability**  
   The FAISS index allows the app to find transactions that are **semantically similar** to the user query, even if the exact keywords do not match.

### Usage
Run the following command to create the index:

```bash
python build_index.py
```
Once built, app.py can use this index for fast semantic search of transaction descriptions.

### Example Queries

| Query                                | Action                                                |
| ------------------------------------ | ----------------------------------------------------- |
| `show me all Amazon shopping`        | Search transactions in `Description` for "Amazon"     |
| `how much did I pay to Pooja`        | Aggregate sum on `Withdrawal Amt` filtered by "Pooja" |
| `total salary received in October`   | Aggregate sum on `Deposit Amt` filtered by "salary"   |
| `total money transferred to Rent`    | Aggregate sum on `Withdrawal Amt` filtered by "Rent"  |
| `all refunds received from Flipkart` | Search transactions in `Description` for "Flipkart"   |
