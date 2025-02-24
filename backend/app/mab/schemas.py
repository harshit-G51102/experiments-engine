from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from ..schemas import ArmPriors, RewardLikelihood


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
    prior_type: ArmPriors = ArmPriors.BETA
    alpha: float | None = None
    beta: float | None = None
    mu: float | None = None
    sigma: float | None = None

    # reward likelihood
    reward_type: RewardLikelihood = RewardLikelihood.BERNOULLI
    successes: int | None = None
    failures: int | None = None
    reward: list[float] | None = None

    @model_validator(mode="after")
    def check_params(self) -> Self:
        """
        Check the parameters are provided correctly.
        """
        prior_type = self.prior_type
        reward_type = self.reward_type

        prior_params = {
            ArmPriors.BETA: ("alpha", "beta"),
            ArmPriors.NORMAL: ("mu", "sigma"),
        }

        reward_params = {
            RewardLikelihood.BERNOULLI: ("successes", "failures"),
            RewardLikelihood.NORMAL: ("reward",),
        }

        if prior_type in prior_params:
            missing_params = [
                param
                for param in prior_params[prior_type]
                if getattr(self, param) is None
            ]
            if missing_params:
                raise ValueError(
                    f"{prior_type.value} prior requires {', '.join(missing_params)}."
                )

        if reward_type in reward_params:
            missing_params = [
                param
                for param in reward_params[reward_type]
                if getattr(self, param) is None
            ]
            if missing_params:
                raise ValueError(
                    f"{reward_type.value} llhood requires {', '.join(missing_params)}."
                )

        return self

    model_config = ConfigDict(from_attributes=True)


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
        arms = values.get("arms")
        if arms is None:
            raise ValueError("At least one arm is required.")
        if any(arm["reward_type"] != reward_type for arm in arms):
            raise ValueError(
                "All arms' reward type must be same as experiment reward type."
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
