import os
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Cliente, Fornecedor, Funcionario, Produto, Venda, VendaItem
from app.schemas.sales import VendaCancel
from app.services.sales import cancel_sale

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="defina TEST_DATABASE_URL para executar os testes PostgreSQL",
)


def make_supplier() -> Fornecedor:
    return Fornecedor(
        nome="Fornecedor de teste",
        cidade="São Paulo",
        estado="SP",
        rua="Rua A",
        numero="10A",
        cnpj="12.345.678/0001-90",
    )


def make_customer() -> Cliente:
    return Cliente(
        nome="Cliente de teste",
        cidade="São Paulo",
        estado="SP",
        rua="Rua B",
        numero="S/N",
    )


def make_employee() -> Funcionario:
    return Funcionario(
        nome_completo="Funcionário de teste",
        cidade="São Paulo",
        estado="SP",
        rua="Rua C",
        numero="20",
        cpf="123.456.789-09",
        data_nascimento=date(1990, 1, 1),
    )


def make_product(supplier: Fornecedor, name: str = "Produto de teste") -> Produto:
    return Produto(
        nome=name,
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=Decimal("15.50"),
        fornecedor=supplier,
    )


def test_can_persist_all_entities_and_multiple_items(session: Session) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()
    product_one = make_product(supplier, "Produto 1")
    product_two = make_product(supplier, "Produto 2")
    session.add_all([supplier, customer, employee, product_one, product_two])
    session.flush()
    assert product_one.fornecedor_id is not None
    assert product_two.fornecedor_id is not None
    sale = Venda(
        cliente=customer,
        funcionario=employee,
        data_venda=datetime.now(timezone.utc),
        itens=[
            VendaItem(
                produto=product_one,
                quantidade=Decimal("2.000"),
                preco_unitario=Decimal("15.50"),
                fornecedor_id=product_one.fornecedor_id,
            ),
            VendaItem(
                produto=product_two,
                quantidade=Decimal("1.500"),
                preco_unitario=Decimal("20.00"),
                fornecedor_id=product_two.fornecedor_id,
            ),
        ],
    )

    session.add(sale)
    session.commit()

    assert supplier.id is not None
    assert customer.id is not None
    assert employee.id is not None
    assert product_one.id is not None
    assert sale.id is not None
    assert len(sale.itens) == 2
    assert sale.itens[0].preco_unitario == Decimal("15.50")
    assert employee.rg is None
    assert customer.complemento is None


def test_database_rejects_null_in_required_column(session: Session) -> None:
    supplier = make_supplier()
    invalid_product = Produto(
        nome="Produto inválido",
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=None,
        fornecedor=supplier,
    )
    session.add(invalid_product)

    with pytest.raises(IntegrityError):
        session.commit()


def test_database_accepts_null_optional_fields(session: Session) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()

    session.add_all([supplier, customer, employee])
    session.commit()

    assert supplier.complemento is None
    assert customer.complemento is None
    assert employee.complemento is None
    assert employee.rg is None


def test_duplicate_cpf_is_rejected(session: Session) -> None:
    first = make_employee()
    second = make_employee()
    second.nome_completo = "Outro funcionário"

    session.add_all([first, second])

    with pytest.raises(IntegrityError):
        session.commit()


def test_duplicate_cnpj_is_rejected(session: Session) -> None:
    first = make_supplier()
    second = make_supplier()
    second.nome = "Outro fornecedor"

    session.add_all([first, second])

    with pytest.raises(IntegrityError):
        session.commit()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("preco_custo", Decimal("-0.01")),
        ("preco_venda", Decimal("-0.01")),
    ],
)
def test_negative_product_prices_are_rejected(
    session: Session,
    field: str,
    value: Decimal,
) -> None:
    supplier = make_supplier()
    product = make_product(supplier)
    setattr(product, field, value)
    session.add(product)

    with pytest.raises(IntegrityError):
        session.commit()


