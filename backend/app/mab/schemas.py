from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..schemas import ArmPriors, RewardLikelihood


class ArmPriorParams(BaseModel):
    """
    Pydantic model for arm prior parameters.
    """

    prior_type: ArmPriors = ArmPriors.BETA
    alpha: float | None = None
    beta: float | None = None
    mu: float | None = None
    sigma: float | None = None

    @model_validator(mode="before")
    def check_prior_params(cls: BaseModel, values: dict) -> dict:
        """
        Check if the prior parameters are provided correctly.
        """
        prior_type = values.get("prior_type")
        error_message = "{prior_type} prior requires {params} parameters."
        if (prior_type == ArmPriors.BETA) and (
            values.get("alpha") is None or values.get("beta") is None
        ):
            error_message.format(prior_type=prior_type, params="alpha and beta")
            raise ValueError(error_message)
        elif (prior_type == ArmPriors.NORMAL) and (
            values.get("mu") is None or values.get("sigma") is None
        ):
            error_message.format(prior_type=prior_type, params="mu and sigma")
            raise ValueError(error_message)
        return values


class RewardLikelihoodParams(BaseModel):
    """
    Pydantic model for reward likelihood parameters.
    """

    reward_type: RewardLikelihood
    successes: int | None = None
    failures: int | None = None
    reward: list[float] | None = None

    @model_validator(mode="before")
    def check_reward_params(cls: BaseModel, values: dict) -> dict:
        """
        Check if the reward likelihood parameters are provided correctly.
        """
        reward_type = values.get("reward_type")
        error_message = "{reward_type} likelihood requires {params} parameters."
        if (reward_type == RewardLikelihood.BERNOULLI) and (
            values.get("successes") is None or values.get("failures") is None
        ):
            error_message.format(
                reward_type=reward_type, params="successes and failures"
            )
            raise ValueError(error_message)
        elif (reward_type == RewardLikelihood.NORMAL) and (
            values.get("reward") is None
        ):
            error_message.format(reward_type=reward_type, params="reward")
            raise ValueError(error_message)
        return values


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

    prior: ArmPriorParams = Field(
        description="The prior distribution of the arm.",
        default_factory=lambda: ArmPriorParams(
            prior_type=ArmPriors.BETA, alpha=1.0, beta=1.0
        ),
    )

    reward: RewardLikelihoodParams = Field(
        description="The type of observed reward, and corresponding paramters.",
        default_factory=lambda: RewardLikelihoodParams(
            reward_type=RewardLikelihood.BERNOULLI, successes=0, failures=0
        ),
    )
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
    def check_arm_and_experiment_reward_type(
        cls: MultiArmedBanditBase, values: dict
    ) -> dict:
        """
        Check if the arm reward type is same as the experiment reward type.
        """
        reward_type = values.get("reward_type")
        arms = values.get("arms")
        if arms is None:
            raise ValueError("At least one arm is required.")
        if any(arm["reward"]["reward_type"] != reward_type for arm in arms):
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
