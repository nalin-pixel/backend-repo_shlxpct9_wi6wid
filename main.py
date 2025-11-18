import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from database import db, create_document, get_documents
from schemas import User, Blogpost, Contactmessage
from datetime import datetime

app = FastAPI(title="SaaS Landing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "ok", "service": "backend"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# -------------------- Auth (simple) --------------------
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Extremely simplified password hash util (demo purposes only)
import hashlib, secrets

def hash_password(password: str):
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed, salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    return hashlib.sha256((salt + password).encode()).hexdigest() == hashed

@app.post("/auth/signup")
def signup(payload: SignupRequest):
    # check existing
    existing = db["user"].find_one({"email": payload.email}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed, salt = hash_password(payload.password)
    user = User(name=payload.name, email=payload.email, password_hash=hashed, password_salt=salt)
    user_id = create_document("user", user)
    return {"ok": True, "user_id": user_id}

@app.post("/auth/login")
def login(payload: LoginRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = db["user"].find_one({"email": payload.email})
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(payload.password, doc.get("password_hash", ""), doc.get("password_salt", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # simple session token
    token = secrets.token_urlsafe(24)
    return {"ok": True, "token": token, "name": doc.get("name"), "email": doc.get("email")}


# -------------------- Blog --------------------
class CreatePostRequest(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    published: bool = True

@app.post("/blog")
def create_post(payload: CreatePostRequest):
    post = Blogpost(
        title=payload.title,
        slug=payload.slug,
        content=payload.content,
        excerpt=payload.excerpt,
        tags=payload.tags or [],
        author=payload.author,
        published=payload.published,
        published_at=datetime.utcnow() if payload.published else None,
    )
    post_id = create_document("blogpost", post)
    return {"ok": True, "post_id": post_id}

@app.get("/blog")
def list_posts(limit: int = 10):
    items = get_documents("blogpost", {"published": True}, limit)
    # convert ObjectId
    for it in items:
        it["_id"] = str(it.get("_id"))
        if it.get("published_at"):
            it["published_at"] = it["published_at"].isoformat()
    return {"ok": True, "items": items}

@app.get("/blog/{slug}")
def get_post(slug: str):
    doc = db["blogpost"].find_one({"slug": slug}) if db else None
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    doc["_id"] = str(doc.get("_id"))
    if doc.get("published_at"):
        doc["published_at"] = doc["published_at"].isoformat()
    return {"ok": True, "item": doc}


# -------------------- Contact --------------------
class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: Optional[str] = None
    message: str

@app.post("/contact")
def contact(payload: ContactRequest):
    msg = Contactmessage(name=payload.name, email=payload.email, subject=payload.subject, message=payload.message)
    msg_id = create_document("contactmessage", msg)
    return {"ok": True, "message_id": msg_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
