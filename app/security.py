"""
Two jobs live here:
1. Password hashing — using Argon2id (via pwdlib), the current recommended
   algorithm. We NEVER store plain passwords, and hashes are one-way
   (can't be reversed, only verified against).
2. JWT tokens — short-lived signed tokens issued at login. The token itself
   holds the user's id (as "sub"), so we don't need a server-side session
   store. Anyone with a valid, unexpired token is trusted as that user.
"""
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings

password_hasher = PasswordHash.recommended()  # currently resolves to Argon2id

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(plain_password: str) -> str:
    return password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_hasher.verify(plain_password, password_hash)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.api_secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Returns the user_id from a valid token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.api_secret_key, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
