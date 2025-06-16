"""simplify_ingestion_jobs_remove_progress_add_error

Revision ID: 1cbbfec48c37
Revises: persona_specific_prompts
Create Date: 2025-06-13 09:58:24.399216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cbbfec48c37'
down_revision: Union[str, None] = 'persona_specific_prompts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove progress column from ingestion_jobs (if it exists)
    try:
        op.drop_column('ingestion_jobs', 'progress')
    except Exception:
        # Column might not exist, that's okay
        pass
    
    # Add error_message column
    op.add_column('ingestion_jobs', 
        sa.Column('error_message', sa.Text(), nullable=True)
    )
    
    # Note: We're leaving existing status values as-is for now
    # The application code will handle both old (QUEUED, COMPLETED) and new (queued, ready) formats
    
    # Add index for efficient status queries
    op.create_index('idx_ingestion_persona_status', 
        'ingestion_jobs', ['persona_id', 'status'])


def downgrade() -> None:
    # Reverse operations for rollback
    op.drop_index('idx_ingestion_persona_status', table_name='ingestion_jobs')
    
    # Add back progress column
    op.add_column('ingestion_jobs',
        sa.Column('progress', sa.Integer(), nullable=True, default=0)
    )
    
    # Remove error_message column
    op.drop_column('ingestion_jobs', 'error_message')
    
    # Note: Status values remain as-is since we didn't change them in upgrade
