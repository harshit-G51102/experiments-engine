from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import authenticate_key, get_current_user
from ..database import get_async_session
from ..exp_engine.schemas import RewardLikelihood
from ..users.models import UserDB
from .models import (
    delete_mab_by_id,
    get_all_mabs,
    get_all_rewards_by_experiment_id,
    get_mab_by_id,
    save_mab_to_db,
    save_observation_to_db,
)
from .sampling_utils import choose_arm, update_arm_params
from .schemas import (
    ArmResponse,
    MABObservationBinary,
    MABObservationBinaryResponse,
    MABObservationRealVal,
    MABObservationRealValResponse,
    MultiArmedBandit,
    MultiArmedBanditResponse,
)

router = APIRouter(prefix="/mab", tags=["Multi-Armed Bandits"])


@router.post("/", response_model=MultiArmedBanditResponse)
async def create_mab(
    experiment: MultiArmedBandit,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> MultiArmedBanditResponse:
    """
    Create a new experiment.
    """
    response = await save_mab_to_db(experiment, user_db.user_id, asession)
    # return response
    return MultiArmedBanditResponse.model_validate(response)


@router.get("/", response_model=list[MultiArmedBanditResponse])
async def get_mabs(
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[MultiArmedBanditResponse]:
    """
    Get details of all experiments.
    """
    experiments = await get_all_mabs(user_db.user_id, asession)
    return [
        MultiArmedBanditResponse.model_validate(experiment)
        for experiment in experiments
    ]


@router.get("/{experiment_id}", response_model=MultiArmedBanditResponse)
async def get_mab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> MultiArmedBanditResponse | HTTPException:
    """
    Get details of experiment with the provided `experiment_id`.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
    if experiment is None:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    return MultiArmedBanditResponse.model_validate(experiment)


@router.delete("/{experiment_id}", response_model=dict)
async def delete_mab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Delete the experiment with the provided `experiment_id`.
    """
    try:
        experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
        if experiment is None:
            return HTTPException(
                status_code=404, detail=f"Experiment with id {experiment_id} not found"
            )
        await delete_mab_by_id(experiment_id, user_db.user_id, asession)
        return {"message": f"Experiment with id {experiment_id} deleted successfully."}
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error: {e}")


@router.get("/{experiment_id}/draw", response_model=ArmResponse)
async def get_arm(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ArmResponse | HTTPException:
    """
    Get which arm to pull next for provided experiment.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
    if experiment is None:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )
    experiment_data = MultiArmedBanditResponse.model_validate(experiment)
    chosen_arm = choose_arm(experiment=experiment_data)
    return ArmResponse.model_validate(experiment.arms[chosen_arm])


@router.put("/{experiment_id}/{arm_id}/{outcome}", response_model=ArmResponse)
async def update_arm(
    experiment_id: int,
    arm_id: int,
    outcome: float,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ArmResponse | HTTPException:
    """
    Update the arm with the provided `arm_id` for the given
    `experiment_id` based on the `outcome`.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
    if experiment is None:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    arms = [a for a in experiment.arms if a.arm_id == arm_id]
    if not arms:
        return HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    else:
        arm = arms[0]
        reward = None
        if experiment.reward_type == RewardLikelihood.BERNOULLI.value:
            reward = MABObservationBinary.model_validate(
                dict(experiment_id=experiment_id, arm_id=arm_id, reward=outcome)
            )
            arm.alpha, arm.beta = update_arm_params(
                arm, experiment.prior_type, experiment.reward_type, reward.reward
            )

        elif experiment.reward_type == RewardLikelihood.NORMAL.value:
            reward = MABObservationRealVal.model_validate(
                dict(experiment_id=experiment_id, arm_id=arm_id, reward=outcome)
            )
            arm.mu, arm.sigma = update_arm_params(
                arm, experiment.prior_type, experiment.reward_type, reward.reward
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Reward type not supported.",
            )

        if not reward:
            raise HTTPException(
                status_code=400, detail="No reward found for the experiment."
            )

        await asession.commit()
        await save_observation_to_db(reward, user_db.user_id, asession)

    return ArmResponse.model_validate(arm)


@router.get(
    "/{experiment_id}/outcomes",
    response_model=list[MABObservationRealValResponse | MABObservationBinaryResponse],
)
async def get_outcomes(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> list[MABObservationRealValResponse | MABObservationBinaryResponse]:
    """
    Get the outcomes for the experiment.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
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
            MABObservationRealValResponse.model_validate(reward)
            if experiment.reward_type == RewardLikelihood.NORMAL.value
            else MABObservationBinaryResponse.model_validate(reward)
        )
        for reward in rewards
    ]
