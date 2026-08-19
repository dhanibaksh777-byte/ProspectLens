"""
get_current_user is a FastAPI dependency — any route that needs auth just
adds `current_user: User = Depends(get_current_user)` to its function
signature. FastAPI runs this first, and if it raises 401, the route body
never executes.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise unauthorized

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise unauthorized

    return user
