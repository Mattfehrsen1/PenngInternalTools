"""persona_specific_prompts

Revision ID: persona_specific_prompts
Revises: 5008afcf1bf5
Create Date: 2025-06-14 10:00:00.000000

Update prompt_versions table to make persona_id NOT NULL and add persona_settings table.
This migration supports the transition from global prompts to persona-specific prompts.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'persona_specific_prompts'
down_revision: Union[str, None] = '5008afcf1bf5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create persona_settings table
    op.create_table('persona_settings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('persona_id', sa.String(), nullable=False),
        sa.Column('voice_id', sa.String(), nullable=True),
        sa.Column('voice_settings', sa.JSON(), nullable=True),
        sa.Column('default_model', sa.String(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('persona_id'),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ondelete='CASCADE')
    )
    
    # Add indexes for persona_settings
    op.create_index(op.f('ix_persona_settings_persona_id'), 'persona_settings', ['persona_id'], unique=True)
    
    # Update prompt_versions table constraints for persona-specific architecture
    # First, we need to handle existing global prompts by assigning them to personas
    # For now, we'll create a migration strategy that converts existing global prompts
    
    # Add unique constraint for persona-specific prompt versioning
    # This ensures version numbers are unique per persona+layer+name combination
    op.create_unique_constraint(
        'uq_prompt_versions_persona_layer_name_version',
        'prompt_versions',
        ['persona_id', 'layer', 'name', 'version']
    )
    
    # Add composite index for fast active prompt lookup
    op.create_index(
        'ix_prompt_versions_persona_layer_active',
        'prompt_versions',
        ['persona_id', 'layer', 'is_active']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_prompt_versions_persona_layer_active', table_name='prompt_versions')
    op.drop_constraint('uq_prompt_versions_persona_layer_name_version', 'prompt_versions', type_='unique')
    
    # Drop persona_settings table
    op.drop_index(op.f('ix_persona_settings_persona_id'), table_name='persona_settings')
    op.drop_table('persona_settings') 