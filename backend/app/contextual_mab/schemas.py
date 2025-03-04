from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from ..exp_engine.schemas import ArmPriors, ContextType
from ..mab.schemas import (
    MABObservationBinary,
    MABObservationRealVal,
    MultiArmedBanditBase,
)


class Context(BaseModel):
    """
    Pydantic model for a binary-valued context of the experiment.
    """

    name: str = Field(
        description="Name of the context",
        examples=["Context 1"],
    )
    description: str = Field(
        description="Description of the context",
        examples=["This is a description of the context."],
    )
    value_type: ContextType = Field(
        description="Type of value the context can take", default=ContextType.BINARY
    )
    model_config = ConfigDict(from_attributes=True)


class ContextResponse(Context):
    """
    Pydantic model for an response for context creation
    """

    context_id: int
    model_config = ConfigDict(from_attributes=True)


class ContextualArm(BaseModel):
    """
    Pydantic model for a contextual arm of the experiment.
    """

    name: str = Field(
        max_length=150,
        examples=["Arm 1"],
    )
    description: str = Field(
        max_length=500,
        examples=["This is a description of the arm."],
    )

    mu_init: float = Field(default=0.0)
    sigma_init: float = Field(default=1.0)

    @model_validator(mode="after")
    def check_values(self) -> Self:
        """
        Check if the values are unique and set new attributes.
        """
        sigma = self.sigma_init
        if sigma is not None and sigma <= 0:
            raise ValueError("sigma must be greater than 0.")
        return self

    model_config = ConfigDict(from_attributes=True)


class ContextualArmResponse(ContextualArm):
    """
    Pydantic model for an response for contextual arm creation
    """

    arm_id: int
    mu: list[float]
    covariance: list[list[float]]

    model_config = ConfigDict(from_attributes=True)


class ContextualBandit(MultiArmedBanditBase):
    """
    Pydantic model for a contextual experiment.
    """

    prior_type: ArmPriors = Field(
        description="The type of prior distribution for the arms.",
        default=ArmPriors.NORMAL,
    )
    arms: list[ContextualArm]
    contexts: list[Context]

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def check_experiment_inputs(self) -> "ContextualBandit":
        """
        Check if the context of the experiment is valid.
        """
        if self.prior_type != ArmPriors.NORMAL:
            raise ValueError(
                f"{self.prior_type.value} prior is not supported for contextual arms."
            )
        return self


class ContextualBanditResponse(ContextualBandit):
    """
    Pydantic model for an response for contextual experiment creation.
    Returns the id of the experiment, the arms and the contexts
    """

    experiment_id: int
    arms: list[ContextualArmResponse]
    contexts: list[ContextResponse]

    model_config = ConfigDict(from_attributes=True)


class CMABObservationBinary(MABObservationBinary):
    """
    Pydantic model for a binary-valued observation of the experiment.
    """

    context: list[float]

    model_config = ConfigDict(from_attributes=True)


class CMABObservationRealVal(MABObservationRealVal):
    """
    Pydantic model for a binary-valued observation of the experiment.
    """

    context: list[float]

    model_config = ConfigDict(from_attributes=True)


class CMABObservationBinaryResponse(CMABObservationBinary):
    """
    Pydantic model for an response for binary observation creation
    """

    observation_id: int
    model_config = ConfigDict(from_attributes=True)


class CMABObservationRealValResponse(CMABObservationRealVal):
    """
    Pydantic model for an response for real-valued observation creation
    """

    observation_id: int
    model_config = ConfigDict(from_attributes=True)
