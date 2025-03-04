from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..schemas import Notifications, NotificationsResponse


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

    alpha_prior: int = Field(
        description="The alpha parameter of the beta distribution.",
        examples=[1, 10, 100],
    )
    beta_prior: int = Field(
        description="The beta parameter of the beta distribution.",
        examples=[1, 10, 100],
    )

    model_config = ConfigDict(from_attributes=True)


class ArmResponse(Arm):
    """
    Pydantic model for an response for arm creation
    """

    arm_id: int

    successes: int = Field(
        description="The number of successes for the arm.",
        examples=[0, 10, 100],
        default=0,
    )
    failures: int = Field(
        description="The number of failures for the arm.",
        examples=[0, 10, 100],
        default=0,
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


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
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class MultiArmedBandit(MultiArmedBanditBase):
    """
    Pydantic model for an experiment.
    """

    arms: list[Arm]
    notifications: Notifications
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def arms_at_least_two(self) -> Self:
        if len(self.arms) < 2:
            raise ValueError("The experiment must have at least two arms.")
        return self


class MultiArmedBanditResponse(MultiArmedBanditBase):
    """
    Pydantic model for an response for experiment creation.
    Returns the id of the experiment and the arms
    """

    experiment_id: int
    arms: list[ArmResponse]
    notifications: list[NotificationsResponse]

    model_config = ConfigDict(from_attributes=True, revalidate_instances="always")
