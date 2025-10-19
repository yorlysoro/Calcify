from passlib.hash import argon2
from src.db.session import SessionLocal
from src.app.models.user import User
from src.app.models.role import Role


class AuthService:
    def __init__(self):
        self.db = SessionLocal()

    def create_user(self, username: str, password: str):
        h = argon2.hash(password)
        user = User(username=username, password_hash=h)
        self.db.add(user)
        self.db.commit()
        return user

    def verify_password(self, user: User, password: str) -> bool:
        try:
            return argon2.verify(password, user.password_hash)
        except Exception:
            return False

    def authenticate(self, username: str, password: str):
        user = self.db.query(User).filter_by(username=username).first()
        if user and self.verify_password(user, password):
            return user
        return None

    def add_role(self, user: User, role_name: str):
        role = self.db.query(Role).filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name)
            self.db.add(role)
            self.db.commit()
        user.roles.append(role)
        self.db.commit()

    def has_role(self, user: User, role_name: str) -> bool:
        return any(r.name == role_name for r in user.roles)
