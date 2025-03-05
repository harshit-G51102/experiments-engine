from enum import Enum
from typing import Any

import numpy as np


class Outcome(int, Enum):
    """
    Enum for the outcome of a trial.
    """

    SUCCESS = 1
    FAILURE = 0


class ArmPriors(Enum):
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


class RewardLikelihood(Enum):
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


class ContextType(Enum):
    """
    Enum for the type of context.
    """

    BINARY = "binary"
    REAL_VALUED = "real-valued"


class ContextLinkFunctions(Enum):
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
