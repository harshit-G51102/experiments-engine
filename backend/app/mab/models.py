from typing import Sequence

from sqlalchemy import Boolean, ForeignKey, Integer, String, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base, NotificationsDB
from .schemas import MultiArmedBandit


class MultiArmedBanditDB(Base):
    """
    ORM for managing experiments.
    """

    __tablename__ = "mabs"

    experiment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    arms: Mapped[list["ArmDB"]] = relationship(
        "ArmDB", back_populates="experiment", lazy="joined"
    )

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "arms": [arm.to_dict() for arm in self.arms],
        }


class ArmDB(Base):
    """
    ORM for managing arms of an experiment
    """

    __tablename__ = "arms"

    arm_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mabs.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)

    alpha_prior: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    beta_prior: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    successes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    experiment: Mapped[MultiArmedBanditDB] = relationship(
        "MultiArmedBanditDB", back_populates="arms", lazy="joined"
    )

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "arm_id": self.arm_id,
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "alpha_prior": self.alpha_prior,
            "beta_prior": self.beta_prior,
            "successes": self.successes,
            "failures": self.failures,
        }


async def save_mab_to_db(
    experiment: MultiArmedBandit,
    user_id: int,
    asession: AsyncSession,
) -> MultiArmedBanditDB:
    """
    Save the experiment to the database.
    """
    arms = [
        ArmDB(**arm.model_dump(), user_id=user_id, successes=0, failures=0)
        for arm in experiment.arms
    ]
    experiment_db = MultiArmedBanditDB(
        name=experiment.name,
        description=experiment.description,
        user_id=user_id,
        is_active=experiment.is_active,
        arms=arms,
    )

    asession.add(experiment_db)
    await asession.commit()
    await asession.refresh(experiment_db)

    return experiment_db


async def get_all_mabs(
    user_id: int,
    asession: AsyncSession,
) -> Sequence[MultiArmedBanditDB]:
    """
    Get all the experiments from the database.
    """
    statement = (
        select(MultiArmedBanditDB)
        .where(
            MultiArmedBanditDB.user_id == user_id,
        )
        .order_by(MultiArmedBanditDB.experiment_id)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_mab_by_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> MultiArmedBanditDB | None:
    """
    Get the experiment by id.
    """
    # return await asession.get(MultiArmedBanditDB, experiment_id)
    result = await asession.execute(
        select(MultiArmedBanditDB)
        .where(MultiArmedBanditDB.user_id == user_id)
        .where(MultiArmedBanditDB.experiment_id == experiment_id)
    )

    return result.unique().scalar_one_or_none()


async def delete_mab_by_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> None:
    """
    Delete the experiment by id.
    """

    await asession.execute(
        delete(NotificationsDB)
        .where(NotificationsDB.user_id == user_id)
        .where(NotificationsDB.experiment_id == experiment_id)
    )

    await asession.execute(
        delete(ArmDB)
        .where(ArmDB.user_id == user_id)
        .where(ArmDB.experiment_id == experiment_id)
    )
    await asession.execute(
        delete(MultiArmedBanditDB)
        .where(MultiArmedBanditDB.user_id == user_id)
        .where(MultiArmedBanditDB.experiment_id == experiment_id)
    )
    await asession.commit()
    return None
