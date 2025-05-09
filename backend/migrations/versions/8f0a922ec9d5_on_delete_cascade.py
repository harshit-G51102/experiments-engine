"""on delete cascade

Revision ID: 8f0a922ec9d5
Revises: 6f4560d8fea2
Create Date: 2025-03-04 21:52:28.667497

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f0a922ec9d5"
down_revision: Union[str, None] = "6f4560d8fea2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_mabs_experiments_base", "mabs", type_="foreignkey")
    op.create_foreign_key(
        None,
        "mabs",
        "experiments_base",
        ["experiment_id"],
        ["experiment_id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_mabs_experiments_base", "mabs", type_="foreignkey")
    op.create_foreign_key(
        "fk_mabs_experiments_base",
        "mabs",
        "experiments_base",
        ["experiment_id"],
        ["experiment_id"],
    )
    # ### end Alembic commands ###
