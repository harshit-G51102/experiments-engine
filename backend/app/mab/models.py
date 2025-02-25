from typing import Sequence

from sqlalchemy import (
    ARRAY,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    delete,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base
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
    prior_type: Mapped[str] = mapped_column(String(length=50), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(length=50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    arms: Mapped[list["ArmDB"]] = relationship(
        "ArmDB", back_populates="experiment", lazy="joined"
    )


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

    # prior variables
    alpha: Mapped[float] = mapped_column(Float, nullable=True)
    beta: Mapped[float] = mapped_column(Float, nullable=True)
    mu: Mapped[float] = mapped_column(Float, nullable=True)
    sigma: Mapped[float] = mapped_column(Float, nullable=True)

    # reward variables
    successes: Mapped[int] = mapped_column(Integer, nullable=True)
    failures: Mapped[int] = mapped_column(Integer, nullable=True)
    reward: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=True)

    experiment: Mapped[MultiArmedBanditDB] = relationship(
        "MultiArmedBanditDB", back_populates="arms", lazy="joined"
    )


async def save_mab_to_db(
    experiment: MultiArmedBandit,
    user_id: int,
    asession: AsyncSession,
) -> MultiArmedBanditDB:
    """
    Save the experiment to the database.
    """
    arms = [
        ArmDB(
            **arm.model_dump(),
            user_id=user_id,
        )
        for arm in experiment.arms
    ]

    experiment_db = MultiArmedBanditDB(
        name=experiment.name,
        description=experiment.description,
        user_id=user_id,
        is_active=experiment.is_active,
        arms=arms,
        prior_type=experiment.prior_type.value,
        reward_type=experiment.reward_type.value,
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
