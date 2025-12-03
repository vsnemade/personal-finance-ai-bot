import faiss
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from config import INDEX_FILE, MODEL_NAME
import subprocess
import json

# ---------------------------
# Load data, model, and FAISS
# ---------------------------
print("Loading data...")
df = pd.read_pickle("data/transactions.pkl")

print("Loading model...")
embed_model = SentenceTransformer(MODEL_NAME)

print("Loading FAISS index...")
index = faiss.read_index(INDEX_FILE)

app = Flask(__name__)

# ---------------------------------------------------
# Helper: call local Llama3 using Ollama
# ---------------------------------------------------
def ask_ollama(prompt):
    command = ["ollama", "run", "llama3.1", prompt]
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


# ---------------------------------------------------
# Clean & parse JSON returned by Ollama
# ---------------------------------------------------
def parse_llm_json(response):
    clean = response.strip()

    # Remove markdown fences like ```json ... ```
    if clean.startswith("```"):
        clean = clean.strip("`").strip()

        # Remove leading "json" if exists
        if clean.lower().startswith("json"):
            clean = clean[4:].strip()

    # Try to parse cleaned text
    try:
        return json.loads(clean)
    except:
        return {
            "action": "error",
            "message": "Failed to parse JSON",
            "raw": response
        }


# ---------------------------------------------------
# Interpret user query using LLM (returns JSON)
# ---------------------------------------------------
def interpret_query(query):
    system_prompt = f"""
You are a finance AI. Convert the user question into a JSON command.

Dataset columns:
- Date
- Description
- Withdrawal Amt  (money user SENT)
- Deposit Amt     (money user RECEIVED)

Rules:
1. If question is about money SENT (transfer, paid, gave, sent, purchase):
   Use "Withdrawal Amt".

2. If question is about money RECEIVED (salary, refund, credited):
   Use "Deposit Amt".

3. For search queries, output:
   {{
      "action": "search",
      "keywords": ["amazon", "pooja"]
   }}

4. For totals, output:
   {{
      "action": "aggregate",
      "type": "sum",
      "field": "Withdrawal Amt",
      "filter": "Description.str.contains('pooja', case=False)"
   }}

5. Respond with JSON ONLY. No explanation.

User query: {query}
"""

    raw = ask_ollama(system_prompt)
    return parse_llm_json(raw)


# ---------------------------------------------------
# Semantic Search using FAISS
# ---------------------------------------------------
def semantic_search(keywords, k=20):
    query = " ".join(keywords)
    q_emb = embed_model.encode([query])
    distances, indices = index.search(np.array(q_emb), k)
    return df.iloc[indices[0]].to_dict(orient="records")


# ---------------------------------------------------
# Safe Aggregation Handler
# ---------------------------------------------------
def apply_aggregation(cmd):

    valid_fields = ["Withdrawal Amt", "Deposit Amt"]
    field = cmd.get("field")

    if field not in valid_fields:
        if field and ("deposit" in field.lower() or "received" in field.lower()):
            field = "Deposit Amt"
        else:
            field = "Withdrawal Amt"

    filtered = df
    if "filter" in cmd and cmd["filter"]:
        try:
            filtered = filtered.query(cmd["filter"])
        except Exception as e:
            return {"error": "Invalid filter", "details": str(e)}

    if cmd["type"] == "sum":
        value = filtered[field].sum()
        return {
            "result": float(value),
            "field_used": field,
            "rows_matched": len(filtered)
        }

    return {"error": "Unknown aggregation type"}


# ---------------------------------------------------
# API Endpoint
# ---------------------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    user_query = request.json.get("query")
    cmd = interpret_query(user_query)

    if cmd["action"] == "search":
        result = semantic_search(cmd["keywords"])
        return jsonify(result)

    elif cmd["action"] == "aggregate":
        result = apply_aggregation(cmd)
        return jsonify(result)

    else:
        return jsonify(cmd)


# ---------------------------------------------------
# Run App
# ---------------------------------------------------
if __name__ == "__main__":
    app.run(port=5000, debug=True)