@pytest.mark.parametrize("quantity", [Decimal("0"), Decimal("-1")])
def test_non_positive_quantities_are_rejected(
    session: Session,
    quantity: Decimal,
) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()
    product = make_product(supplier)
    session.add_all([supplier, customer, employee, product])
    session.flush()
    assert product.fornecedor_id is not None
    sale = Venda(
        cliente=customer,
        funcionario=employee,
        data_venda=datetime.now(timezone.utc),
        itens=[
            VendaItem(
                produto=product,
                quantidade=quantity,
                preco_unitario=Decimal("15.50"),
                fornecedor_id=product.fornecedor_id,
            )
        ],
    )
    session.add(sale)

    with pytest.raises(IntegrityError):
        session.commit()


def test_negative_item_price_is_rejected(session: Session) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()
    product = make_product(supplier)
    session.add_all([supplier, customer, employee, product])
    session.flush()
    assert product.fornecedor_id is not None
    sale = Venda(
        cliente=customer,
        funcionario=employee,
        data_venda=datetime.now(timezone.utc),
        itens=[
            VendaItem(
                produto=product,
                quantidade=Decimal("1.000"),
                preco_unitario=Decimal("-0.01"),
                fornecedor_id=product.fornecedor_id,
            )
        ],
    )
    session.add(sale)

    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_product_supplier_foreign_key_is_rejected(session: Session) -> None:
    product = Produto(
        nome="Produto sem fornecedor",
        categoria="Geral",
        preco_custo=Decimal("10.00"),
        preco_venda=Decimal("15.50"),
        fornecedor_id=999999,
    )
    session.add(product)

    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_sale_customer_foreign_key_is_rejected(session: Session) -> None:
    employee = make_employee()
    session.add(employee)
    session.flush()
    sale = Venda(
        cliente_id=999999,
        funcionario_id=employee.id,
        data_venda=datetime.now(timezone.utc),
    )
    session.add(sale)

    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_sale_employee_foreign_key_is_rejected(session: Session) -> None:
    customer = make_customer()
    session.add(customer)
    session.flush()
    sale = Venda(
        cliente_id=customer.id,
        funcionario_id=999999,
        data_venda=datetime.now(timezone.utc),
    )
    session.add(sale)

    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_item_sale_foreign_key_is_rejected(session: Session) -> None:
    supplier = make_supplier()
    product = make_product(supplier)
    session.add(product)
    session.flush()
    item = VendaItem(
        venda_id=999999,
        produto_id=product.id,
        quantidade=Decimal("1.000"),
        preco_unitario=Decimal("15.50"),
        fornecedor_id=product.fornecedor_id,
    )
    session.add(item)

    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_item_product_foreign_key_is_rejected(session: Session) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()
    sale = Venda(
        cliente=customer,
        funcionario=employee,
        data_venda=datetime.now(timezone.utc),
    )
    session.add_all([supplier, sale])
    session.flush()
    item = VendaItem(
        venda_id=sale.id,
        produto_id=999999,
        quantidade=Decimal("1.000"),
        preco_unitario=Decimal("15.50"),
        fornecedor_id=supplier.id,
    )
    session.add(item)

    with pytest.raises(IntegrityError):
        session.commit()


def test_referenced_records_cannot_be_deleted(session: Session) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()
    product = make_product(supplier)
    session.add_all([supplier, customer, employee, product])
    session.flush()
    assert product.fornecedor_id is not None
    sale = Venda(
        cliente=customer,
        funcionario=employee,
        data_venda=datetime.now(timezone.utc),
        itens=[
            VendaItem(
                produto=product,
                quantidade=Decimal("1.000"),
                preco_unitario=Decimal("15.50"),
                fornecedor_id=product.fornecedor_id,
            )
        ],
    )
    session.add(sale)
    session.commit()

    session.delete(product)

    with pytest.raises(IntegrityError):
        session.commit()


def test_referenced_customer_cannot_be_deleted(session: Session) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()
    product = make_product(supplier)
    session.add_all([supplier, customer, employee, product])
    session.flush()
    assert product.fornecedor_id is not None
    sale = Venda(
        cliente=customer,
        funcionario=employee,
        data_venda=datetime.now(timezone.utc),
        itens=[
            VendaItem(
                produto=product,
                quantidade=Decimal("1.000"),
                preco_unitario=Decimal("15.50"),
                fornecedor_id=product.fornecedor_id,
            )
        ],
    )
    session.add(sale)
    session.commit()

    session.delete(customer)

    with pytest.raises(IntegrityError):
        session.commit()


