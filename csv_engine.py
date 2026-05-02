import pandas as pd
from config import Config

df = pd.read_csv(Config.CSV_PATH)

def normalize(text):
    return str(text).lower().strip()

STOP_WORDS = {'what', 'is', 'the', 'a', 'an', 'and', 'are', 'for', 'how', 'to', 'do', 'does', 'in', 'of', 'about', 'is', 'any'}

def search_csv(query):
    q = normalize(query)
    
    # 1. Try Exact/Partial Match first (High confidence)
    for _, row in df.iterrows():
        question = normalize(row.get("question", ""))
        if q == question or (len(q) > 10 and q in question):
            return str(row.get("answer", "")), 1

    # 2. Keyword Match (Stricter)
    q_words = [w for w in q.split() if w not in STOP_WORDS and len(w) > 2]
    if not q_words:
        return None, 0

    for _, row in df.iterrows():
        question = normalize(row.get("question", ""))
        row_words = [w for w in question.split() if w not in STOP_WORDS and len(w) > 2]
        
        matches = sum(1 for w in q_words if w in row_words)
        
        # Must match at least 60% of the meaningful query words
        if matches >= len(q_words) * 0.6 and matches > 0:
            return str(row.get("answer", "")), 1

    return None, 0