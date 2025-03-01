"""debugging obs datetime

Revision ID: 04ce705b4314
Revises: e3e9a32683dc
Create Date: 2025-03-01 21:59:05.358552

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "04ce705b4314"
down_revision: Union[str, None] = "e3e9a32683dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE contextual_observations
        ALTER COLUMN obs_timestamp_utc TYPE TIMESTAMP WITH TIME ZONE
        USING obs_timestamp_utc::timestamp with time zone;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE contextual_observations
        ALTER COLUMN obs_timestamp_utc TYPE VARCHAR
        USING obs_timestamp_utc::varchar;
        """
    )
