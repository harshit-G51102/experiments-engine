from typing import Annotated

import numpy as np
from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import authenticate_key, get_current_user
from ..database import get_async_session
from ..exp_engine.schemas import (
    ContextType,
    RewardLikelihood,
)

# from ..exp_engine.sampling import ts_beta_binomial
from ..users.models import UserDB
from .models import (
    delete_contextual_mab_by_id,
    get_all_contextual_mabs,
    get_all_rewards_by_experiment_id,
    get_contextual_mab_by_id,
    get_rewards_by_experiment_arm_id,
    save_contextual_mab_to_db,
    save_contextual_obs_to_db,
)
from .sampling_utils import choose_arm, update_arm_params
from .schemas import (
    CMABObservationBinary,
    CMABObservationRealVal,
    ContextualArmResponse,
    ContextualBandit,
    ContextualBanditResponse,
)

router = APIRouter(prefix="/contextual_mab", tags=["Contextual Bandits"])


@router.post("/", response_model=ContextualBanditResponse)
async def create_contextual_mabs(
    experiment: ContextualBandit,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualBanditResponse | HTTPException:
    """
    Create a new contextual experiment with different priors for each context.
    """
    response = await save_contextual_mab_to_db(experiment, user_db.user_id, asession)
    return ContextualBanditResponse.model_validate(response)


@router.get("/", response_model=list[ContextualBanditResponse])
async def get_contextual_mabs(
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[ContextualBanditResponse]:
    """
    Get details of all experiments.
    """
    experiments = await get_all_contextual_mabs(user_db.user_id, asession)
    return [
        ContextualBanditResponse.model_validate(experiment)
        for experiment in experiments
    ]


@router.get("/{experiment_id}", response_model=ContextualBanditResponse)
async def get_contextual_mab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualBanditResponse | HTTPException:
    """
    Get details of experiment with the provided `experiment_id`.
    """
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )
    if experiment is None:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    return ContextualBanditResponse.model_validate(experiment)


@router.delete("/{experiment_id}", response_model=dict)
async def delete_contextual_mab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Delete the experiment with the provided `experiment_id`.
    """
    try:
        experiment = await get_contextual_mab_by_id(
            experiment_id, user_db.user_id, asession
        )
        if experiment is None:
            return HTTPException(
                status_code=404, detail=f"Experiment with id {experiment_id} not found"
            )
        await delete_contextual_mab_by_id(experiment_id, user_db.user_id, asession)
        return {"detail": f"Experiment {experiment_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}") from e


@router.get("/{experiment_id}/draw", response_model=ContextualArmResponse)
async def get_arm(
    experiment_id: int,
    context: list[float] = Query(..., description="List of context values"),
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualArmResponse:
    """
    Get which arm to pull next for provided experiment.
    """
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )
    if len(experiment.contexts) != len(context):
        raise HTTPException(
            status_code=400,
            detail="Number of contexts provided does not match the num contexts.",
        )
    for i, (c_db, c) in enumerate(
        zip(sorted(experiment.contexts, key=lambda x: x.context_id), context)
    ):
        if c_db.value_type == ContextType.BINARY.value and c not in [0, 1]:
            raise HTTPException(
                status_code=400,
                detail=f"Context {i} must be binary.",
            )
        elif c_db.value_type == ContextType.REAL_VALUED.value and not isinstance(
            c, (int, float)
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Context {i} must be real-valued.",
            )
    chosen_arm = choose_arm(experiment, np.array(context))

    return ContextualArmResponse.model_validate(experiment.arms[chosen_arm])


@router.put("/{experiment_id}/{arm_id}/{outcome}", response_model=ContextualArmResponse)
async def update_arm(
    experiment_id: int,
    arm_id: int,
    reward: float,
    context: list[float] = Query(..., description="List of context values"),
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualArmResponse:
    """
    Update the arm with the provided `arm_id` for the given
    `experiment_id` based on the `outcome`.
    """
    # Get the experiment
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    if len(experiment.contexts) != len(context):
        raise HTTPException(
            status_code=400,
            detail="Number of contexts provided does not match the num contexts.",
        )
    experiment_data = ContextualBanditResponse.model_validate(experiment)

    # Get the arm
    arms = [a for a in experiment_data.arms if a.arm_id == arm_id]
    if not arms:
        raise HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    else:
        arm = arms[0]

        # Check context values
        for i, (c_db, c) in enumerate(
            zip(sorted(experiment.contexts, key=lambda x: x.context_id), context)
        ):
            if c_db.value_type == ContextType.BINARY.value and c not in [0, 1]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Context {i} must be binary.",
                )
            elif c_db.value_type == ContextType.REAL_VALUED.value and not isinstance(
                c, (int, float)
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Context {i} must be real-valued.",
                )

        # Get all observations for the arm
        all_obs = await get_rewards_by_experiment_arm_id(
            experiment_id=experiment_id,
            arm_id=arm_id,
            user_id=user_db.user_id,
            asession=asession,
        )
        rewards = np.array([obs.reward for obs in all_obs] + [reward])
        contexts = np.array([obs.context_val for obs in all_obs] + [context])

        # Update the arm
        mu, covariance = update_arm_params(
            arm=arm,
            prior_type=experiment_data.prior_type,
            reward_type=experiment_data.reward_type,
            context=contexts,
            reward=rewards,
        )

        # Update the arm in the database
        arm.mu = mu.tolist()
        arm.covariance = covariance.tolist()
        await asession.commit()

        # Save the observation
        if experiment.reward_type == RewardLikelihood.BERNOULLI.value:
            observation = CMABObservationBinary.model_validate(
                dict(
                    experiment_id=experiment_id,
                    arm_id=arm_id,
                    reward=reward,
                    context=context,
                )
            )
        elif experiment.reward_type == RewardLikelihood.NORMAL.value:
            observation = CMABObservationRealVal.model_validate(
                dict(
                    experiment_id=experiment_id,
                    arm_id=arm_id,
                    reward=reward,
                    context=context,
                )
            )

        await save_contextual_obs_to_db(
            observation=observation, user_id=user_db.user_id, asession=asession
        )

        return ContextualArmResponse.model_validate(arm)


@router.get(
    "/{experiment_id}/outcomes",
    response_model=list[CMABObservationRealVal | CMABObservationBinary],
)
async def get_outcomes(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> list[CMABObservationRealVal | CMABObservationBinary]:
    """
    Get the outcomes for the experiment.
    """
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )
    if not experiment:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    rewards = await get_all_rewards_by_experiment_id(
        experiment_id=experiment.experiment_id,
        user_id=user_db.user_id,
        asession=asession,
    )
    return [
        (
            CMABObservationRealVal.model_validate(reward)
            if experiment.reward_type == RewardLikelihood.NORMAL.value
            else CMABObservationBinary.model_validate(reward)
        )
        for reward in rewards
    ]
