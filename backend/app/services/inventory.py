"""Regras transacionais do estoque baseado em movimentações."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ConfiguracaoEstoque,
    DepositoEstoque,
    InventarioEstoque,
    InventarioEstoqueItem,
    MovimentacaoEstoque,
    Produto,
)
from app.schemas.inventory import (
    InventoryCreate,
    InventoryItemRead,
    InventoryRead,
    MovementType,
    StockMovementCreate,
    StockMovementRead,
)

POSITIVE_TYPES = {
    "ENTRADA",
    "AJUSTE_ENTRADA",
    "DEVOLUCAO_ENTRADA",
}
NEGATIVE_TYPES = {"SAIDA", "AJUSTE_SAIDA", "DEVOLUCAO_SAIDA"}


class InventoryNotFound(Exception):
    """Referência de estoque inexistente."""


class InventoryConflict(Exception):
    """Conflito de saldo, idempotência ou estado."""


class InventoryValidationError(Exception):
    """Dados de estoque inválidos."""


def get_inventory_config(db: Session) -> ConfiguracaoEstoque:
    config = db.get(ConfiguracaoEstoque, 1)
    if config is None:
        config = ConfiguracaoEstoque(id=1, permitir_saldo_negativo=False)
        db.add(config)
        db.flush()
    return config


def movement_effect(
    movement: MovimentacaoEstoque,
    movements: dict[int, MovimentacaoEstoque],
) -> Decimal:
    if movement.tipo in POSITIVE_TYPES:
        return movement.quantidade
    if movement.tipo in NEGATIVE_TYPES:
        return -movement.quantidade
    if movement.tipo == "REVERSAO":
        if movement.movimento_origem_id is None:
            raise InventoryConflict("Reversão sem movimento de origem.")
        source = movements.get(movement.movimento_origem_id)
        if source is None:
            raise InventoryConflict("Movimento de origem da reversão não encontrado.")
        return -movement_effect(source, movements)
    raise InventoryValidationError("Tipo de movimentação inválido.")


def calculate_balance(
    db: Session, product_id: int, deposit_id: int
) -> Decimal:
    movements = db.scalars(
        select(MovimentacaoEstoque)
        .where(
            MovimentacaoEstoque.produto_id == product_id,
            MovimentacaoEstoque.deposito_id == deposit_id,
        )
        .order_by(MovimentacaoEstoque.id)
    ).all()
    movement_map = {movement.id: movement for movement in movements}
    return sum(
        (movement_effect(movement, movement_map) for movement in movements),
        Decimal("0.000"),
    )


def ensure_product_deposit(
    db: Session, product_id: int, deposit_id: int
) -> tuple[Produto, DepositoEstoque]:
    product = db.get(Produto, product_id)
    if product is None:
        raise InventoryNotFound("Produto não encontrado.")
    deposit = db.get(DepositoEstoque, deposit_id)
    if deposit is None or not deposit.ativo:
        raise InventoryNotFound("Depósito não encontrado.")
    return product, deposit


def validate_movement_payload(
    db: Session, payload: StockMovementCreate
) -> tuple[Produto, DepositoEstoque]:
    product, deposit = ensure_product_deposit(
        db, payload.produto_id, payload.deposito_id
    )
    if payload.tipo == "REVERSAO":
        if payload.movimento_origem_id is None:
            raise InventoryValidationError(
                "Reversão exige o movimento de origem."
            )
        source = db.get(MovimentacaoEstoque, payload.movimento_origem_id)
        if source is None:
            raise InventoryNotFound("Movimento de origem não encontrado.")
        if source.tipo == "REVERSAO":
            raise InventoryValidationError("Não é permitido reverter uma reversão.")
        if source.produto_id != product.id or source.deposito_id != deposit.id:
            raise InventoryValidationError(
                "O movimento de origem precisa usar o mesmo produto e depósito."
            )
        already_reversed = db.scalar(
            select(MovimentacaoEstoque.id).where(
                MovimentacaoEstoque.movimento_origem_id == source.id
            )
        )
        if already_reversed is not None:
            raise InventoryConflict("O movimento já foi revertido.")
        if payload.quantidade != source.quantidade:
            raise InventoryValidationError(
                "A reversão deve usar a quantidade do movimento de origem."
            )
    if payload.tipo in {
        "AJUSTE_ENTRADA",
        "AJUSTE_SAIDA",
    } and not payload.observacao:
        raise InventoryValidationError("Ajuste exige motivo no campo observação.")
    return product, deposit


def create_movement(
    db: Session,
    payload: StockMovementCreate,
    *,
    user_id: int | None = None,
    commit: bool = True,
) -> MovimentacaoEstoque:
    if payload.chave_idempotencia:
        existing = db.scalar(
            select(MovimentacaoEstoque).where(
                MovimentacaoEstoque.chave_idempotencia
                == payload.chave_idempotencia
            )
        )
        if existing is not None:
            return existing
    validate_movement_payload(db, payload)
    movement = MovimentacaoEstoque(
        **payload.model_dump(),
        usuario_id=user_id,
    )
    db.add(movement)
    db.flush()
    if payload.tipo in NEGATIVE_TYPES:
        config = get_inventory_config(db)
        projected = calculate_balance(
            db, payload.produto_id, payload.deposito_id
        )
        if projected < 0 and not config.permitir_saldo_negativo:
            db.rollback()
            raise InventoryConflict(
                "A movimentação geraria saldo negativo para o produto."
            )
    if payload.tipo == "REVERSAO":
        config = get_inventory_config(db)
        projected = calculate_balance(
            db, payload.produto_id, payload.deposito_id
        )
        if projected < 0 and not config.permitir_saldo_negativo:
            db.rollback()
            raise InventoryConflict(
                "A reversão geraria saldo negativo para o produto."
            )
    if commit:
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise InventoryConflict(
                "A chave de idempotência já está associada a outra movimentação."
            ) from None
        db.refresh(movement)
    return movement


def get_movement(db: Session, movement_id: int) -> MovimentacaoEstoque | None:
    return db.get(MovimentacaoEstoque, movement_id)


def list_movements(db: Session, product_id: int | None, deposit_id: int | None):
    query = select(MovimentacaoEstoque).order_by(MovimentacaoEstoque.id.desc())
    if product_id is not None:
        query = query.where(MovimentacaoEstoque.produto_id == product_id)
    if deposit_id is not None:
        query = query.where(MovimentacaoEstoque.deposito_id == deposit_id)
    return db.scalars(query).all()


def list_balances(
    db: Session, deposit_id: int, product_id: int | None = None
):
    deposit = db.get(DepositoEstoque, deposit_id)
    if deposit is None or not deposit.ativo:
        raise InventoryNotFound("Depósito não encontrado.")
    query = select(Produto).where(Produto.ativo.is_(True)).order_by(Produto.id)
    if product_id is not None:
        query = query.where(Produto.id == product_id)
    products = db.scalars(query).all()
    return [
        {
            "produto_id": product.id,
            "deposito_id": deposit.id,
            "saldo": calculate_balance(db, product.id, deposit.id),
            "estoque_minimo": product.estoque_minimo,
            "abaixo_do_minimo": calculate_balance(db, product.id, deposit.id)
            < product.estoque_minimo,
        }
        for product in products
    ]


def movement_to_read(movement: MovimentacaoEstoque) -> StockMovementRead:
    return StockMovementRead.model_validate(movement)


def create_inventory(
    db: Session,
    payload: InventoryCreate,
    *,
    user_id: int | None = None,
) -> InventarioEstoque:
    deposit = db.get(DepositoEstoque, payload.deposito_id)
    if deposit is None or not deposit.ativo:
        raise InventoryNotFound("Depósito não encontrado.")
    product_ids = [item.produto_id for item in payload.itens]
    if len(product_ids) != len(set(product_ids)):
        raise InventoryValidationError(
            "O mesmo produto não pode aparecer duas vezes no inventário."
        )
    items: list[InventarioEstoqueItem] = []
    for item_payload in payload.itens:
        product = db.get(Produto, item_payload.produto_id)
        if product is None:
            raise InventoryNotFound("Produto não encontrado.")
        balance = calculate_balance(db, product.id, deposit.id)
        items.append(
            InventarioEstoqueItem(
                produto_id=product.id,
                saldo_sistema=balance,
                quantidade_contada=item_payload.quantidade_contada,
                diferenca=item_payload.quantidade_contada - balance,
            )
        )
    inventory = InventarioEstoque(
        deposito_id=deposit.id,
        data_inventario=payload.data_inventario,
        usuario_id=user_id,
        observacao=payload.observacao,
        itens=items,
    )
    db.add(inventory)
    db.commit()
    return get_inventory(db, inventory.id)  # type: ignore[return-value]


def get_inventory(db: Session, inventory_id: int) -> InventarioEstoque | None:
    return db.scalar(
        select(InventarioEstoque)
        .options(selectinload(InventarioEstoque.itens))
        .where(InventarioEstoque.id == inventory_id)
    )


def confirm_inventory(
    db: Session, inventory_id: int, *, user_id: int | None = None
) -> InventarioEstoque:
    inventory = get_inventory(db, inventory_id)
    if inventory is None:
        raise InventoryNotFound("Inventário não encontrado.")
    if inventory.status == "CONFIRMADO":
        return inventory
    if inventory.status != "RASCUNHO":
        raise InventoryConflict("Somente inventário em rascunho pode ser confirmado.")
    try:
        for item in inventory.itens:
            difference = item.quantidade_contada - calculate_balance(
                db, item.produto_id, inventory.deposito_id
            )
            if difference == 0:
                continue
            movement_type: MovementType = (
                "AJUSTE_ENTRADA" if difference > 0 else "AJUSTE_SAIDA"
            )
            movement = StockMovementCreate(
                produto_id=item.produto_id,
                deposito_id=inventory.deposito_id,
                tipo=movement_type,
                quantidade=abs(difference),
                data_movimentacao=datetime.now(timezone.utc),
                origem="INVENTARIO",
                documento_tipo="INVENTARIO",
                documento_id=inventory.id,
                observacao=inventory.observacao or "Ajuste de inventário",
                chave_idempotencia=f"INVENTARIO-{inventory.id}-{item.id}",
            )
            create_movement(db, movement, user_id=user_id, commit=False)
        inventory.status = "CONFIRMADO"
        db.commit()
    except Exception:
        db.rollback()
        raise
    return get_inventory(db, inventory.id)  # type: ignore[return-value]


def inventory_to_read(inventory: InventarioEstoque) -> InventoryRead:
    return InventoryRead(
        id=inventory.id,
        deposito_id=inventory.deposito_id,
        data_inventario=inventory.data_inventario,
        status=inventory.status,
        usuario_id=inventory.usuario_id,
        observacao=inventory.observacao,
        created_at=inventory.created_at,
        updated_at=inventory.updated_at,
        itens=[
            InventoryItemRead.model_validate(item) for item in inventory.itens
        ],
    )
