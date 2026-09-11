import uuid
import warnings
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.appearance import (
    AppearanceSettings,
    ElementAppearanceOverride,
    PageAppearanceSettings,
)
from app.schemas.appearance import (
    AppearanceOverridePayload,
    AppearanceOverrideRead,
    AppearanceOverridesRead,
    AppearancePatch,
    AppearanceRead,
    PageAppearancePatch,
    PageAppearanceRead,
    PageId,
    ResolvedPageAppearance,
)

router = APIRouter(prefix="/api/settings/appearance", tags=["appearance"])
LOGO_STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "branding"
MAX_LOGO_BYTES = 2 * 1024 * 1024
MAX_LOGO_DIMENSION = 1024
MAX_LOGO_PIXELS = 25_000_000

DEFAULTS = {
    "id": 1,
    "nome_sistema": "ERP Geral",
    "logo_url": None,
    "cor_primaria": "#487A98",
    "cor_secundaria": "#2F5975",
    "cor_destaque": "#2F8065",
    "cor_fundo": "#EEF4F8",
    "cor_superficie": "#FFFFFF",
    "cor_texto": "#1E293B",
    "cor_texto_primario": "#1E293B",
    "cor_texto_secundario": "#4B6575",
    "cor_texto_mudo": "#718096",
    "cor_titulo": "#1E293B",
    "cor_link": "#2F5975",
    "cor_sobre_primaria": "#FFFFFF",
    "cor_sobre_secundaria": "#2F5975",
    "cor_sobre_destaque": "#FFFFFF",
    "cor_tabela_cabecalho": "#2F5975",
    "cor_tabela_corpo": "#1E293B",
    "cor_tabela_fundo": "#FFFFFF",
    "cor_tabela_borda": "#DCE7EE",
    "cor_perigo": "#B95353",
    "cor_sucesso": "#2F8065",
    "cor_aviso": "#9A7441",
    "raio_controle": "0.75rem",
    "raio_card": "1.5rem",
    "rotulo_dashboard": "Dashboard",
    "rotulo_clientes": "Clientes",
    "rotulo_produtos": "Produtos",
    "rotulo_funcionarios": "Funcionários",
    "rotulo_fornecedores": "Fornecedores",
    "rotulo_vendas": "Vendas",
    "rotulo_nova_venda": "Nova venda",
}

PAGE_OVERRIDE_FIELDS = (
    "cor_fundo",
    "cor_superficie",
    "cor_titulo",
    "cor_texto_primario",
    "cor_texto_secundario",
    "cor_texto_mudo",
    "cor_destaque",
    "cor_link",
)


def _page_theme(
    settings: AppearanceSettings,
    override: PageAppearanceSettings | None,
) -> dict[str, str]:
    global_values = {
        "cor_fundo": settings.cor_fundo,
        "cor_superficie": settings.cor_superficie,
        "cor_titulo": settings.cor_titulo,
        "cor_texto_primario": settings.cor_texto_primario,
        "cor_texto_secundario": settings.cor_texto_secundario,
        "cor_texto_mudo": settings.cor_texto_mudo,
        "cor_destaque": settings.cor_destaque,
        "cor_link": settings.cor_link,
    }
    return {
        field: (getattr(override, field) if override else None) or value
        for field, value in global_values.items()
    }


def _page_response(
    page: str,
    settings: AppearanceSettings,
    override: PageAppearanceSettings | None,
) -> PageAppearanceRead:
    resolved = _page_theme(settings, override)
    inherited = [
        field for field in PAGE_OVERRIDE_FIELDS
        if override is None or getattr(override, field) is None
    ]
    overrides = {
        field: getattr(override, field) if override else None
        for field in PAGE_OVERRIDE_FIELDS
    }
    return PageAppearanceRead(
        pagina=page,
        overrides=overrides,
        resolved=ResolvedPageAppearance(**resolved),
        inherited=inherited,
    )


