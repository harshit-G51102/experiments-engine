from enum import Enum

# --- Outcome ---


class Outcome(str, Enum):
    """
    Enum for the outcome of a trial.
    """

    SUCCESS = "success"
    FAILURE = "failure"
