from pydantic import BaseModel, ConfigDict, Field
from ..mab.schemas import Arm, MultiArmedBandit, MultiArmedBanditResponse


class Context(BaseModel):
    """
    Pydantic model for a binary-valued context of the experiment.
    """

    name: str = Field(
        max_length=150,
        examples=["Context 1"],
    )
    description: str = Field(
        max_length=500,
        examples=["This is a description of the context."],
    )

    model_config = ConfigDict(from_attributes=True)


class ContextResponse(Context):
    """
    Pydantic model for an response for context creation
    """

    context_id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ContextualArm(Arm):
    """
    Pydantic model for a contextual arm of the experiment.
    """

    context: dict[str, int] = Field(
        description="dictionary of context id and its value for this arm",
        examples=[{"1": 1, "2": 0}],
    )

    model_config = ConfigDict(from_attributes=True)


class ContextualArmResponse(ContextualArm):
    """
    Pydantic model for an response for contextual arm creation
    """

    arm_id: int

    model_config = ConfigDict(from_attributes=True)


class ContextualBandit(MultiArmedBandit):
    """
    Pydantic model for a contextual experiment.
    """

    arms: list[ContextualArm]
    contexts: list[Context]

    model_config = ConfigDict(from_attributes=True)


class ContextualBanditResponse(MultiArmedBanditResponse):
    """
    Pydantic model for an response for contextual experiment creation.
    Returns the id of the experiment, the arms and the contexts
    """

    arms: list[ContextualArmResponse]
    contexts: list[ContextResponse]

    model_config = ConfigDict(from_attributes=True)
