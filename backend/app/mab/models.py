from datetime import datetime, timezone
from typing import Sequence

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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base, ExperimentBaseDB, NotificationsDB
from .schemas import MABObservationBinary, MABObservationRealVal, MultiArmedBandit


class MultiArmedBanditDB(ExperimentBaseDB):
    """
    ORM for managing experiments.
    """

    __tablename__ = "mabs"

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments_base.experiment_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
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
    observations: Mapped[list["ObservationDB"]] = relationship(
        "ObservationDB", back_populates="experiment", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "mabs"}

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "created_datetime_utc": self.created_datetime_utc,
            "is_active": self.is_active,
            "n_trials": self.n_trials,
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

    # prior variables
    alpha: Mapped[float] = mapped_column(Float, nullable=True)
    beta: Mapped[float] = mapped_column(Float, nullable=True)
    mu: Mapped[float] = mapped_column(Float, nullable=True)
    sigma: Mapped[float] = mapped_column(Float, nullable=True)

    experiment: Mapped[MultiArmedBanditDB] = relationship(
        "MultiArmedBanditDB", back_populates="arms", lazy="joined"
    )
    observations: Mapped[list["ObservationDB"]] = relationship(
        "ObservationDB", back_populates="arm", lazy="joined"
    )


class ObservationDB(Base):
    """
    ORM for managing observations of an experiment
    """

    __tablename__ = "observations"

    observation_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    arm_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("arms.arm_id"), nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mabs.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )

    reward: Mapped[float] = mapped_column(Float, nullable=False)
    obs_datetime_utc: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    arm: Mapped[ArmDB] = relationship(
        "ArmDB", back_populates="observations", lazy="joined"
    )
    experiment: Mapped[MultiArmedBanditDB] = relationship(
        "MultiArmedBanditDB", back_populates="observations", lazy="joined"
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
        created_datetime_utc=datetime.now(timezone.utc),
        n_trials=0,
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
        delete(NotificationsDB)
        .where(NotificationsDB.user_id == user_id)
        .where(NotificationsDB.experiment_id == experiment_id)
    )

    await asession.execute(
        delete(ObservationDB)
        .where(ObservationDB.user_id == user_id)
        .where(ObservationDB.experiment_id == experiment_id)
    )
    await asession.execute(
        delete(ArmDB)
        .where(ArmDB.user_id == user_id)
        .where(ArmDB.experiment_id == experiment_id)
    )
    await asession.execute(
        delete(ExperimentBaseDB)
        .where(ExperimentBaseDB.user_id == user_id)
        .where(ExperimentBaseDB.experiment_id == experiment_id)
    )
    await asession.commit()
    return None


async def save_observation_to_db(
    observation: MABObservationRealVal | MABObservationBinary,
    user_id: int,
    asession: AsyncSession,
) -> ObservationDB:
    """
    Save the observation to the database.
    """
    observation_db = ObservationDB(
        **observation.model_dump(),
        obs_datetime_utc=datetime.now(timezone.utc),
        user_id=user_id,
    )

    asession.add(observation_db)
    await asession.commit()
    await asession.refresh(observation_db)

    return observation_db


async def get_rewards_by_experiment_arm_id(
    experiment_id: int, arm_id: int, user_id: int, asession: AsyncSession
) -> Sequence[ObservationDB]:
    """
    Get the observations for the experiment and arm.
    """
    statement = (
        select(ObservationDB)
        .where(ObservationDB.user_id == user_id)
        .where(ObservationDB.experiment_id == experiment_id)
        .where(ObservationDB.arm_id == arm_id)
        .order_by(ObservationDB.obs_datetime_utc)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_all_rewards_by_experiment_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> Sequence[ObservationDB]:
    """
    Get the observations for the experiment and arm.
    """
    statement = (
        select(ObservationDB)
        .where(ObservationDB.user_id == user_id)
        .where(ObservationDB.experiment_id == experiment_id)
        .order_by(ObservationDB.obs_datetime_utc)
    )

    return (await asession.execute(statement)).unique().scalars().all()
