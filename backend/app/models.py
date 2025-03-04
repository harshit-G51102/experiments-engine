from typing import Sequence

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .schemas import EventType, Notifications


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


class NotificationsDB(Base):
    """
    Model for notifications.
    Note: if you are updating this, you should also update models in
    the background celery job
    """

    __tablename__ = "notifications"

    notification_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mabs.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    notification_type: Mapped[EventType] = mapped_column(
        Enum(EventType), nullable=False
    )
    notification_value: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        """
        Convert the model to a dictionary
        """
        return {
            "notification_id": self.notification_id,
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "notification_value": self.notification_value,
            "is_active": self.is_active,
        }


async def save_notifications_to_db(
    experiment_id: int,
    user_id: int,
    notifications: Notifications,
    asession: AsyncSession,
) -> list[NotificationsDB]:
    """
    Save notifications to the database
    """
    notification_records = []
    if notifications.onTrialCompletion:
        notification_row = NotificationsDB(
            experiment_id=experiment_id,
            user_id=user_id,
            notification_type=EventType.TRIALS_COMPLETED,
            notification_value=notifications.onTrialCompletion,
            is_active=True,
        )
        notification_records.append(notification_row)
    if notifications.onDaysElapsed:
        notification_row = NotificationsDB(
            experiment_id=experiment_id,
            user_id=user_id,
            notification_type=EventType.TRIALS_COMPLETED,
            notification_value=notifications.daysElapsed,
            is_active=True,
        )
        notification_records.append(notification_row)
    if notifications.onPercentBetter:
        notification_row = NotificationsDB(
            experiment_id=experiment_id,
            user_id=user_id,
            notification_type=EventType.PERCENTAGE_BETTER,
            notification_value=notifications.percentBetterThreshold,
            is_active=True,
        )
        notification_records.append(notification_row)

    asession.add_all(notification_records)
    await asession.commit()

    return notification_records


async def get_notifications_from_db(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> Sequence[NotificationsDB]:
    """
    Get notifications from the database
    """
    statement = (
        select(NotificationsDB)
        .where(NotificationsDB.experiment_id == experiment_id)
        .where(NotificationsDB.user_id == user_id)
    )

    return (await asession.execute(statement)).scalars().all()
