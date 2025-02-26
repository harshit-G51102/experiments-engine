from enum import Enum


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


class RewardLikelihood(Enum):
    """
    Enum for the likelihood distribution of the reward.
    """

    BERNOULLI = "binary"
    NORMAL = "real-valued"


# class PosteriorSampling(Enum):
#     """"""
#     THOMPSON_SAMPLING = "thompson_sampling"


# class ContextLinkFunctions(Enum):
#     NONE = "none"
#     LOGISTIC = "logistic"


# class ContextualArmPriorParams(BaseModel):
#     prior_type: ArmPriors
#     mu: list
#     sigma: list

#     @classmethod
#     def validate(cls, values):
#         prior_type = values.get("prior_type")
#         if prior_type == ArmPriors.BETA:
#             raise ValueError(
#                 f"{prior_type.BETA} prior is not supported for contextual arms."
#             )
#         elif (prior_type == ArmPriors.NORMAL) and (
#             values.get("mu") is None or values.get("sigma") is None
#         ):
#             raise ValueError(
#                 f"{prior_type.NORMAL} prior requires mu and sigma parameters."
#             )

#     class Config:
#         validate_assignment = True
