from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import authenticate_key, get_current_user
from ..database import get_async_session
from ..exp_engine_utils.sampling import ts_beta_binomial
from ..models import get_notifications_from_db, save_notifications_to_db
from ..schemas import NotificationsResponse, Outcome
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
    mab = await save_mab_to_db(experiment, user_db.user_id, asession)
    notifications = await save_notifications_to_db(
        experiment_id=mab.experiment_id,
        user_id=user_db.user_id,
        notifications=experiment.notifications,
        asession=asession,
    )

    mab_dict = mab.to_dict()
    mab_dict["notifications"] = [n.to_dict() for n in notifications]

    return MultiArmedBanditResponse.model_validate(mab_dict)


@router.get("/", response_model=list[MultiArmedBanditResponse])
async def get_mabs(
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[MultiArmedBanditResponse]:
    """
    Get details of all experiments.
    """
    experiments = await get_all_mabs(user_db.user_id, asession)

    all_experiments = []
    for exp in experiments:
        exp_dict = exp.to_dict()
        exp_dict["notifications"] = [
            n.to_dict()
            for n in await get_notifications_from_db(
                exp.experiment_id, exp.user_id, asession
            )
        ]
        all_experiments.append(
            MultiArmedBanditResponse.model_validate(
                {
                    **exp_dict,
                    "notifications": [
                        NotificationsResponse(**n) for n in exp_dict["notifications"]
                    ],
                }
            )
        )

    return [
        MultiArmedBanditResponse.model_validate(experiment)
        for experiment in all_experiments
    ]


@router.get("/{experiment_id}", response_model=MultiArmedBanditResponse)
async def get_mab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> MultiArmedBanditResponse:
    """
    Get details of experiment with the provided `experiment_id`.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)

    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    experiment_dict = experiment.to_dict()
    experiment_dict["notifications"] = [
        n.to_dict()
        for n in await get_notifications_from_db(
            experiment.experiment_id, experiment.user_id, asession
        )
    ]

    return MultiArmedBanditResponse.model_validate(experiment_dict)


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
            raise HTTPException(
                status_code=404, detail=f"Experiment with id {experiment_id} not found"
            )
        await delete_mab_by_id(experiment_id, user_db.user_id, asession)
        return {"message": f"Experiment with id {experiment_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}") from e


@router.get("/{experiment_id}/draw", response_model=Arm)
async def get_arm(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ArmResponse:
    """
    Get which arm to pull next for provided experiment.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    alphas = [arm.alpha_prior for arm in experiment.arms]
    betas = [arm.beta_prior for arm in experiment.arms]
    successes = [arm.successes for arm in experiment.arms]
    failures = [arm.failures for arm in experiment.arms]

    chosen_arm = ts_beta_binomial(alphas, betas, successes, failures)

    return ArmResponse.model_validate(experiment.arms[chosen_arm])


@router.put("/{experiment_id}/{arm_id}/{outcome}", response_model=Arm)
async def update_arm(
    experiment_id: int,
    arm_id: int,
    outcome: Outcome,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ArmResponse:
    """
    Update the arm with the provided `arm_id` for the given
    `experiment_id` based on the `outcome`.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    arms = [a for a in experiment.arms if a.arm_id == arm_id]
    if not arms:
        raise HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    else:
        arm = arms[0]

    if outcome == Outcome.SUCCESS:
        arm.successes += 1
    else:
        arm.failures += 1

    await asession.commit()

    return ArmResponse.model_validate(arm)
