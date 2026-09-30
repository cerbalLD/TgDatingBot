# store/store.py
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

from store.models import BaseTable
from store.repositories import (
    UsersRepository,
    AdminRepository,
    MediaRepository,
    ComplaintsRepository,
    SwipesRepository,
    CityRepository,
    PaymentsRepository,
)
from config import DB_PATH


def _fk_pragma_on_connect(dbapi_con, con_record):
    cur = dbapi_con.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.close()


class Store:
    def __init__(self) -> None:
        self.db_url = f"sqlite:///{DB_PATH}"

        self.engine = create_engine(
            self.db_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        event.listen(self.engine, "connect", _fk_pragma_on_connect)

        # репозитории
        self.user = UsersRepository(self.engine)
        self.admin = AdminRepository(self.engine)
        self.media = MediaRepository(self.engine)
        self.complaint = ComplaintsRepository(self.engine)
        self.swipe = SwipesRepository(self.engine)
        self.city = CityRepository(self.engine)
        self.payment = PaymentsRepository(self.engine)

    def init_db(self) -> None:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        BaseTable.metadata.create_all(self.engine)
        self._ensure_moderation_status_column()

    def _ensure_moderation_status_column(self) -> None:
        with self.engine.begin() as conn:
            columns = conn.execute(text("PRAGMA table_info('Users')")).mappings().all()
            if not any(column["name"] == "moderation_status" for column in columns):
                conn.execute(
                    text("ALTER TABLE \"Users\" ADD COLUMN moderation_status TEXT NOT NULL DEFAULT 'pending'")
                )
            conn.execute(
                text(
                    """
                    UPDATE "Users"
                    SET moderation_status = CASE
                        WHEN is_approved = 1 THEN 'approved'
                        ELSE moderation_status
                    END
                    WHERE moderation_status IS NULL
                       OR moderation_status = ''
                       OR moderation_status = 'pending'
                    """
                )
            )

    def drop_all(self) -> None:
        BaseTable.metadata.drop_all(self.engine)

    @contextmanager
    def session_scope(self):
        with Session(self.engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
