from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from ..exp_engine.schemas import (
    ArmPriors,
    Outcome,
    RewardLikelihood,
    allowed_combos_mab,
)


class Arm(BaseModel):
    """
    Pydantic model for a arm of the experiment.
    """

    name: str = Field(
        max_length=150,
        examples=["Arm 1"],
    )
    description: str = Field(
        max_length=500,
        examples=["This is a description of the arm."],
    )

    # prior variables
    alpha: float | None = Field(default=None)
    beta: float | None = Field(default=None)
    mu: float | None = Field(default=None)
    sigma: float | None = Field(default=None)

    @model_validator(mode="after")
    def check_values(self) -> Self:
        """
        Check if the values are unique.
        """
        alpha = self.alpha
        beta = self.beta
        sigma = self.sigma
        if alpha is not None and alpha <= 0:
            raise ValueError("Alpha must be greater than 0.")
        if beta is not None and beta <= 0:
            raise ValueError("Beta must be greater than 0.")
        if sigma is not None and sigma <= 0:
            raise ValueError("Sigma must be greater than 0.")
        return self


class ArmResponse(Arm):
    """
    Pydantic model for an response for arm creation
    """

    arm_id: int

    model_config = ConfigDict(from_attributes=True)


class MultiArmedBanditBase(BaseModel):
    """
    Pydantic model for an experiment - Base model.
    Note: Do not use this model directly. Use `MultiArmedBandit` instead.
    """

    name: str = Field(
        max_length=150,
        examples=["Experiment 1"],
    )

    description: str = Field(
        max_length=500,
        examples=["This is a description of the experiment."],
    )

    reward_type: RewardLikelihood = Field(
        description="The type of reward we observe from the experiment.",
        default=RewardLikelihood.BERNOULLI,
    )
    prior_type: ArmPriors = Field(
        description="The type of prior distribution for the arms.",
        default=ArmPriors.BETA,
    )

    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class MultiArmedBandit(MultiArmedBanditBase):
    """
    Pydantic model for an experiment.
    """

    arms: list[Arm]

    @model_validator(mode="before")
    def check_arm_and_experiment_reward_type(cls, values: dict) -> dict:
        """
        Check if the arm reward type is same as the experiment reward type.
        """
        reward_type = values.get("reward_type")
        prior_type = values.get("prior_type")
        arms = values.get("arms")

        if arms is None:
            raise ValueError("At least one arm is required.")

        prior_params = {
            ArmPriors.BETA.value: ("alpha", "beta"),
            ArmPriors.NORMAL.value: ("mu", "sigma"),
        }

        if (prior_type, reward_type) not in allowed_combos_mab:
            raise ValueError(
                f"Prior and reward type combination {prior_type} and\
                    {reward_type} is not supported."
            )

        for arm in arms:
            if prior_type in prior_params:
                missing_params = []
                for param in prior_params[prior_type]:
                    if param not in arm.keys():
                        missing_params.append(param)
                    elif arm[param] is None:
                        missing_params.append(param)

                if missing_params:
                    raise ValueError(
                        f"{prior_type} prior requires {', '.join(missing_params)}."
                    )

        return values

    model_config = ConfigDict(from_attributes=True)


class MultiArmedBanditResponse(MultiArmedBanditBase):
    """
    Pydantic model for an response for experiment creation.
    Returns the id of the experiment and the arms
    """

    experiment_id: int
    arms: list[ArmResponse]

    model_config = ConfigDict(from_attributes=True)


class MABObservationBase(BaseModel):
    """
    Pydantic model for an observation of the experiment.
    """

    experiment_id: int
    arm_id: int

    model_config = ConfigDict(from_attributes=True)


class MABObservationBinary(MABObservationBase):
    """
    Pydantic model for binary observations of the experiment.
    """

    reward: Outcome

    model_config = ConfigDict(from_attributes=True)


class MABObservationRealVal(MABObservationBase):
    """
    Pydantic model for real-valued observations of the experiment.
    """

    reward: float

    model_config = ConfigDict(from_attributes=True)


class MABObservationBinaryResponse(MABObservationBinary):
    """
    Pydantic model for an response for observation creation
    """

    observation_id: int
    obs_datetime_utc: datetime

    model_config = ConfigDict(from_attributes=True)


class MABObservationRealValResponse(MABObservationRealVal):
    """
    Pydantic model for an response for observation creation
    """

    observation_id: int
    obs_datetime_utc: datetime

    model_config = ConfigDict(from_attributes=True)
