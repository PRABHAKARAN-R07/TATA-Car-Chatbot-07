TATA CAR GUIDE UI UPDATE

Files:
- app.py: FastAPI backend (uses your existing chatbot.py)
- static/index.html: UI
- static/style.css: styling
- static/script.js: chat interactions
- static/tata-safari.png: provided Tata Safari image

IMPORTANT:
1. Copy these files into your existing project. Keep your current chatbot.py, .env,
   Chroma database, and brochure documents.
2. The image is expected at static/tata-safari.png.
3. The frontend calls POST /chat and expects ask(question) to return either:
   (answer, sources) or just answer.
4. Run from the project root:
   python -m pip install fastapi uvicorn
   python -m uvicorn app:app --reload
5. Open http://127.0.0.1:8000
6. Do not share your .env or Groq API key.
