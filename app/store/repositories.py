# store/repositories.py
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from store.models import (
    BaseTable,
    UsersTable,
    AdminTable,
    MediaTable,
    ComplaintTable,
    SwipeTable,
    CityTable,
    PaymentTable,
)

ModelT = TypeVar("ModelT", bound=BaseTable)


class Repository(Generic[ModelT]):
    def __init__(self, engine: Engine, model: Type[ModelT]):
        self.engine = engine
        self.model = model

    # --- базовые CRUD ---
    def create(self, **fields) -> int:
        with Session(self.engine) as session:
            obj = self.model(**fields)  # type: ignore[arg-type]
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj.id

    def get(self, id: int) -> Optional[ModelT]:
        with Session(self.engine) as session:
            return session.get(self.model, id)

    def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[Any] = None,
        **filters: Any,
    ) -> List[ModelT]:
        with Session(self.engine) as session:
            query = session.query(self.model)

            for field_name, value in filters.items():
                if value is None:
                    continue
                query = query.filter(getattr(self.model, field_name) == value)

            if order_by is None:
                order_by = self.model.id  # type: ignore[attr-defined]

            query = query.order_by(order_by)
            return query.offset(offset).limit(limit).all()

    def count(self, **filters: Any) -> int:
        with Session(self.engine) as session:
            query = session.query(func.count(self.model.id))

            for field_name, value in filters.items():
                if value is None:
                    continue
                query = query.filter(getattr(self.model, field_name) == value)

            return int(query.scalar() or 0)

    def update(self, id: int, **fields) -> bool:
        with Session(self.engine) as session:
            obj = session.get(self.model, id)
            if not obj:
                return False

            for field_name, value in fields.items():
                if value is not None:
                    setattr(obj, field_name, value)

            session.commit()
            return True

    def delete(self, id: int) -> bool:
        with Session(self.engine) as s:
            obj = s.get(self.model, id)
            if not obj:
                return False
            s.delete(obj)
            s.commit()
            return True


class UsersRepository(Repository[UsersTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, UsersTable)

    def get_by_user_id(self, user_id: int) -> Optional[UsersTable]:
        """Находит пользователя по telegram user_id"""
        with Session(self.engine) as s:
            return s.query(UsersTable).filter(
                UsersTable.user_id == user_id
            ).first()

class AdminRepository(Repository[AdminTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, AdminTable)
        
class MediaRepository(Repository[MediaTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, MediaTable)


class CityRepository(Repository[CityTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, CityTable)

    def get_by_norm(self, norm: str) -> Optional[CityTable]:
        with Session(self.engine) as s:
            return s.query(CityTable).filter(CityTable.norm == norm).first()

    def get_by_name(self, name: str) -> Optional[CityTable]:
        with Session(self.engine) as s:
            return s.query(CityTable).filter(CityTable.name == name).first()

    def upsert(self, norm: str, name: str, lat: float, lon: float) -> int:
        with Session(self.engine) as s:
            existing = s.query(CityTable).filter(CityTable.norm == norm).first()
            if existing:
                existing.name = name
                existing.lat = lat
                existing.lon = lon
                s.commit()
                return existing.id
            obj = CityTable(name=name, norm=norm, lat=lat, lon=lon)
            s.add(obj)
            s.commit()
            s.refresh(obj)
            return obj.id


class ComplaintsRepository(Repository[ComplaintTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, ComplaintTable)

    def get_by_admin_message_id(self, admin_message_id: int) -> Optional[ComplaintTable]:
        with Session(self.engine) as s:
            return s.query(ComplaintTable).filter(
                ComplaintTable.admin_message_id == admin_message_id
            ).first()


class SwipesRepository(Repository[SwipeTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, SwipeTable)

    def list_incoming_likes(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> List[SwipeTable]:
        with Session(self.engine) as s:
            query = (
                s.query(SwipeTable)
                .filter(
                    SwipeTable.target_user_id == user_id,
                    SwipeTable.action == 1,
                )
                .order_by(SwipeTable.created_at.desc())
            )
            return query.offset(offset).limit(limit).all()

    def get_by_user_target_version(
        self, user_id: int, target_user_id: int, target_version: int
    ) -> Optional[SwipeTable]:
        with Session(self.engine) as s:
            return s.query(SwipeTable).filter(
                SwipeTable.user_id == user_id,
                SwipeTable.target_user_id == target_user_id,
                SwipeTable.target_version == target_version,
            ).first()

    def count_by_user_since(self, user_id: int, since: datetime) -> int:
        with Session(self.engine) as s:
            count = (
                s.query(func.count(SwipeTable.id))
                .filter(
                    SwipeTable.user_id == user_id,
                    SwipeTable.created_at >= since,
                )
                .scalar()
            )
            return int(count or 0)

    def count_by_user(self, user_id: int) -> int:
        with Session(self.engine) as s:
            count = (
                s.query(func.count(SwipeTable.id))
                .filter(SwipeTable.user_id == user_id)
                .scalar()
            )
            return int(count or 0)


class PaymentsRepository(Repository[PaymentTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, PaymentTable)

    def get_by_invoice_id(self, invoice_id: int) -> Optional[PaymentTable]:
        with Session(self.engine) as s:
            return s.query(PaymentTable).filter(PaymentTable.invoice_id == invoice_id).first()
