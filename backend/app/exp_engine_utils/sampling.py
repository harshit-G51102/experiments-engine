import numpy as np
from numpy.random import beta


def ts_beta_binomial(alphas: list, betas: list, successes: list, failures: list) -> int:
    """
    Thompson Sampling with Beta-Binomial distribution.

    Parameters
    ----------
    alphas : alpha parameter of Beta distribution for each arm
    betas : beta parameter of Beta distribution for each arm
    successes : number of successes for each arm
    failures : number of failures for each arm
    """
    samples = beta(
        np.array(alphas) + np.array(successes), np.array(betas) + np.array(failures)
    )
    return samples.argmax()
