from typing import Generic, TypeVar

from pydantic import Field

from app.schemas.base import APIModel

ItemT = TypeVar("ItemT")


class PaginationResponse(APIModel, Generic[ItemT]):
    items: list[ItemT]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)
