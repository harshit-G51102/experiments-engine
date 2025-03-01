from datetime import datetime, timezone
from typing import Sequence

import numpy as np
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    delete,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base
from .schemas import CMABObservationBinary, CMABObservationRealVal, ContextualBandit


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
    prior_type: Mapped[str] = mapped_column(String(length=50), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(length=50), nullable=False)
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
    observations: Mapped[list["ContextualObservationDB"]] = relationship(
        "ContextualObservationDB", back_populates="experiment", lazy="joined"
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

    # prior variables
    mu_init: Mapped[float] = mapped_column(Float, nullable=False)
    sigma_init: Mapped[float] = mapped_column(Float, nullable=False)
    mu: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    covariance: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)

    experiment: Mapped[ContextualBanditDB] = relationship(
        "ContextualBanditDB", back_populates="arms", lazy="joined"
    )
    observations: Mapped[list["ContextualObservationDB"]] = relationship(
        "ContextualObservationDB", back_populates="arm", lazy="joined"
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
    value_type: Mapped[str] = mapped_column(String(length=50), nullable=False)

    experiment: Mapped[ContextualBanditDB] = relationship(
        "ContextualBanditDB", back_populates="contexts", lazy="joined"
    )


class ContextualObservationDB(Base):
    """
    ORM for managing observations of an experiment
    """

    __tablename__ = "contextual_observations"

    observation_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    arm_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contextual_arms.arm_id"), nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contextual_mabs.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )

    reward: Mapped[float] = mapped_column(Float, nullable=True)
    context_val: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    obs_timestamp_utc: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    experiment: Mapped[ContextualBanditDB] = relationship(
        "ContextualBanditDB", back_populates="observations", lazy="joined"
    )
    arm: Mapped[ContextualArmDB] = relationship(
        "ContextualArmDB", back_populates="observations", lazy="joined"
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
        ContextDB(
            name=context.name,
            description=context.description,
            value_type=context.value_type.value,
            user_id=user_id,
        )
        for context in experiment.contexts
    ]
    arms = []
    for arm in experiment.arms:
        arms.append(
            ContextualArmDB(
                name=arm.name,
                description=arm.description,
                mu_init=arm.mu_init,
                sigma_init=arm.sigma_init,
                mu=(np.ones(len(experiment.contexts)) * arm.mu_init).tolist(),
                covariance=(
                    np.identity(len(experiment.contexts)) * arm.sigma_init
                ).tolist(),
                user_id=user_id,
            )
        )

    experiment_db = ContextualBanditDB(
        name=experiment.name,
        description=experiment.description,
        user_id=user_id,
        is_active=experiment.is_active,
        arms=arms,
        contexts=contexts,
        prior_type=experiment.prior_type.value,
        reward_type=experiment.reward_type.value,
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
        delete(ContextualObservationDB)
        .where(ContextualObservationDB.user_id == user_id)
        .where(ContextualObservationDB.experiment_id == experiment_id)
    )
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


async def save_contextual_obs_to_db(
    observation: CMABObservationRealVal | CMABObservationBinary,
    user_id: int,
    asession: AsyncSession,
) -> ContextualObservationDB:
    """
    Save the observation to the database.
    """
    observation_db = ContextualObservationDB(
        arm_id=observation.arm_id,
        experiment_id=observation.experiment_id,
        user_id=user_id,
        reward=observation.reward,
        context_val=observation.context,
        obs_timestamp_utc=datetime.now(timezone.utc),
    )

    asession.add(observation_db)
    await asession.commit()
    await asession.refresh(observation_db)

    return observation_db


async def get_rewards_by_experiment_arm_id(
    experiment_id: int, arm_id: int, user_id: int, asession: AsyncSession
) -> Sequence[ContextualObservationDB]:
    """
    Get the rewards for an arm of an experiment.
    """
    statement = (
        select(ContextualObservationDB)
        .where(ContextualObservationDB.user_id == user_id)
        .where(ContextualObservationDB.experiment_id == experiment_id)
        .where(ContextualObservationDB.arm_id == arm_id)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_all_rewards_by_experiment_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> Sequence[ContextualObservationDB]:
    """
    Get the rewards for an experiment.
    """
    statement = (
        select(ContextualObservationDB)
        .where(ContextualObservationDB.user_id == user_id)
        .where(ContextualObservationDB.experiment_id == experiment_id)
    )

    return (await asession.execute(statement)).unique().scalars().all()
