from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# --- Auth ---

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# --- Users ---

class UserCreate(BaseModel):
    nombre: str
    email: str
    edad: int
    password: str


class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    edad: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    nombre: str
    email: str
    edad: int

    class Config:
        from_attributes = True


# --- Login ---

class LoginRequest(BaseModel):
    email: str
    password: str


# --- Productos ---

class ProductoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock_disponible: int
    impuesto_pct: float = 0.0

    @field_validator("nombre")
    @classmethod
    def nombre_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        if len(v) > 150:
            raise ValueError("El nombre no puede superar 150 caracteres")
        return v

    @field_validator("descripcion")
    @classmethod
    def descripcion_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 1000:
            raise ValueError("La descripción no puede superar 1000 caracteres")
        return v

    @field_validator("precio")
    @classmethod
    def precio_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        return round(v, 2)

    @field_validator("stock_disponible")
    @classmethod
    def stock_no_negativo(cls, v: int) -> int:
        if v < 0:
            raise ValueError("El stock disponible no puede ser negativo")
        return v

    @field_validator("impuesto_pct")
    @classmethod
    def impuesto_pct_valido(cls, v: float) -> float:
        if v < 0 or v > 100:
            raise ValueError("El impuesto_pct debe estar entre 0 y 100")
        return v


class ProductoUpdate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock_disponible: int
    impuesto_pct: float = 0.0

    @field_validator("nombre")
    @classmethod
    def nombre_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        if len(v) > 150:
            raise ValueError("El nombre no puede superar 150 caracteres")
        return v

    @field_validator("descripcion")
    @classmethod
    def descripcion_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 1000:
            raise ValueError("La descripción no puede superar 1000 caracteres")
        return v

    @field_validator("precio")
    @classmethod
    def precio_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        return round(v, 2)

    @field_validator("stock_disponible")
    @classmethod
    def stock_no_negativo(cls, v: int) -> int:
        if v < 0:
            raise ValueError("El stock disponible no puede ser negativo")
        return v

    @field_validator("impuesto_pct")
    @classmethod
    def impuesto_pct_valido(cls, v: float) -> float:
        if v < 0 or v > 100:
            raise ValueError("El impuesto_pct debe estar entre 0 y 100")
        return v


class ProductoPatch(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    stock_disponible: Optional[int] = None
    impuesto_pct: Optional[float] = None

    @field_validator("nombre")
    @classmethod
    def nombre_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 3:
                raise ValueError("El nombre debe tener al menos 3 caracteres")
            if len(v) > 150:
                raise ValueError("El nombre no puede superar 150 caracteres")
        return v

    @field_validator("descripcion")
    @classmethod
    def descripcion_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 1000:
            raise ValueError("La descripción no puede superar 1000 caracteres")
        return v

    @field_validator("precio")
    @classmethod
    def precio_positivo(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError("El precio debe ser mayor a 0")
            return round(v, 2)
        return v

    @field_validator("stock_disponible")
    @classmethod
    def stock_no_negativo(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("El stock disponible no puede ser negativo")
        return v

    @field_validator("impuesto_pct")
    @classmethod
    def impuesto_pct_valido(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v > 100):
            raise ValueError("El impuesto_pct debe estar entre 0 y 100")
        return v


class ProductoResponse(BaseModel):
    id: UUID
    nombre: str
    descripcion: Optional[str]
    precio: float
    stock_disponible: int
    impuesto_pct: float

    class Config:
        from_attributes = True


# --- Ventas ---

class ItemVentaCreate(BaseModel):
    producto_id: UUID
    cantidad: int

    @field_validator("cantidad")
    @classmethod
    def cantidad_positiva(cls, v: int) -> int:
        if v < 1:
            raise ValueError("La cantidad debe ser mayor o igual a 1")
        return v


class VentaCreate(BaseModel):
    items: List[ItemVentaCreate]

    @field_validator("items")
    @classmethod
    def items_no_vacio(cls, v: List[ItemVentaCreate]) -> List[ItemVentaCreate]:
        if not v:
            raise ValueError("Se debe enviar al menos un ítem para crear la venta")
        return v


class ItemVentaResponse(BaseModel):
    id: UUID
    producto_id: UUID
    cantidad: int
    precio_unitario: float
    impuesto_pct: float
    impuesto_valor: float
    subtotal_item: float
    total_item: float

    class Config:
        from_attributes = True


class VentaResponse(BaseModel):
    id: UUID
    usuario_id: int
    items: List[ItemVentaResponse]
    subtotal: float
    total_impuestos: float
    total: float
    estado: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True
