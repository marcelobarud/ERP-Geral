from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app.api.appearance as appearance_api
from app.db.session import get_db_session
from app.main import app


def configure_logo_storage(tmp_path: Path, monkeypatch) -> Path:
    storage_root = tmp_path / "storage"
    logo_storage = storage_root / "branding"
    logo_storage.mkdir(parents=True)
    monkeypatch.setattr(appearance_api, "LOGO_STORAGE_DIR", logo_storage)
    upload_mount = next(
        route for route in app.routes if getattr(route, "path", None) == "/uploads"
    )
    monkeypatch.setattr(upload_mount.app, "directory", str(storage_root))
    monkeypatch.setattr(upload_mount.app, "all_directories", [str(storage_root)])
    return logo_storage


def upload_logo(
    client: TestClient,
    body: bytes,
    content_type: str,
    filename: str = "logo",
):
    return client.put(
        "/api/settings/appearance/logo",
        files={"file": (filename, body, content_type)},
    )


@pytest.fixture
def client(session):
    def override_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_appearance_can_be_read_updated_and_restored(client: TestClient) -> None:
    default_response = client.get("/api/settings/appearance")
    assert default_response.status_code == 200
    assert default_response.json()["nome_sistema"] == "ERP Geral"

    update_response = client.patch(
        "/api/settings/appearance",
        json={
            "nome_sistema": "CRM Exemplo",
            "cor_primaria": "#123456",
            "cor_texto_mudo": "#334455",
            "raio_card": "2rem",
            "rotulo_clientes": "Contas",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["nome_sistema"] == "CRM Exemplo"
    assert update_response.json()["rotulo_clientes"] == "Contas"
    assert update_response.json()["cor_texto_mudo"] == "#334455"

    restored_response = client.post("/api/settings/appearance/reset")
    assert restored_response.status_code == 200
    assert restored_response.json()["nome_sistema"] == "ERP Geral"
    assert restored_response.json()["cor_primaria"] == "#487A98"

    read_after_restore = client.get("/api/settings/appearance")
    assert read_after_restore.status_code == 200
    assert read_after_restore.json()["nome_sistema"] == "ERP Geral"
    assert read_after_restore.json()["rotulo_clientes"] == "Clientes"


def test_appearance_logo_openapi_describes_multipart_upload(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()["paths"][
        "/api/settings/appearance/logo"
    ]["put"]
    assert "multipart/form-data" in schema["requestBody"]["content"]


def test_page_appearance_inherits_overrides_and_can_be_reset(
    client: TestClient,
) -> None:
    inherited = client.get("/api/settings/appearance/pages/customers")
    assert inherited.status_code == 200
    assert inherited.json()["overrides"]["cor_fundo"] is None
    assert "cor_fundo" in inherited.json()["inherited"]
    assert inherited.json()["resolved"]["cor_fundo"] == "#EEF4F8"

    updated = client.patch(
        "/api/settings/appearance/pages/customers",
        json={"cor_fundo": "#EEF2FF", "cor_texto_primario": "#111827"},
    )
    assert updated.status_code == 200
    assert updated.json()["resolved"]["cor_fundo"] == "#EEF2FF"
    assert updated.json()["resolved"]["cor_texto_primario"] == "#111827"

    products = client.get("/api/settings/appearance/pages/products")
    assert products.json()["resolved"]["cor_fundo"] == "#EEF4F8"

    global_update = client.patch(
        "/api/settings/appearance",
        json={"cor_fundo": "#FFF7ED"},
    )
    assert global_update.status_code == 200
    products_after_global_update = client.get(
        "/api/settings/appearance/pages/products"
    )
    assert products_after_global_update.json()["resolved"]["cor_fundo"] == "#FFF7ED"
    customers_with_override = client.get(
        "/api/settings/appearance/pages/customers"
    )
    assert customers_with_override.json()["resolved"]["cor_fundo"] == "#EEF2FF"

    reset = client.post("/api/settings/appearance/pages/customers/reset")
    assert reset.status_code == 200
    assert reset.json()["overrides"]["cor_fundo"] is None
    assert reset.json()["resolved"]["cor_fundo"] == "#FFF7ED"


def test_page_appearance_rejects_unknown_page_and_invalid_color(
    client: TestClient,
) -> None:
    unknown_page = client.get("/api/settings/appearance/pages/orders")
    assert unknown_page.status_code == 422

    invalid_color = client.patch(
        "/api/settings/appearance/pages/customers",
        json={"cor_fundo": "var(--danger)"},
    )
    assert invalid_color.status_code == 422


def test_visual_override_crud_inherits_and_rejects_unsafe_properties(
    client: TestClient,
) -> None:
    initial = client.get("/api/settings/appearance/overrides")
    assert initial.status_code == 200
    assert initial.json()["items"] == []

    created = client.put(
        "/api/settings/appearance/overrides/customers.title",
        json={
            "customization_type": "TEXT",
            "customization_group": "page-title",
            "pagina": "customers",
            "properties": {"cor": "#B42318", "peso": 700, "tamanho": 24},
        },
    )
    assert created.status_code == 200
    assert created.json()["customization_key"] == "customers.title"
    assert created.json()["properties"]["cor"] == "#B42318"

    updated = client.put(
        "/api/settings/appearance/overrides/customers.title",
        json={
            "customization_type": "TEXT",
            "pagina": "customers",
            "properties": {"cor": "#2563EB"},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["properties"] == {"cor": "#2563EB"}

    invalid_property = client.put(
        "/api/settings/appearance/overrides/customers.title",
        json={
            "customization_type": "TEXT",
            "pagina": "customers",
            "properties": {"position": "absolute"},
        },
    )
    assert invalid_property.status_code == 422

    invalid_color = client.put(
        "/api/settings/appearance/overrides/customers.title",
        json={
            "customization_type": "TEXT",
            "pagina": "customers",
            "properties": {"cor": "var(--danger)"},
        },
    )
    assert invalid_color.status_code == 422

    deleted = client.delete(
        "/api/settings/appearance/overrides/customers.title"
    )
    assert deleted.status_code == 204
    assert client.get("/api/settings/appearance/overrides").json()["items"] == []


def test_appearance_rejects_unsafe_values_and_unknown_fields(
    client: TestClient,
) -> None:
    invalid_color = client.patch(
        "/api/settings/appearance",
        json={"cor_primaria": "red"},
    )
    assert invalid_color.status_code == 422

    invalid_radius = client.patch(
        "/api/settings/appearance",
        json={"raio_card": "calc(100vw)"},
    )
    assert invalid_radius.status_code == 422

    unknown_field = client.patch(
        "/api/settings/appearance",
        json={"css_livre": "body { display: none; }"},
    )
    assert unknown_field.status_code == 422


def test_appearance_logo_accepts_supported_image_and_rejects_invalid_content(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    logo_storage = configure_logo_storage(tmp_path, monkeypatch)

    image = Image.new("RGBA", (200, 80), (72, 122, 152, 180))
    image_body = BytesIO()
    image.save(image_body, format="PNG")
    valid_logo = upload_logo(client, image_body.getvalue(), "image/png")
    assert valid_logo.status_code == 200
    logo_url = valid_logo.json()["logo_url"]
    assert logo_url.startswith("/uploads/branding/")
    stored_logo = logo_storage / Path(logo_url).name
    assert stored_logo.exists()
    with Image.open(stored_logo) as stored_image:
        assert stored_image.size == (200, 80)
        assert stored_image.mode == "RGBA"
    public_logo = client.get(logo_url)
    assert public_logo.status_code == 200
    assert public_logo.headers["content-type"].startswith("image/png")
    assert public_logo.content == stored_logo.read_bytes()

    generic_content_type = upload_logo(
        client,
        image_body.getvalue(),
        "application/octet-stream",
        filename="logo.png",
    )
    assert generic_content_type.status_code == 200

    invalid_logo = upload_logo(client, b"<svg></svg>", "image/svg+xml")
    assert invalid_logo.status_code == 415


def test_appearance_logo_normalizes_dimensions_without_upscale(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    logo_storage = configure_logo_storage(tmp_path, monkeypatch)

    cases = [
        ("PNG", (3000, 3000), (1024, 1024), "image/png"),
        ("PNG", (2000, 300), (1024, 154), "image/png"),
        ("JPEG", (500, 2000), (256, 1024), "image/jpeg"),
        ("PNG", (200, 80), (200, 80), "image/png"),
    ]
    for image_format, size, expected_size, content_type in cases:
        mode = "RGB" if image_format == "JPEG" else "RGBA"
        color = (72, 122, 152, 180) if mode == "RGBA" else (72, 122, 152)
        image = Image.new(mode, size, color)
        image_body = BytesIO()
        image.save(image_body, format=image_format)
        response = upload_logo(client, image_body.getvalue(), content_type)
        assert response.status_code == 200
        logo_path = logo_storage / Path(response.json()["logo_url"]).name
        with Image.open(logo_path) as stored_image:
            assert stored_image.size == expected_size


def test_appearance_logo_normalizes_jpeg_orientation_and_preserves_previous_on_error(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    logo_storage = configure_logo_storage(tmp_path, monkeypatch)

    image = Image.new("RGB", (2, 3), (72, 122, 152))
    exif = Image.Exif()
    exif[274] = 6
    image_body = BytesIO()
    image.save(image_body, format="JPEG", exif=exif)
    uploaded = upload_logo(client, image_body.getvalue(), "image/jpeg")
    assert uploaded.status_code == 200
    logo_url = uploaded.json()["logo_url"]
    with Image.open(logo_storage / Path(logo_url).name) as stored_image:
        assert stored_image.size == (3, 2)

    corrupt = upload_logo(client, b"\xff\xd8\xffcorrupt", "image/jpeg")
    assert corrupt.status_code == 415
    assert client.get("/api/settings/appearance").json()["logo_url"] == logo_url

    too_large = upload_logo(
        client,
        b"\x89PNG\r\n\x1a\n" + b"x" * appearance_api.MAX_LOGO_BYTES,
        "image/png",
    )
    assert too_large.status_code == 413
    assert client.get("/api/settings/appearance").json()["logo_url"] == logo_url

    restored = client.post("/api/settings/appearance/reset")
    assert restored.status_code == 200
    assert restored.json()["logo_url"] is None
    assert not (logo_storage / Path(logo_url).name).exists()
