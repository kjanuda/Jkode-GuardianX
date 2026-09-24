"""add telemetry table

Revision ID: febd43e70f23
Revises: 224c58a47e3f
Create Date: 2026-09-22 21:11:05.318596

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "febd43e70f23"
down_revision: Union[str, Sequence[str], None] = "224c58a47e3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass