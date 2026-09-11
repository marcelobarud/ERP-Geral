
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_authenticated, require_permission
from app.db.session import get_db_session
from app.models import DepositoEstoque, Usuario
from app.schemas.inventory import (
    DepositCreate,
    DepositRead,
    DepositUpdate,
    InventoryConfigRead,
    InventoryConfigUpdate,
    InventoryCreate,
    InventoryRead,
    StockBalanceRead,
    StockMovementCreate,
    StockMovementRead,
)
from app.services.auth import add_audit_log
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
    list_inventories,
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
    deposits = db.scalars(select(DepositoEstoque).order_by(DepositoEstoque.nome)).all()
    return [DepositRead.model_validate(deposit) for deposit in deposits]


@router.post(
    "/deposits",
    response_model=DepositRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("inventory:write"))],
)
def create_deposit(
    payload: DepositCreate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("inventory:write")),
) -> DepositRead:
    if payload.padrao:
        db.execute(update(DepositoEstoque).values(padrao=False))
    deposit = DepositoEstoque(**payload.model_dump())
    db.add(deposit)
    try:
        db.commit()
        db.refresh(deposit)
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="deposit_created",
            entity="deposito_estoque",
            entity_id=deposit.id,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Código de depósito já cadastrado."
        ) from None
    return DepositRead.model_validate(deposit)


@router.patch(
    "/deposits/{deposit_id}",
    response_model=DepositRead,
    dependencies=[Depends(require_permission("inventory:write"))],
)
def update_deposit(
    deposit_id: int,
    payload: DepositUpdate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("inventory:write")),
) -> DepositRead:
    deposit = db.get(DepositoEstoque, deposit_id)
    if deposit is None:
        raise HTTPException(status_code=404, detail="Depósito não encontrado.")
    data = payload.model_dump(exclude_unset=True)
    if data.get("padrao") is True:
        db.execute(update(DepositoEstoque).values(padrao=False))
    for field, value in data.items():
        setattr(deposit, field, value)
    try:
        db.commit()
        db.refresh(deposit)
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="deposit_updated",
            entity="deposito_estoque",
            entity_id=deposit.id,
        )
        db.commit()
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
    payload: InventoryConfigUpdate,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("inventory:write")),
) -> InventoryConfigRead:
    config = get_inventory_config(db)
    config.permitir_saldo_negativo = payload.permitir_saldo_negativo
    db.commit()
    db.refresh(config)
    add_audit_log(
        db,
        user_id=actor.id if actor else None,
        action="inventory_config_updated",
        entity="configuracao_estoque",
        entity_id=config.id,
    )
    db.commit()
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
    actor: Usuario | None = Depends(require_permission("inventory:write")),
) -> StockMovementRead:
    try:
        validate_movement_payload(db, payload)
        movement = create_movement(db, payload, user_id=actor.id if actor else None)
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="stock_movement_created",
            entity="movimentacao_estoque",
            entity_id=movement.id,
            metadata={"tipo": movement.tipo, "origem": movement.origem},
        )
        db.commit()
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
    actor: Usuario | None = Depends(require_permission("inventory:write")),
) -> InventoryRead:
    try:
        inventory = create_inventory(
            db, payload, user_id=actor.id if actor else None
        )
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="inventory_created",
            entity="inventario_estoque",
            entity_id=inventory.id,
        )
        db.commit()
        return inventory_to_read(inventory)
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


@router.get("/inventories", response_model=list[InventoryRead])
def list_stock_inventories(
    db: Session = Depends(get_db_session),
) -> list[InventoryRead]:
    return [inventory_to_read(item) for item in list_inventories(db)]


@router.post(
    "/inventories/{inventory_id}/confirm",
    response_model=InventoryRead,
    dependencies=[Depends(require_permission("inventory:write"))],
)
def confirm_stock_inventory(
    inventory_id: int,
    db: Session = Depends(get_db_session),
    actor: Usuario | None = Depends(require_permission("inventory:write")),
) -> InventoryRead:
    try:
        inventory = confirm_inventory(
            db, inventory_id, user_id=actor.id if actor else None
        )
        add_audit_log(
            db,
            user_id=actor.id if actor else None,
            action="inventory_confirmed",
            entity="inventario_estoque",
            entity_id=inventory_id,
        )
        db.commit()
        return inventory_to_read(inventory)
    except InventoryNotFound as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from None
    except InventoryValidationError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from None
    except InventoryConflict as exception:
        raise HTTPException(status_code=409, detail=str(exception)) from None
