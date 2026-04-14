from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserUpdate
from auth import get_current_user, hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db)
):
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(user)
    db.commit()
