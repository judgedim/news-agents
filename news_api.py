from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
bearer_scheme = HTTPBearer()

# Персональний токен для авторизації (зберігайте у .env!)
API_TOKEN = os.getenv("API_TOKEN", "supersecrettoken")

# Перевірка токена
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@app.get("/news", dependencies=[Depends(verify_token)])
def get_news(limit: int = 10):
    conn = sqlite3.connect("articles.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, summary, link, published, category FROM articles ORDER BY id DESC LIMIT ?", (limit,))
    news = [
        {
            "title": row[0],
            "summary": row[1],
            "link": row[2],
            "published": row[3],
            "category": row[4]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return {"news": news} 