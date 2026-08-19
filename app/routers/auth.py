from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from app.security import hash_password, verify_password, create_access_token
from app.rate_limit import limiter

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # slows down account-creation spam/abuse
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        # Deliberately generic — don't reveal whether the email exists to
        # someone probing the endpoint (email enumeration protection).
        raise HTTPException(status_code=400, detail="Could not register with these details")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        company_name=payload.company_name,
        country=payload.country,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")  # slows down brute-force password guessing
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Same generic error whether the email doesn't exist or the password is
    # wrong — again, don't leak which one it was.
    invalid_credentials = HTTPException(status_code=401, detail="Invalid email or password")

    if not user or not verify_password(payload.password, user.password_hash):
        raise invalid_credentials

    if not user.is_active:
        raise invalid_credentials

    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token)
