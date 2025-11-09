from openai import OpenAI
import os
import chromadb

openai_client = OpenAI()


PERSIST_DIR = os.getenv("CHROMA_DIR", "./data/chroma_store")
os.makedirs(PERSIST_DIR, exist_ok=True)

chroma = chromadb.PersistentClient(path=PERSIST_DIR)
coll = chroma.get_or_create_collection("portfolio_docs")
