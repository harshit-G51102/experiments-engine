from enum import Enum

# --- Outcome ---


class Outcome(str, Enum):
    """
    Enum for the outcome of a trial.
    """

    SUCCESS = "success"
    FAILURE = "failure"


class ArmPriors(Enum):
    """
    Enum for the prior distribution of the arm.
    """

    BETA = "beta"
    NORMAL = "normal"


class RewardLikelihood(Enum):
    """
    Enum for the likelihood distribution of the reward.
    """

    BERNOULLI = "binary"
    NORMAL = "real-valued"
