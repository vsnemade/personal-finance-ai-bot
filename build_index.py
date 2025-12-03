import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import MODEL_NAME, INDEX_FILE, EXCEL_FILE

print("Loading Excel...")
df = pd.read_excel(EXCEL_FILE)

if "Description" not in df.columns:
    raise Exception("Excel must contain a column named 'Description'")

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("Generating embeddings...")
texts = df["Description"].astype(str).tolist()
embeddings = model.encode(texts)

dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)

print("Adding vectors to FAISS index...")
index.add(np.array(embeddings))

print("Saving index...")
faiss.write_index(index, INDEX_FILE)

df.to_pickle("data/transactions.pkl")

print("Index build complete!")
