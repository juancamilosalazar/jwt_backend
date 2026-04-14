from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone

from database import get_db
from models import Venta, ItemVenta, Producto, EstadoVenta, User
from schemas import VentaCreate, VentaResponse
from auth import get_current_user

router = APIRouter(prefix="/sales", tags=["sales"])


def _get_venta_or_404(venta_id: UUID, db: Session) -> Venta:
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venta no encontrada")
    return venta


def _check_owner(venta: Venta, current_user: User) -> None:
    if venta.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para acceder a esta venta")


@router.post("", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
def crear_venta(
    data: VentaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validar existencia de productos y stock suficiente
    productos_map: dict[UUID, Producto] = {}
    for item in data.items:
        producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con id '{item.producto_id}' no encontrado",
            )
        if producto.stock_disponible < item.cantidad:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Stock insuficiente para el producto '{producto.nombre}' (disponible: {producto.stock_disponible}, solicitado: {item.cantidad})",
            )
        productos_map[item.producto_id] = producto

    # Calcular totales
    subtotal = 0.0
    total_impuestos = 0.0
    items_data = []

    for item in data.items:
        producto = productos_map[item.producto_id]
        precio_unitario = round(producto.precio, 2)
        impuesto_pct = producto.impuesto_pct
        subtotal_item = round(precio_unitario * item.cantidad, 2)
        impuesto_valor = round(subtotal_item * impuesto_pct / 100, 2)
        total_item = round(subtotal_item + impuesto_valor, 2)

        subtotal += subtotal_item
        total_impuestos += impuesto_valor

        items_data.append({
            "producto_id": item.producto_id,
            "cantidad": item.cantidad,
            "precio_unitario": precio_unitario,
            "impuesto_pct": impuesto_pct,
            "impuesto_valor": impuesto_valor,
            "subtotal_item": subtotal_item,
            "total_item": total_item,
        })

    subtotal = round(subtotal, 2)
    total_impuestos = round(total_impuestos, 2)
    total = round(subtotal + total_impuestos, 2)

    now = datetime.now(timezone.utc)
    venta = Venta(
        usuario_id=current_user.id,
        subtotal=subtotal,
        total_impuestos=total_impuestos,
        total=total,
        estado=EstadoVenta.pendiente,
        fecha_creacion=now,
        fecha_actualizacion=now,
    )
    db.add(venta)
    db.flush()  # obtener venta.id antes de agregar items

    for item_data in items_data:
        db.add(ItemVenta(venta_id=venta.id, **item_data))

    db.commit()
    db.refresh(venta)
    return venta


@router.get("", response_model=List[VentaResponse], status_code=status.HTTP_200_OK)
def listar_ventas(
    estado: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Venta).filter(Venta.usuario_id == current_user.id)

    if estado is not None:
        try:
            estado_enum = EstadoVenta(estado)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Estado inválido. Los valores permitidos son: pendiente, confirmada, cancelada",
            )
        query = query.filter(Venta.estado == estado_enum)

    offset = (page - 1) * limit
    return query.offset(offset).limit(limit).all()


@router.get("/{venta_id}", response_model=VentaResponse, status_code=status.HTTP_200_OK)
def obtener_venta(
    venta_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venta = _get_venta_or_404(venta_id, db)
    _check_owner(venta, current_user)
    return venta


@router.patch("/{venta_id}/confirm", response_model=VentaResponse, status_code=status.HTTP_200_OK)
def confirmar_venta(
    venta_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venta = _get_venta_or_404(venta_id, db)
    _check_owner(venta, current_user)

    if venta.estado != EstadoVenta.pendiente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo las ventas en estado 'pendiente' pueden confirmarse. Estado actual: '{venta.estado.value}'",
        )

    # Validar stock de forma atómica antes de descontar
    for item in venta.items:
        producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
        if not producto or producto.stock_disponible < item.cantidad:
            nombre = producto.nombre if producto else str(item.producto_id)
            disponible = producto.stock_disponible if producto else 0
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Stock insuficiente para el producto '{nombre}' (disponible: {disponible}, requerido: {item.cantidad})",
            )

    # Descontar stock
    for item in venta.items:
        producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
        producto.stock_disponible -= item.cantidad

    venta.estado = EstadoVenta.confirmada
    venta.fecha_actualizacion = datetime.now(timezone.utc)
    db.commit()
    db.refresh(venta)
    return venta


@router.patch("/{venta_id}/cancel", response_model=VentaResponse, status_code=status.HTTP_200_OK)
def cancelar_venta(
    venta_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venta = _get_venta_or_404(venta_id, db)
    _check_owner(venta, current_user)

    if venta.estado == EstadoVenta.confirmada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No es posible cancelar una venta ya confirmada",
        )
    if venta.estado == EstadoVenta.cancelada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La venta ya se encuentra cancelada",
        )

    venta.estado = EstadoVenta.cancelada
    venta.fecha_actualizacion = datetime.now(timezone.utc)
    db.commit()
    db.refresh(venta)
    return venta


@router.delete("/{venta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_venta(
    venta_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venta = _get_venta_or_404(venta_id, db)
    _check_owner(venta, current_user)

    if venta.estado != EstadoVenta.cancelada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo las ventas en estado 'cancelada' pueden eliminarse. Estado actual: '{venta.estado.value}'",
        )

    db.delete(venta)
    db.commit()
