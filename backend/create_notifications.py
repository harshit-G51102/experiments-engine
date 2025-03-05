# For each type of notification, get notification data from database
# check if experiment has reached milestone
# if so, create entry in messages table
# if not, do nothing

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import get_session
from app.models import ExperimentBaseDB, NotificationsDB
from app.schemas import EventType
from app.utils import setup_logger

logger = setup_logger()


def check_days_elapsed(
    experiment_id: int, notification_id: int, milestone_days: int, session: Session
) -> bool:
    """
    Check if the number of days elapsed since the experiment was created is greater
    than or equal to the milestone
    """
    experiment: ExperimentBaseDB | None = (
        session.query(ExperimentBaseDB).filter_by(experiment_id=experiment_id).first()
    )
    now = datetime.now(timezone.utc)
    if experiment:
        days_elapsed = (now - experiment.created_datetime_utc).days
        if days_elapsed >= milestone_days:
            # disable notification row
            session.query(NotificationsDB).filter_by(
                experiment_id=notification_id
            ).update({"is_active": False})
            logger.info(
                f"Creating message for experiment: {experiment_id} for days elapsed"
            )
            session.commit()
            return True
        logger.info(
            (
                f"Milestone not reached. Days elapsed for experiment {experiment_id} "
                f"is {days_elapsed}. Milestone is {milestone_days}"
            )
        )
        return False
    else:
        raise ValueError(f"Experiment with id {experiment_id} not found")


def check_trials_completed(
    experiment_id: int, notification_id: int, milestone_trials: int, session: Session
) -> bool:
    """
    Check if the number of trials completed for the experiment is greater than
    or equal to the milestone
    """
    experiment: ExperimentBaseDB | None = (
        session.query(ExperimentBaseDB).filter_by(experiment_id=experiment_id).first()
    )
    if experiment:
        if experiment.n_trials >= milestone_trials:
            session.query(NotificationsDB).filter_by(
                experiment_id=notification_id
            ).update({"is_active": False})
            logger.info(
                f"Creating message for experiment: {experiment_id} for trials completed"
            )
            session.commit()
            return True

        logger.info(
            (
                f"Milestone not reached. Trials completed for experiment "
                f"{experiment_id} is {experiment.n_trials}. "
                f"Milestone is {milestone_trials}"
            )
        )
        return False
    else:
        raise ValueError(f"Experiment with id {experiment_id} not found")


def check_percentage_better(
    experiment_id: int,
    notification_id: int,
    milestone_percentage: int,
    session: Session,
) -> bool:
    """
    TBD: Implement this function
    """
    return False


def process_notifications() -> int:
    """
    Process all active notifications
    """
    session = next(get_session())
    # get all active notifications
    notifications = session.query(NotificationsDB).filter_by(is_active=True).all()
    total_messages_created = 0
    for notification in notifications:
        if notification.notification_type == EventType.DAYS_ELAPSED:
            message_was_created = check_days_elapsed(
                notification.experiment_id,
                notification.notification_id,
                notification.notification_value,
                session,
            )
        elif notification.notification_type == EventType.TRIALS_COMPLETED:
            message_was_created = check_trials_completed(
                notification.experiment_id,
                notification.notification_id,
                notification.notification_value,
                session,
            )
        elif notification.notification_type == EventType.PERCENTAGE_BETTER:
            message_was_created = check_percentage_better(
                notification.experiment_id,
                notification.notification_id,
                notification.notification_value,
                session,
            )
        else:
            raise ValueError(
                f"Unknown notification type: {notification.notification_type}"
            )
        total_messages_created += message_was_created

    logger.info(f"{total_messages_created} notifications processed successfully")

    return total_messages_created


if __name__ == "__main__":
    process_notifications()
