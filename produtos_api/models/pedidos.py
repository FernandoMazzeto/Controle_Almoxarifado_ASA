from sqlalchemy import String, Integer, Column, TIMESTAMP, text, ForeignKey
from .database import Base


class Pedido(Base):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto = Column(String(50), nullable=False)
    quantidade = Column(Integer, nullable=False)
    status = Column(String(100), nullable=True)
    