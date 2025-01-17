from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_user, authenticate_key
from ..database import get_async_session
from ..users.models import UserDB
from .models import (
    get_all_contextual_mabs,
    get_contextual_mab_by_id,
    save_contextual_mab_to_db,
    delete_contextual_mab_by_id,
)
from .schemas import (
    ContextualArmResponse,
    ContextualBandit,
    ContextualBanditResponse,
)
import numpy as np
from ..exp_engine_utils.sampling import ts_beta_binomial
from ..schemas import Outcome


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
    if (experiment.arms[0].successes.shape != experiment.arms[0].failures.shape) or (
        experiment.arms[0].successes.size
        == np.prod([len(c.values) for c in experiment.contexts])
    ):
        raise HTTPException(
            status_code=400,
            detail="Successes and failures are wrong shape.",
        )

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
        await delete_contextual_mab_by_id(experiment_id, user_db.user_id, asession)
        return {"detail": f"Experiment {experiment_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.get("/{experiment_id}/draw", response_model=ContextualArmResponse)
async def get_arm(
    experiment_id: int,
    context: list[int],
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualArmResponse | HTTPException:
    """
    Get which arm to pull next for provided experiment.
    """
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )
    if experiment is None:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    # Get coordinates for indexing successes and failures for the arms
    coordinates = [c.values.argwhere(v) for c, v in zip(experiment.contexts, context)]

    alphas = [arm.alpha_prior for arm in experiment.arms]
    betas = [arm.beta_prior for arm in experiment.arms]
    successes = [arm.successes[coordinates] for arm in experiment.arms]
    failures = [arm.failures[coordinates] for arm in experiment.arms]

    chosen_arm = ts_beta_binomial(alphas, betas, successes, failures)

    return ContextualArmResponse.model_validate(experiment.arms[chosen_arm])


@router.put("/{experiment_id}/{arm_id}/{outcome}", response_model=ContextualArmResponse)
async def update_arm(
    experiment_id: int,
    arm_id: int,
    context: list[int],
    outcome: Outcome,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualArmResponse | HTTPException:
    """
    Update the arm with the provided `arm_id` for the given `experiment_id` based on the `outcome`.
    """
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )
    if experiment is None:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    arms = [a for a in experiment.arms if a.arm_id == arm_id]
    if not arms:
        return HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    else:
        arm = arms[0]

    # Get coordinates for indexing successes and failures for the arms
    coordinates = [c.values.argwhere(v) for c, v in zip(experiment.contexts, context)]

    if outcome == Outcome.SUCCESS:
        arm.successes[coordinates] += 1
    else:
        arm.failures[coordinates] += 1

    await asession.commit()

    return ContextualArmResponse.model_validate(arm)
