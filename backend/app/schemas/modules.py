from app.schemas.base import APIModel, ReadModel


class ModuleRead(ReadModel):
    id: int
    codigo: str
    nome: str
    ativo: bool
    ordem: int


class ModuleStatusUpdate(APIModel):
    ativo: bool
