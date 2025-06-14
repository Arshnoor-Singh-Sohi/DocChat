# test_env.py
import os
from dotenv import load_dotenv

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    print(f"✅ OpenAI key found: sk-...{openai_key[-4:]}")
else:
    print("❌ OpenAI key NOT found!")

qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
print(f"📍 Qdrant URL: {qdrant_url}")