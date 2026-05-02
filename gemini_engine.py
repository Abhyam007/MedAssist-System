import google.generativeai as genai
from config import Config
import time

# Initialize model safely
if Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-flash-latest")
else:
    model = None


def basic_fallback(query):
    q = query.lower()

    if "headache" in q:
        return "Headaches can be caused by stress, dehydration, or migraines. If persistent, consult a doctor."

    if "fever" in q:
        return "Fever is usually due to infection. Stay hydrated and monitor temperature."

    if "chest pain" in q:
        return "Chest pain can be serious. Please seek immediate medical attention."

    return "⚠️ Unable to access AI service. Please try again or consult a doctor."


def ask_gemini(query, context):
    if not model:
        return basic_fallback(query)

    prompt = f"""
You are a medical assistant.

Use context if helpful, otherwise answer normally.

Context:
{context}

Question:
{query}

Answer briefly (2–3 lines).
End with: Consult a doctor if symptoms persist.
"""

    # Retry mechanism (handles intermittent failures)
    for _ in range(2):
        try:
            time.sleep(0.5)  # prevents rate-limit issues

            response = model.generate_content(prompt)

            if response.text:
                return response.text.strip()

        except Exception as e:
            print("[!] GEMINI ERROR:", str(e))
            continue

    # Final fallback
    return basic_fallback(query)