def test_same_sale_can_have_multiple_items(session: Session) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()
    product_one = make_product(supplier, "Produto 1")
    product_two = make_product(supplier, "Produto 2")
    session.add_all([supplier, customer, employee, product_one, product_two])
    session.flush()
    assert product_one.fornecedor_id is not None
    assert product_two.fornecedor_id is not None
    sale = Venda(
        cliente=customer,
        funcionario=employee,
        data_venda=datetime.now(timezone.utc),
    )
    sale.itens.extend(
        [
            VendaItem(
                produto=product_one,
                quantidade=Decimal("1.000"),
                preco_unitario=Decimal("10.00"),
                fornecedor_id=product_one.fornecedor_id,
            ),
            VendaItem(
                produto=product_two,
                quantidade=Decimal("2.000"),
                preco_unitario=Decimal("12.00"),
                fornecedor_id=product_two.fornecedor_id,
            ),
        ]
    )
    session.add(sale)
    session.commit()

    item_count = session.scalar(
        select(func.count(VendaItem.id)).where(VendaItem.venda_id == sale.id)
    )
    assert item_count == 2


def test_cancel_sale_preserves_items_and_root_records(
    session: Session,
) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()
    product_one = make_product(supplier, "Produto 1")
    product_two = make_product(supplier, "Produto 2")
    session.add_all([supplier, customer, employee, product_one, product_two])
    session.flush()
    assert product_one.fornecedor_id is not None
    assert product_two.fornecedor_id is not None
    sale = Venda(
        cliente=customer,
        funcionario=employee,
        data_venda=datetime.now(timezone.utc),
        itens=[
            VendaItem(
                produto=product_one,
                quantidade=Decimal("1.000"),
                preco_unitario=Decimal("15.50"),
                fornecedor_id=product_one.fornecedor_id,
            ),
            VendaItem(
                produto=product_two,
                quantidade=Decimal("2.000"),
                preco_unitario=Decimal("15.50"),
                fornecedor_id=product_two.fornecedor_id,
            ),
        ],
    )
    session.add(sale)
    session.commit()
    sale_id = sale.id

    cancelled = cancel_sale(session, sale_id, VendaCancel(motivo="Ajuste"))

    assert cancelled.status == "CANCELADA"
    assert cancelled.motivo_cancelamento == "Ajuste"
    assert session.get(Venda, sale_id) is not None
    assert len(session.scalars(
        select(VendaItem).where(VendaItem.venda_id == sale_id)
    ).all()) == 2
    assert session.get(Cliente, customer.id) is not None
    assert session.get(Funcionario, employee.id) is not None
    assert session.get(Fornecedor, supplier.id) is not None
    assert session.get(Produto, product_one.id) is not None
    assert session.get(Produto, product_two.id) is not None


def test_cancel_sale_rolls_back_when_commit_fails(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    supplier = make_supplier()
    customer = make_customer()
    employee = make_employee()
    product = make_product(supplier)
    session.add_all([supplier, customer, employee, product])
    session.flush()
    assert product.fornecedor_id is not None
    sale = Venda(
        cliente=customer,
        funcionario=employee,
        data_venda=datetime.now(timezone.utc),
        itens=[
            VendaItem(
                produto=product,
                quantidade=Decimal("1.000"),
                preco_unitario=Decimal("15.50"),
                fornecedor_id=product.fornecedor_id,
            )
        ],
    )
    session.add(sale)
    session.commit()
    sale_id = sale.id

    def fail_commit() -> None:
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(session, "commit", fail_commit)

    with pytest.raises(RuntimeError, match="falha simulada"):
        cancel_sale(session, sale_id, VendaCancel(motivo="Falha simulada"))

    sale_after_failure = session.get(Venda, sale_id)
    assert sale_after_failure is not None
    assert sale_after_failure.status == "CONCLUIDA"
    assert len(session.scalars(
        select(VendaItem).where(VendaItem.venda_id == sale_id)
    ).all()) == 1
