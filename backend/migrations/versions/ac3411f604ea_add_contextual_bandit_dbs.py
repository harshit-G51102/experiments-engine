"""add contextual bandit dbs

Revision ID: ac3411f604ea
Revises: af0fdaa1e60d
Create Date: 2025-01-16 19:47:28.366995

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ac3411f604ea"
down_revision: Union[str, None] = "af0fdaa1e60d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "contextual_mabs",
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("experiment_id"),
    )
    op.create_table(
        "contexts",
        sa.Column("context_id", sa.Integer(), nullable=False),
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("values", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["contextual_mabs.experiment_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("context_id"),
    )
    op.create_table(
        "contextual_arms",
        sa.Column("arm_id", sa.Integer(), nullable=False),
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("alpha_prior", sa.Integer(), nullable=False),
        sa.Column("beta_prior", sa.Integer(), nullable=False),
        sa.Column("successes", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("failures", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["contextual_mabs.experiment_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("arm_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("contextual_arms")
    op.drop_table("contexts")
    op.drop_table("contextual_mabs")
    # ### end Alembic commands ###
