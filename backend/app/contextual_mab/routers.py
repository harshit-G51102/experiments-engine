from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_user
from ..database import get_async_session
from ..users.models import UserDB
from .models import (
    get_all_contextual_mabs,
    get_contextual_mab_by_id,
    save_contextual_mab_to_db,
)
from ..mab.schemas import MultiArmedBandit
from .schemas import (
    Context,
    ContextualArm,
    ContextualBandit,
    ContextualBanditResponse,
)
import numpy as np


router = APIRouter(prefix="/contextual_mab", tags=["Contextual Bandits"])


@router.post("/no_context_priors", response_model=ContextualBanditResponse)
async def create_contextual_mab_no_context_priors(
    experiment: MultiArmedBandit,
    contexts: list[Context],
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualBanditResponse:
    """
    Create a new contextual experiment assuming same prior across contexts.
    """
    new_arms = []
    # TODO: explicit assuming only binary contexts.
    # Need to include logic for other types of contexts.
    context_values = [[0, 1] for _ in contexts]
    context_combos = (
        np.array(np.meshgrid(*context_values)).reshape(len(contexts), -1).astype(int).T
    )

    # Split each arm into multiple arms based per context combo
    for arm in experiment.arms:
        for combo in context_combos:
            context = dict(zip([str(i) for i in range(len(contexts))], combo))
            new_arm = ContextualArm(
                name=arm.name,
                description=arm.description,
                alpha_prior=arm.alpha_prior,
                beta_prior=arm.beta_prior,
                successes=arm.successes,
                failures=arm.failures,
                context=context,
            )
            new_arms.append(new_arm)

    # Create the new experiment with the new arms
    new_experiment = ContextualBandit(
        name=experiment.name,
        description=experiment.description,
        is_active=experiment.is_active,
        arms=new_arms,
        contexts=contexts,
    )
    response = await save_contextual_mab_to_db(
        new_experiment, user_db.user_id, asession
    )
    return ContextualBanditResponse.model_validate(response)


@router.post("/context_priors", response_model=ContextualBanditResponse)
async def create_contextual_mabs_with_priors(
    experiment: ContextualBandit,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualBanditResponse | HTTPException:
    """
    Create a new contextual experiment with different priors for each context.
    """
    # TODO implement check for number of arms / contexts
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
async def get_mab(
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


# @router.get("/{experiment_id}/draw", response_model=Arm)
# async def get_arm(
#     experiment_id: int,
#     user_db: UserDB = Depends(authenticate_key),
#     asession: AsyncSession = Depends(get_async_session),
# ) -> ArmResponse | HTTPException:
#     """
#     Get which arm to pull next for provided experiment.
#     """
#     experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
#     if experiment is None:
#         return HTTPException(
#             status_code=404, detail=f"Experiment with id {experiment_id} not found"
#         )

#     alphas = [arm.alpha_prior for arm in experiment.arms]
#     betas = [arm.beta_prior for arm in experiment.arms]
#     successes = [arm.successes for arm in experiment.arms]
#     failures = [arm.failures for arm in experiment.arms]

#     chosen_arm = ts_beta_binomial(alphas, betas, successes, failures)

#     return ArmResponse.model_validate(experiment.arms[chosen_arm])


# @router.put("/{experiment_id}/{arm_id}/{outcome}", response_model=Arm)
# async def update_arm(
#     experiment_id: int,
#     arm_id: int,
#     outcome: Outcome,
#     user_db: UserDB = Depends(authenticate_key),
#     asession: AsyncSession = Depends(get_async_session),
# ) -> ArmResponse | HTTPException:
#     """
#     Update the arm with the provided `arm_id` for the given `experiment_id` based on the `outcome`.
#     """
#     experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
#     if experiment is None:
#         return HTTPException(
#             status_code=404, detail=f"Experiment with id {experiment_id} not found"
#         )

#     arms = [a for a in experiment.arms if a.arm_id == arm_id]
#     if not arms:
#         return HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
#     else:
#         arm = arms[0]

#     if outcome == Outcome.SUCCESS:
#         arm.successes += 1
#     else:
#         arm.failures += 1

#     await asession.commit()

#     return ArmResponse.model_validate(arm)
