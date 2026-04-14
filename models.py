from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime, timezone
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    edad = Column(Integer, nullable=False)
    password_hash = Column(String, nullable=False)

    ventas = relationship("Venta", back_populates="usuario")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    nombre = Column(String(150), unique=True, nullable=False, index=True)
    descripcion = Column(String(1000), nullable=True)
    precio = Column(Float, nullable=False)
    stock_disponible = Column(Integer, nullable=False)
    impuesto_pct = Column(Float, nullable=False, default=0.0)


class EstadoVenta(str, enum.Enum):
    pendiente = "pendiente"
    confirmada = "confirmada"
    cancelada = "cancelada"


class Venta(Base):
    __tablename__ = "ventas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subtotal = Column(Float, nullable=False)
    total_impuestos = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    estado = Column(SAEnum(EstadoVenta), nullable=False, default=EstadoVenta.pendiente)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    usuario = relationship("User", back_populates="ventas")
    items = relationship("ItemVenta", back_populates="venta", cascade="all, delete-orphan")


class ItemVenta(Base):
    __tablename__ = "items_venta"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venta_id = Column(UUID(as_uuid=True), ForeignKey("ventas.id"), nullable=False, index=True)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    impuesto_pct = Column(Float, nullable=False)
    impuesto_valor = Column(Float, nullable=False)
    subtotal_item = Column(Float, nullable=False)
    total_item = Column(Float, nullable=False)

    venta = relationship("Venta", back_populates="items")