def appearance_or_default(
    db: Session,
    *,
    persist: bool = True,
) -> AppearanceSettings:
    settings = db.get(AppearanceSettings, 1)
    if settings is None:
        settings = AppearanceSettings(**DEFAULTS)
        if persist:
            db.add(settings)
            db.flush()
    return settings


def remove_logo_file(logo_url: str | None) -> None:
    if not logo_url or not logo_url.startswith("/uploads/branding/"):
        return
    filename = Path(logo_url).name
    if filename:
        (LOGO_STORAGE_DIR / filename).unlink(missing_ok=True)


def normalize_logo(body: bytes, content_type: str) -> tuple[bytes, str]:
    expected_format = {
        "image/png": "PNG",
        "image/jpeg": "JPEG",
        "image/webp": "WEBP",
    }[content_type]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(body)) as image:
                if image.format != expected_format:
                    raise ValueError("O conteúdo não corresponde ao tipo informado")
                if image.width * image.height > MAX_LOGO_PIXELS:
                    raise ValueError("A imagem excede o limite seguro de pixels")
                image.verify()

            with Image.open(BytesIO(body)) as image:
                image.load()
                normalized = ImageOps.exif_transpose(image)
                normalized.thumbnail(
                    (MAX_LOGO_DIMENSION, MAX_LOGO_DIMENSION),
                    Image.Resampling.LANCZOS,
                )
                if expected_format == "JPEG" and normalized.mode not in {"L", "RGB"}:
                    normalized = normalized.convert("RGB")
                output = BytesIO()
                save_options = {"format": expected_format}
                if expected_format == "PNG":
                    save_options["optimize"] = True
                elif expected_format == "JPEG":
                    save_options.update({"quality": 95, "optimize": True})
                else:
                    save_options.update({"quality": 95, "method": 6})
                normalized.save(output, **save_options)
                normalized_bytes = output.getvalue()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(
            status_code=413,
            detail="A imagem excede o limite seguro de dimensões.",
        ) from None
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=415,
            detail="O conteúdo enviado não é uma imagem PNG, JPEG ou WEBP válida.",
        ) from None

    if len(normalized_bytes) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=413, detail="A logo deve ter no máximo 2 MB.")
    return normalized_bytes, expected_format.lower().replace("jpeg", "jpg")


def detect_logo_content_type(body: bytes) -> str | None:
    try:
        with Image.open(BytesIO(body)) as image:
            return {
                "PNG": "image/png",
                "JPEG": "image/jpeg",
                "WEBP": "image/webp",
            }.get(image.format)
    except (Image.DecompressionBombError, OSError, UnidentifiedImageError):
        return None


@router.get("", response_model=AppearanceRead)
def get_appearance(db: Session = Depends(get_db_session)) -> AppearanceSettings:
    return appearance_or_default(db, persist=False)


@router.patch("", response_model=AppearanceRead)
def update_appearance(
    payload: AppearancePatch,
    db: Session = Depends(get_db_session),
) -> AppearanceSettings:
    settings = appearance_or_default(db, persist=True)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field_name, value)
    try:
        db.commit()
        db.refresh(settings)
    except Exception:
        db.rollback()
        raise
    return settings


@router.post("/reset", response_model=AppearanceRead)
def reset_appearance(db: Session = Depends(get_db_session)) -> AppearanceSettings:
    settings = appearance_or_default(db, persist=True)
    previous_logo = settings.logo_url
    for field_name, value in DEFAULTS.items():
        if field_name != "id":
            setattr(settings, field_name, value)
    try:
        db.commit()
        db.refresh(settings)
    except Exception:
        db.rollback()
        raise
    remove_logo_file(previous_logo)
    return settings


@router.get("/pages/{page}", response_model=PageAppearanceRead)
def get_page_appearance(
    page: PageId,
    db: Session = Depends(get_db_session),
) -> PageAppearanceRead:
    settings = appearance_or_default(db, persist=False)
    override = (
        db.query(PageAppearanceSettings)
        .filter(PageAppearanceSettings.pagina == page)
        .one_or_none()
    )
    return _page_response(page, settings, override)


