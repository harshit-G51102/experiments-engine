import numpy as np
from numpy.random import beta, normal

from ..mab.schemas import MultiArmedBanditResponse
from .schemas import ArmPriors, RewardLikelihood


def mab_beta_binomial(
    alphas: np.ndarray, betas: np.ndarray, successes: np.ndarray, failures: np.ndarray
) -> int:
    """
    Thompson Sampling with Beta-Binomial distribution.

    Parameters
    ----------
    alphas : alpha parameter of Beta distribution for each arm
    betas : beta parameter of Beta distribution for each arm
    successes : number of successes for each arm
    failures : number of failures for each arm
    """
    samples = beta(alphas + successes, betas + failures)
    return samples.argmax()


def mab_normal(
    mus: np.ndarray, sigmas: np.ndarray, rewards: np.ndarray, sigma_llhood: float
) -> int:
    """
    Thompson Sampling with conjugate normal distribution.

    Parameters
    ----------
    mus: mean of Normal distribution for each arm
    sigmas: standard deviation of Normal distribution for each arm
    rewards: rewards for each arm
    sigma_llhood:
    """
    num_updates = np.array([reward.size for reward in rewards])
    current_sigmas = (sigmas * sigma_llhood) / np.sqrt(
        num_updates * sigmas**2 + sigma_llhood**2
    )
    current_mus = (current_sigmas / sigmas) ** 2 * mus + (
        current_sigmas / sigmas
    ) ** 2 * num_updates * np.array([reward.mean() for reward in rewards])

    samples = normal(loc=current_mus, scale=current_sigmas)
    return samples.argmax()


def mab_choose_arm(experiment: MultiArmedBanditResponse) -> int:
    """
    Choose arm based on posterior

    Parameters
    ----------
    experiment : MultiArmedBanditResponse
        The experiment data containing priors and rewards for each arm.
    """
    print(experiment.prior_type, experiment.reward_type)
    if (experiment.prior_type == ArmPriors.BETA) and (
        experiment.reward_type == RewardLikelihood.BERNOULLI
    ):
        alphas = np.array([arm.alpha for arm in experiment.arms])
        betas = np.array([arm.beta for arm in experiment.arms])
        successes = np.array([arm.successes for arm in experiment.arms])
        failures = np.array([arm.failures for arm in experiment.arms])
        return mab_beta_binomial(
            alphas=alphas, betas=betas, successes=successes, failures=failures
        )

    elif (experiment.prior_type == ArmPriors.NORMAL) and (
        experiment.reward_type == RewardLikelihood.NORMAL
    ):
        mus = np.array([arm.mu for arm in experiment.arms])
        sigmas = np.array([arm.sigma for arm in experiment.arms])
        rewards = [np.array(arm.reward) for arm in experiment.arms]
        # TODO: add support for non-std sigma_llhood
        return mab_normal(mus=mus, sigmas=sigmas, rewards=rewards, sigma_llhood=1.0)
    else:
        raise ValueError("Prior and reward type combination is not supported.")
