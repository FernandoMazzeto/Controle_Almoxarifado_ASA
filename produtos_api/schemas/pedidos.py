from pydantic import BaseModel

class Pedido(BaseModel):
    id: int
    produto: str
    quantidade: int
    status: str