@router.patch("/pages/{page}", response_model=PageAppearanceRead)
def update_page_appearance(
    page: PageId,
    payload: PageAppearancePatch,
    db: Session = Depends(get_db_session),
) -> PageAppearanceRead:
    settings = appearance_or_default(db, persist=True)
    override = (
        db.query(PageAppearanceSettings)
        .filter(PageAppearanceSettings.pagina == page)
        .one_or_none()
    )
    if override is None:
        override = PageAppearanceSettings(pagina=page)
        db.add(override)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(override, field_name, value)
    try:
        db.commit()
        db.refresh(override)
    except Exception:
        db.rollback()
        raise
    return _page_response(page, settings, override)


@router.post("/pages/{page}/reset", response_model=PageAppearanceRead)
def reset_page_appearance(
    page: PageId,
    db: Session = Depends(get_db_session),
) -> PageAppearanceRead:
    settings = appearance_or_default(db, persist=False)
    override = (
        db.query(PageAppearanceSettings)
        .filter(PageAppearanceSettings.pagina == page)
        .one_or_none()
    )
    if override is not None:
        db.delete(override)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return _page_response(page, settings, None)


@router.get("/overrides", response_model=AppearanceOverridesRead)
def get_appearance_overrides(
    db: Session = Depends(get_db_session),
) -> AppearanceOverridesRead:
    overrides = (
        db.query(ElementAppearanceOverride)
        .order_by(ElementAppearanceOverride.customization_key)
        .all()
    )
    return AppearanceOverridesRead(
        items=[
            AppearanceOverrideRead.model_validate(override)
            for override in overrides
        ]
    )


@router.put(
    "/overrides/{customization_key}",
    response_model=AppearanceOverrideRead,
)
def upsert_appearance_override(
    customization_key: str,
    payload: AppearanceOverridePayload,
    db: Session = Depends(get_db_session),
) -> ElementAppearanceOverride:
    try:
        AppearanceOverridePayload.validate_key(customization_key)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    override = (
        db.query(ElementAppearanceOverride)
        .filter(
            ElementAppearanceOverride.customization_key == customization_key
        )
        .one_or_none()
    )
    if override is None:
        override = ElementAppearanceOverride(customization_key=customization_key)
        db.add(override)

    override.customization_type = payload.customization_type
    override.customization_group = payload.customization_group
    override.pagina = payload.pagina
    override.properties = payload.properties
    try:
        db.commit()
        db.refresh(override)
    except Exception:
        db.rollback()
        raise
    return override


@router.delete("/overrides/{customization_key}", status_code=204)
def reset_appearance_override(
    customization_key: str,
    db: Session = Depends(get_db_session),
) -> None:
    try:
        AppearanceOverridePayload.validate_key(customization_key)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    override = (
        db.query(ElementAppearanceOverride)
        .filter(
            ElementAppearanceOverride.customization_key == customization_key
        )
        .one_or_none()
    )
    if override is None:
        return
    db.delete(override)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


@router.put("/logo", response_model=AppearanceRead)
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
) -> AppearanceSettings:
    content_type = (file.content_type or "").split(";", 1)[0].lower()
    if content_type == "application/octet-stream":
        content_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
    }.get(Path(file.filename or "").suffix.lower(), content_type)
    body = await file.read()
    if len(body) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=413, detail="A logo deve ter no máximo 2 MB.")
    if content_type not in {"image/png", "image/jpeg", "image/webp"}:
        content_type = detect_logo_content_type(body) or content_type
    if content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(
            status_code=415,
            detail="Envie uma imagem PNG, JPEG ou WEBP.",
        )
    normalized_body, extension = normalize_logo(body, content_type)

    LOGO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{extension}"
    destination = LOGO_STORAGE_DIR / filename
    destination.write_bytes(normalized_body)
    settings = appearance_or_default(db, persist=True)
    previous_logo = settings.logo_url
    settings.logo_url = f"/uploads/branding/{filename}"
    try:
        db.commit()
        db.refresh(settings)
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise
    remove_logo_file(previous_logo)
    return settings
