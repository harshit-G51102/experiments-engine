from typing import Sequence

from sqlalchemy import Boolean, ForeignKey, Integer, Float, String, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from ..models import Base
from .schemas import ContextualBandit


class ContextualBanditDB(Base):
    """
    ORM for managing contextual experiments.
    """

    __tablename__ = "contextual_mabs"

    experiment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    arms: Mapped[list["ContextualArmDB"]] = relationship(
        "ContextualArmDB",
        back_populates="experiment",
        lazy="joined",
        cascade="all, delete-orphan",
    )
    contexts: Mapped[list["ContextDB"]] = relationship(
        "ContextDB",
        back_populates="experiment",
        lazy="joined",
        cascade="all, delete-orphan",
    )


class ContextualArmDB(Base):
    """
    ORM for managing contextual arms of an experiment
    """

    __tablename__ = "contextual_arms"

    arm_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contextual_mabs.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)

    alpha_prior: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    beta_prior: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    successes: Mapped[list] = mapped_column(ARRAY(Integer), nullable=False)
    failures: Mapped[list] = mapped_column(ARRAY(Integer), nullable=False)

    experiment: Mapped[ContextualBanditDB] = relationship(
        "ContextualBanditDB", back_populates="arms", lazy="joined"
    )


class ContextDB(Base):
    """
    ORM for managing context for an experiment
    """

    __tablename__ = "contexts"

    context_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contextual_mabs.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)
    values: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    experiment: Mapped[ContextualBanditDB] = relationship(
        "ContextualBanditDB", back_populates="contexts", lazy="joined"
    )


async def save_contextual_mab_to_db(
    experiment: ContextualBandit,
    user_id: int,
    asession: AsyncSession,
) -> ContextualBanditDB:
    """
    Save the experiment to the database.
    """
    contexts = [
        ContextDB(**context.model_dump(), user_id=user_id)
        for context in experiment.contexts
    ]
    arms = [
        ContextualArmDB(**arm.model_dump(), user_id=user_id) for arm in experiment.arms
    ]

    experiment_db = ContextualBanditDB(
        name=experiment.name,
        description=experiment.description,
        user_id=user_id,
        is_active=experiment.is_active,
        arms=arms,
        contexts=contexts,
    )

    asession.add(experiment_db)
    await asession.commit()
    await asession.refresh(experiment_db)

    return experiment_db


async def get_all_contextual_mabs(
    user_id: int,
    asession: AsyncSession,
) -> Sequence[ContextualBanditDB]:
    """
    Get all the contextual experiments from the database.
    """
    statement = (
        select(ContextualBanditDB)
        .where(
            ContextualBanditDB.user_id == user_id,
        )
        .order_by(ContextualBanditDB.experiment_id)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_contextual_mab_by_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> ContextualBanditDB | None:
    """
    Get the contextual experiment by id.
    """
    result = await asession.execute(
        select(ContextualBanditDB)
        .where(ContextualBanditDB.user_id == user_id)
        .where(ContextualBanditDB.experiment_id == experiment_id)
    )

    return result.unique().scalar_one_or_none()


async def delete_contextual_mab_by_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> None:
    """
    Delete the contextual experiment by id.
    """
    await asession.execute(
        delete(ContextDB)
        .where(ContextDB.user_id == user_id)
        .where(ContextDB.experiment_id == experiment_id)
    )
    await asession.execute(
        delete(ContextualArmDB)
        .where(ContextualArmDB.user_id == user_id)
        .where(ContextualArmDB.experiment_id == experiment_id)
    )
    await asession.execute(
        delete(ContextualBanditDB)
        .where(ContextualBanditDB.user_id == user_id)
        .where(ContextualBanditDB.experiment_id == experiment_id)
    )
    await asession.commit()
    return None
