import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User as UserSchema

app = FastAPI(title="Ashen API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

ADMIN_USER = os.getenv("ASHEN_ADMIN_USER", "joost")
ADMIN_PASS = os.getenv("ASHEN_ADMIN_PASS", "Ollie.vdl2004!!")


def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if not (credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


# Helpers
class PublicUser(BaseModel):
    username: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


def to_public_user(doc: dict) -> PublicUser:
    return PublicUser(
        username=doc.get("username"),
        display_name=doc.get("display_name"),
        bio=doc.get("bio"),
        avatar_url=doc.get("avatar_url"),
    )


def serialize(doc: dict) -> dict:
    if not doc:
        return doc
    d = {**doc}
    if isinstance(d.get("_id"), ObjectId):
        d["_id"] = str(d["_id"])
    return d


@app.get("/")
def read_root():
    return {"app": "Ashen API", "status": "ok"}


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
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
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
    return response


# Public endpoints
@app.get("/api/users", response_model=List[PublicUser])
def list_public_users():
    docs = get_documents("user", {}, limit=100)
    return [to_public_user(doc) for doc in docs]


@app.post("/api/users")
def create_user(user: UserSchema):
    # Check unique username
    existing = db["user"].find_one({"username": user.username}) if db else None
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    # Optional: unique email
    existing_email = db["user"].find_one({"email": user.email}) if db else None
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already registered")
    inserted_id = create_document("user", user)
    return {"id": inserted_id, "username": user.username}


# Admin endpoints (protected)
@app.get("/api/admin/users")
def admin_list_users(_=Depends(require_admin)):
    docs = get_documents("user")
    return [serialize(doc) for doc in docs]


@app.delete("/api/admin/users/{username}")
def admin_delete_user(username: str, _=Depends(require_admin)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    res = db["user"].delete_one({"username": username})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted", "username": username}


@app.post("/api/admin/login")
def admin_login(_=Depends(require_admin)):
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
