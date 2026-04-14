from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from database import get_db
from models import Producto
from schemas import ProductoCreate, ProductoUpdate, ProductoPatch, ProductoResponse
from auth import get_current_user

router = APIRouter(prefix="/products", tags=["products"])


def _get_or_404(product_id: UUID, db: Session) -> Producto:
    producto = db.query(Producto).filter(Producto.id == product_id).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return producto


def _check_nombre_unique(nombre: str, db: Session, exclude_id: UUID = None) -> None:
    query = db.query(Producto).filter(Producto.nombre == nombre)
    if exclude_id:
        query = query.filter(Producto.id != exclude_id)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ya existe un producto con ese nombre"
        )


@router.post("", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(
    data: ProductoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_nombre_unique(data.nombre, db)
    producto = Producto(**data.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


@router.get("", response_model=List[ProductoResponse], status_code=status.HTTP_200_OK)
def listar_productos(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    offset = (page - 1) * limit
    return db.query(Producto).offset(offset).limit(limit).all()


@router.get("/{product_id}", response_model=ProductoResponse, status_code=status.HTTP_200_OK)
def obtener_producto(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return _get_or_404(product_id, db)


@router.put("/{product_id}", response_model=ProductoResponse, status_code=status.HTTP_200_OK)
def actualizar_producto(
    product_id: UUID,
    data: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    producto = _get_or_404(product_id, db)
    _check_nombre_unique(data.nombre, db, exclude_id=product_id)
    for field, value in data.model_dump().items():
        setattr(producto, field, value)
    db.commit()
    db.refresh(producto)
    return producto


@router.patch("/{product_id}", response_model=ProductoResponse, status_code=status.HTTP_200_OK)
def actualizar_producto_parcial(
    product_id: UUID,
    data: ProductoPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    producto = _get_or_404(product_id, db)
    cambios = data.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] is not None:
        _check_nombre_unique(cambios["nombre"], db, exclude_id=product_id)
    for field, value in cambios.items():
        setattr(producto, field, value)
    db.commit()
    db.refresh(producto)
    return producto


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    producto = _get_or_404(product_id, db)
    db.delete(producto)
    db.commit()
