from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db
from models import User
from schemas import LoginRequest, Token, UserCreate, UserResponse
from auth import hash_password, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    new_user = User(
        nombre=user_data.nombre,
        email=user_data.email,
        edad=user_data.edad,
        password_hash=hash_password(user_data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    print(user)
    print(credentials.password)
    if not user or not verify_password(credentials.password, user.password_hash):
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}
