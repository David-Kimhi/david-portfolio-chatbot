import os, time
from typing import List, Dict
from fastapi import Header, APIRouter, HTTPException
from pydantic import BaseModel
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()  # load .env

ADMIN_EMAIL = (os.getenv("ADMIN_EMAIL") or "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or ""
JWT_SECRET = os.getenv("JWT_SECRET") or "change_me"
JWT_ISS = os.getenv("JWT_ISS", "portfolio-chat")

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ----- MODELS -----
class LoginReq(BaseModel):
    email: str
    password: str

class IngestItem(BaseModel):
    id: str
    text: str
    meta: Dict[str, str] = {}

# ----- AUTH -----
@router.post("/login")
async def login(req: LoginReq):
    # single-user auth
    if req.email.strip().lower() != ADMIN_EMAIL.lower() or req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    now = int(time.time())
    token = jwt.encode(
        {
            "sub": req.email,
            "iss": JWT_ISS,
            "iat": now,
            "exp": now + 60 * 30,  # 30 minutes
        },
        JWT_SECRET,
        algorithm="HS256",
    )
    return {"access_token": token, "token_type": "bearer"}

def require_jwt(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("iss") != JWT_ISS:
            raise HTTPException(401, "Bad issuer")
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")