from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.types import NonNegativeInt


class EventType(StrEnum):
    """Types of events that can trigger a notification"""

    DAYS_ELAPSED = "days_elapsed"
    TRIALS_COMPLETED = "trials_completed"
    PERCENTAGE_BETTER = "percentage_better"


class Outcome(StrEnum):
    """
    Enum for the outcome of a trial.
    """

    SUCCESS = "success"
    FAILURE = "failure"


class Notifications(BaseModel):
    """
    Pydantic model for a notifications.
    """

    onTrialCompletion: bool = False
    numberOfTrials: NonNegativeInt | None
    onDaysElapsed: bool = False
    daysElapsed: NonNegativeInt | None
    onPercentBetter: bool = False
    percentBetterThreshold: NonNegativeInt | None

    @model_validator(mode="after")
    def validate_has_assocatiated_value(self) -> Self:
        """
        Validate that the required corresponding fields have been set.
        """
        if self.onTrialCompletion and (
            not self.numberOfTrials or self.numberOfTrials == 0
        ):
            raise ValueError(
                "numberOfTrials is required when onTrialCompletion is True"
            )
        if self.onDaysElapsed and (not self.daysElapsed or self.daysElapsed == 0):
            raise ValueError("daysElapsed is required when onDaysElapsed is True")
        if self.onPercentBetter and (
            not self.percentBetterThreshold or self.percentBetterThreshold == 0
        ):
            raise ValueError(
                "percentBetterThreshold is required when onPercentBetter is True"
            )

        return self


class NotificationsResponse(BaseModel):
    """
    Pydantic model for a response for notifications
    """

    model_config = ConfigDict(from_attributes=True)

    notification_id: int
    notification_type: EventType
    notification_value: NonNegativeInt
    is_active: bool
