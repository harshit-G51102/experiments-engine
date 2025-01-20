from .schemas import ContextualBandit
import numpy as np
from fastapi.exceptions import HTTPException


def check_experiment_inputs(experiment: ContextualBandit) -> None:
    """
    Check if the context of the experiment is valid.
    """
    for arm in experiment.arms:
        if (np.array(arm.successes).shape != np.array(arm.failures).shape) or (
            np.array(arm.successes).ndim != len(experiment.contexts)
        ):
            raise HTTPException(
                status_code=400,
                detail="Successes and failures are wrong shape.",
            )

        for i, context in enumerate(experiment.contexts):
            if np.array(arm.successes).shape[i] != len(context.values):
                raise HTTPException(
                    status_code=400,
                    detail=f"Dimension {i+1} should match the number of values in context {i+1}.",
                )
            if np.unique(context.values).shape != np.shape(context.values):
                raise HTTPException(
                    status_code=400,
                    detail=f"Context {i+1} values should be unique.",
                )
    return None
