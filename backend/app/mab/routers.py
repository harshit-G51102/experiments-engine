from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import authenticate_key, get_current_user
from ..database import get_async_session
from ..exp_engine.schemas import Outcome, RewardLikelihood
from ..exp_engine.thompson_sampling import mab_choose_arm
from ..users.models import UserDB
from .models import delete_mab_by_id, get_all_mabs, get_mab_by_id, save_mab_to_db
from .schemas import Arm, ArmResponse, MultiArmedBandit, MultiArmedBanditResponse

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


@router.get("/{experiment_id}/draw", response_model=Arm)
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
    chosen_arm = mab_choose_arm(experiment=experiment_data)

    return ArmResponse.model_validate(experiment.arms[chosen_arm])


@router.put("/{experiment_id}/{arm_id}/{outcome}", response_model=Arm)
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

    if experiment.reward_type == RewardLikelihood.BERNOULLI.value:
        if outcome == Outcome.SUCCESS.value:
            arm.successes += 1
        elif outcome == Outcome.FAILURE.value:
            arm.failures += 1
        else:
            return HTTPException(
                status_code=404,
                detail="Only binary-valued outcomes allowed for Bernoulli rewards.",
            )
    elif experiment.reward_type == RewardLikelihood.NORMAL.value:
        arm.reward = list(arm.reward) + [outcome]

    await asession.commit()

    return ArmResponse.model_validate(arm)
