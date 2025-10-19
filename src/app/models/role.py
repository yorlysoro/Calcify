from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.db.session import Base
from src.app.models.user import user_roles


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    users = relationship("User", secondary=user_roles, back_populates="roles")