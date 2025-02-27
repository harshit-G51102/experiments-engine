import numpy as np

from ..exp_engine.schemas import ArmPriors, ContextLinkFunctions, RewardLikelihood
from .schemas import ContextualArmResponse, ContextualBanditResponse


def sample_normal(
    mus: list[np.ndarray],
    covariances: list[np.ndarray],
    context: np.ndarray,
    link_function: ContextLinkFunctions,
) -> int:
    """
    Thompson Sampling with normal prior.

    Parameters
    ----------
    mus: mean of Normal distribution for each arm
    covariances: covariance matrix of Normal distribution for each arm
    context: context vector
    link_function: link function for the context
    """
    samples = np.array(
        [
            np.random.multivariate_normal(mean=mu, cov=cov)
            for mu, cov in zip(mus, covariances)
        ]
    ).reshape(-1, len(context))
    probs = link_function.value(samples @ context)
    return probs.argmax()


def update_arm_normal(
    current_mu: np.ndarray,
    current_covariance: np.ndarray,
    reward: float,
    context: np.ndarray,
    sigma_llhood: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Update the mean and covariance of the normal distribution.

    Parameters
    ----------
    current_mu : The mean of the normal distribution.
    current_covariance : The covariance matrix of the normal distribution.
    reward : The reward of the arm.
    context : The context vector.
    sigma_llhood : The stddev of the likelihood.
    """
    new_covariance_inv = (
        np.linalg.inv(current_covariance) + (context.T @ context) / sigma_llhood**2
    )
    new_covariance = np.linalg.inv(new_covariance_inv)

    new_mu = new_covariance @ (
        np.linalg.inv(current_covariance) @ current_mu
        + context * reward / sigma_llhood**2
    )
    return new_mu, new_covariance


def choose_arm(experiment: ContextualBanditResponse, context: np.ndarray) -> int:
    """
    Choose the arm with the highest probability.

    Parameters
    ----------
    experiment : The experiment object.
    context : The context vector.
    """
    # TODO need to implement updating for bernoulli updates
    if experiment.reward_type == RewardLikelihood.BERNOULLI:
        raise NotImplementedError("Bernoulli updates are not implemented yet")

    link_function = (
        ContextLinkFunctions.NONE
        if experiment.reward_type == RewardLikelihood.NORMAL
        else ContextLinkFunctions.LOGISTIC
    )
    return sample_normal(
        mus=[arm.mu for arm in experiment.arms],
        covariances=[arm.covariance for arm in experiment.arms],
        context=context,
        link_function=link_function,
    )


def update_arm_params(
    arm: ContextualArmResponse,
    prior_type: ArmPriors,
    reward_type: RewardLikelihood,
    reward: float,
    context: np.ndarray,
) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Update the arm parameters.

    Parameters
    ----------
    arm : The arm object.
    prior_type : The prior type of the arm.
    reward_type : The reward type of the arm.
    reward : The reward of the arm.
    context : The context vector.
    """
    if prior_type == ArmPriors.NORMAL and reward_type == RewardLikelihood.NORMAL:
        return update_arm_normal(
            current_mu=np.array(arm.mu),
            current_covariance=np.ndarray(arm.covariance),
            reward=reward,
            context=np.array(context),
            sigma_llhood=1.0,  # TODO: need to implement likelihood stddev
        )

    return None
