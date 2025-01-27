from .schemas import ContextualBandit, ContextType
import numpy as np
from fastapi.exceptions import HTTPException


def check_experiment_inputs(experiment: ContextualBandit) -> None:
    """
    Check if the context of the experiment is valid.
    """
    context_values = list(ContextType._value2member_map_.keys())
    for context in experiment.contexts:
        if context.context_type not in context_values:
            raise HTTPException(
                status_code=400,
                detail=f"Context type must be one of the following: {context_values}",
            )
        if context.context_type == ContextType.BINARY:
            if len(context.values) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Binary context should have 2 values.",
                )
        elif context.context_type == ContextType.CATEGORICAL:
            if len(context.values) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Categorical context should have more than 1 value.",
                )

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
