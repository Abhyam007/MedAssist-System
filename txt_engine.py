from config import Config

def load_txt():
    try:
        with open(Config.TXT_PATH, "r", encoding="utf-8") as f:
            return f.read().lower()
    except:
        return ""

# Global loading removed to allow per-request reloading

def search_txt(query):
    # Reload text data to ensure we have the latest updates
    data = load_txt()
    if not data:
        return None, 0
        
    q = query.lower().strip()
    
    # 1. Substring match (High confidence)
    if q in data:
        return data, 1
    
    # 2. Keyword match
    stop_words = {'what', 'is', 'the', 'a', 'an', 'and', 'are', 'for', 'how', 'to', 'do', 'does', 'in', 'of', 'any', 'tell', 'me', 'level', 'range'}
    keywords = [w for w in q.split() if w not in stop_words and len(w) > 2]
    
    if not keywords:
        return None, 0
        
    matches = sum(1 for k in keywords if k in data)
    
    # Threshold: Match at least 50% of the meaningful keywords
    if matches >= len(keywords) * 0.5 and matches > 0:
        return data, 1
        
    return None, 0