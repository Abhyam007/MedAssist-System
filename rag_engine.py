import os
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import Config

@st.cache_resource
def load_embedding():
    try:
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    except Exception as e:
        print("[!] EMBEDDING ERROR:", e)
        return None


@st.cache_resource
def load_db():
    try:
        if not os.path.exists(Config.DB_PATH):
            print("[!] FAISS not found")
            return None

        embedding_model = load_embedding()

        if embedding_model is None:
            return None

        db = FAISS.load_local(
            Config.DB_PATH,
            embedding_model,
            allow_dangerous_deserialization=True
        )
        return db

    except Exception as e:
        print("[!] FAISS ERROR:", e)
        return None


db = load_db()


def search_pdf(query):
    if db is None:
        return None, 0

    try:
        # Search with score (distance)
        # For FAISS, distance is L2. Lower is better.
        docs_with_scores = db.similarity_search_with_score(query, k=3)

        if not docs_with_scores:
            return None, 0

        # Calculate average distance
        avg_distance = sum([score for doc, score in docs_with_scores]) / len(docs_with_scores)
        
        # Threshold: For all-MiniLM-L6-v2, distance > 1.1 is usually weak
        if avg_distance > 1.15:
            return None, 0

        # Create context and extract page numbers
        contexts = []
        page_numbers = set()
        
        for doc, score in docs_with_scores:
            contexts.append(doc.page_content[:200])
            # Try to get page number from metadata
            page = doc.metadata.get("page")
            if page is not None:
                # Add 1 if it's 0-indexed
                page_numbers.add(str(page + 1) if isinstance(page, int) else str(page))
        
        context = " ".join(contexts)
        
        # Convert distance to a 0-100 score where higher is better
        relevance_score = max(0, min(100, int((1.3 - avg_distance) * 100)))

        # Append page info to context or return it separately?
        # Let's return it as part of the label in app.py logic
        source_suffix = ""
        if page_numbers:
            source_suffix = f" (Pages: {', '.join(sorted(page_numbers))})"

        return context, relevance_score, source_suffix

    except Exception as e:
        print("[!] SEARCH ERROR:", e)
        return None, 0, ""
