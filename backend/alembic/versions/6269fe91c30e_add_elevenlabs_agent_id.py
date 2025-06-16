"""add_elevenlabs_agent_id

Revision ID: 6269fe91c30e
Revises: c6c212bd9e9b
Create Date: 2025-06-13 16:52:26.288278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6269fe91c30e'
down_revision: Union[str, None] = 'c6c212bd9e9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add elevenlabs_agent_id column to personas table
    op.add_column('personas', sa.Column('elevenlabs_agent_id', sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove elevenlabs_agent_id column from personas table
    op.drop_column('personas', 'elevenlabs_agent_id')
