from datetime import datetime

from sqlalchemy import Integer, Float, TIMESTAMP, text, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class BaseTable(DeclarativeBase):
    # так как уже DeclarativeBase строчка излишняя
    # __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    
class UsersTable(BaseTable):
    __tablename__ = "Users"

    # телеграм id
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    # имя
    name: Mapped[str] = mapped_column(Text)
    # возраст
    age: Mapped[int] = mapped_column(Integer)
    # город
    city: Mapped[str] = mapped_column(Text)
    # пол
    sex: Mapped[bool] = mapped_column(Boolean)
    # текст анкеты
    text: Mapped[str] = mapped_column(Text)
    # прошла модерацию
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending", server_default=text("'pending'"))
    # версия анкеты (для сброса лайков/дизлайков при изменениях)
    profile_version: Mapped[int] = mapped_column(Integer, default=1)
    # когда закончиться подписка
    expire_subscription_date: Mapped[datetime] = mapped_column(TIMESTAMP, default=None)
    # анкета включена/выключена
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # анонимно?
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    
    
class AdminTable(BaseTable):
    __tablename__ = "Admins"

    # телеграм id
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    # уровень привелегий
    level: Mapped[int] = mapped_column(Integer, default=0)
    
class MediaTable(BaseTable):
    __tablename__ = "Media"

    # путь к медиа
    path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    # id пользователя
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"), nullable=False)
    # версия анкеты (для сброса лайков/дизлайков при изменениях)
    profile_version: Mapped[int] = mapped_column(Integer, default=1)


class CityTable(BaseTable):
    __tablename__ = "Cities"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    norm: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)


class ComplaintTable(BaseTable):
    __tablename__ = "Complaints"

    # id пользователя
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"), nullable=False)
    # id пользователя, кого жалуют
    target_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"), nullable=True)
    # id сообщения пользователя
    user_message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 0 - жалоба на сервис, 1 - жалоба на анкету
    complaint_type: Mapped[int] = mapped_column(Integer, default=0)
    # id администратора
    admin_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # id пересланного сообщения администратору
    admin_message_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 0 - новое, 1 - в работе, 2 - отвечено
    status: Mapped[int] = mapped_column(Integer, default=0)


class SwipeTable(BaseTable):
    __tablename__ = "Swipes"

    # кто смотрел
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"), nullable=False)
    # чью анкету смотрел
    target_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"), nullable=False)
    # версия анкеты на момент просмотра
    target_version: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1 - лайк, 0 - дизлайк
    action: Mapped[int] = mapped_column(Integer, nullable=False)

class PaymentTable(BaseTable):
    __tablename__ = "Payments"

    invoice_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"), nullable=False)
    payment_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=True, default="")
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0 pending, 1 paid
    is_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
