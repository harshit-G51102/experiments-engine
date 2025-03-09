from enum import Enum, StrEnum
from typing import Any, Self

import numpy as np
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.types import NonNegativeInt


class EventType(StrEnum):
    """Types of events that can trigger a notification"""

    DAYS_ELAPSED = "days_elapsed"
    TRIALS_COMPLETED = "trials_completed"
    PERCENTAGE_BETTER = "percentage_better"


class Notifications(BaseModel):
    """
    Pydantic model for a notifications.
    """

    onTrialCompletion: bool = False
    numberOfTrials: NonNegativeInt | None
    onDaysElapsed: bool = False
    daysElapsed: NonNegativeInt | None
    onPercentBetter: bool = False
    percentBetterThreshold: NonNegativeInt | None

    @model_validator(mode="after")
    def validate_has_assocatiated_value(self) -> Self:
        """
        Validate that the required corresponding fields have been set.
        """
        if self.onTrialCompletion and (
            not self.numberOfTrials or self.numberOfTrials == 0
        ):
            raise ValueError(
                "numberOfTrials is required when onTrialCompletion is True"
            )
        if self.onDaysElapsed and (not self.daysElapsed or self.daysElapsed == 0):
            raise ValueError("daysElapsed is required when onDaysElapsed is True")
        if self.onPercentBetter and (
            not self.percentBetterThreshold or self.percentBetterThreshold == 0
        ):
            raise ValueError(
                "percentBetterThreshold is required when onPercentBetter is True"
            )

        return self


class NotificationsResponse(BaseModel):
    """
    Pydantic model for a response for notifications
    """

    model_config = ConfigDict(from_attributes=True)

    notification_id: int
    notification_type: EventType
    notification_value: NonNegativeInt
    is_active: bool


class Outcome(float, Enum):
    """
    Enum for the outcome of a trial.
    """

    SUCCESS = 1
    FAILURE = 0


class ArmPriors(StrEnum):
    """
    Enum for the prior distribution of the arm.
    """

    BETA = "beta"
    NORMAL = "normal"

    def __call__(self, theta: np.ndarray, **kwargs: Any) -> np.ndarray:
        """
        Return the log pdf of the input param.
        """
        if self == ArmPriors.BETA:
            alpha = kwargs.get("alpha", np.ones_like(theta))
            beta = kwargs.get("beta", np.ones_like(theta))
            return (alpha - 1) * np.log(theta) + (beta - 1) * np.log(1 - theta)

        elif self == ArmPriors.NORMAL:
            mu = kwargs.get("mu", np.zeros_like(theta))
            covariance = kwargs.get("covariance", np.diag(np.ones_like(theta)))
            inv_cov = np.linalg.inv(covariance)
            x = theta - mu
            return -0.5 * x @ inv_cov @ x


class RewardLikelihood(StrEnum):
    """
    Enum for the likelihood distribution of the reward.
    """

    BERNOULLI = "binary"
    NORMAL = "real-valued"

    def __call__(self, reward: np.ndarray, probs: np.ndarray) -> np.ndarray:
        """
        Calculate the log likelihood of the reward.

        Parameters
        ----------
        reward : The reward.
        probs : The probability of the reward.
        """
        if self == RewardLikelihood.NORMAL:
            return -0.5 * np.sum((reward - probs) ** 2)
        elif self == RewardLikelihood.BERNOULLI:
            return np.sum(reward * np.log(probs) + (1 - reward) * np.log(1 - probs))


class ContextType(StrEnum):
    """
    Enum for the type of context.
    """

    BINARY = "binary"
    REAL_VALUED = "real-valued"


class ContextLinkFunctions(StrEnum):
    """
    Enum for the link function of the arm params and context.
    """

    NONE = "none"
    LOGISTIC = "logistic"

    def __call__(self, x: np.ndarray) -> np.ndarray:
        """
        Apply the link function to the input param.

        Parameters
        ----------
        x : The input param.
        """
        if self == ContextLinkFunctions.NONE:
            return x
        elif self == ContextLinkFunctions.LOGISTIC:
            return 1.0 / (1.0 + np.exp(-x))


allowed_combos_mab = [
    (ArmPriors.BETA, RewardLikelihood.BERNOULLI),
    (ArmPriors.NORMAL, RewardLikelihood.NORMAL),
]
