
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import DepositoEstoque
from app.schemas.inventory import (
    DepositCreate,
    DepositRead,
    InventoryConfigRead,
    InventoryConfigUpdate,
    InventoryCreate,
    InventoryRead,
    StockBalanceRead,
    StockMovementCreate,
    StockMovementRead,
)
from app.services.inventory import (
    InventoryConflict,
    InventoryNotFound,
    InventoryValidationError,
    confirm_inventory,
    create_inventory,
    create_movement,
    get_inventory,
    get_inventory_config,
    inventory_to_read,
    list_balances,
    list_movements,
    movement_to_read,
    validate_movement_payload,
)

router = APIRouter(
    prefix="/api/inventory",
    tags=["inventory"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("/deposits", response_model=list[DepositRead])
def list_deposits(db: Session = Depends(get_db_session)) -> list[DepositRead]:
    deposits = db.scalars(
        select(DepositoEstoque)
        .where(DepositoEstoque.ativo.is_(True))
        .order_by(DepositoEstoque.nome)
    ).all()
    return [DepositRead.model_validate(deposit) for deposit in deposits]


@router.post(
    "/deposits",
    response_model=DepositRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("inventory:write"))],
)
def create_deposit(
    payload: DepositCreate, db: Session = Depends(get_db_session)
) -> DepositRead:
    if payload.padrao:
        db.execute(update(DepositoEstoque).values(padrao=False))
    deposit = DepositoEstoque(**payload.model_dump())
    db.add(deposit)
    try:
        db.commit()
        db.refresh(deposit)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Código de depósito já cadastrado."
        ) from None
    return DepositRead.model_validate(deposit)


@router.get("/config", response_model=InventoryConfigRead)
def read_inventory_config(
    db: Session = Depends(get_db_session),
) -> InventoryConfigRead:
    config = get_inventory_config(db)
    db.commit()
    return InventoryConfigRead.model_validate(config)


@router.patch(
    "/config",
    response_model=InventoryConfigRead,
    dependencies=[Depends(require_permission("inventory:write"))],
)
def update_inventory_config(
    payload: InventoryConfigUpdate, db: Session = Depends(get_db_session)
) -> InventoryConfigRead:
    config = get_inventory_config(db)
    config.permitir_saldo_negativo = payload.permitir_saldo_negativo
    db.commit()
    db.refresh(config)
    return InventoryConfigRead.model_validate(config)


@router.get("/movements", response_model=list[StockMovementRead])
def read_movements(
    product_id: int | None = Query(default=None, gt=0),
    deposit_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db_session),
) -> list[StockMovementRead]:
    return [
        movement_to_read(movement)
        for movement in list_movements(db, product_id, deposit_id)
    ]


@router.post(
    "/movements",
    response_model=StockMovementRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("inventory:write"))],
)
def create_stock_movement(
    payload: StockMovementCreate,
    db: Session = Depends(get_db_session),
) -> StockMovementRead:
    try:
        validate_movement_payload(db, payload)
        movement = create_movement(db, payload)
        return movement_to_read(movement)
    except InventoryNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except InventoryValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except InventoryConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None


@router.get("/balances", response_model=list[StockBalanceRead])
def read_balances(
    deposit_id: int = Query(gt=0),
    product_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db_session),
) -> list[StockBalanceRead]:
    try:
        return [
            StockBalanceRead.model_validate(item)
            for item in list_balances(db, deposit_id, product_id)
        ]
    except InventoryNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None


@router.post(
    "/inventories",
    response_model=InventoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("inventory:write"))],
)
def create_stock_inventory(
    payload: InventoryCreate,
    db: Session = Depends(get_db_session),
) -> InventoryRead:
    try:
        return inventory_to_read(create_inventory(db, payload))
    except InventoryNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except InventoryValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None


@router.get("/inventories/{inventory_id}", response_model=InventoryRead)
def read_stock_inventory(
    inventory_id: int, db: Session = Depends(get_db_session)
) -> InventoryRead:
    inventory = get_inventory(db, inventory_id)
    if inventory is None:
        raise HTTPException(status_code=404, detail="Inventário não encontrado.")
    return inventory_to_read(inventory)


@router.post(
    "/inventories/{inventory_id}/confirm",
    response_model=InventoryRead,
    dependencies=[Depends(require_permission("inventory:write"))],
)
def confirm_stock_inventory(
    inventory_id: int, db: Session = Depends(get_db_session)
) -> InventoryRead:
    try:
        return inventory_to_read(confirm_inventory(db, inventory_id))
    except InventoryNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except InventoryValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except InventoryConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None
