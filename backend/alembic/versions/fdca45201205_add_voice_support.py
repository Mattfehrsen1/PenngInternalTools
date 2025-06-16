"""add_voice_support

Revision ID: fdca45201205
Revises: 1cbbfec48c37
Create Date: 2025-06-13 13:00:29.600684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'fdca45201205'
down_revision: Union[str, None] = '1cbbfec48c37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if persona_settings table exists, create if not
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'persona_settings' not in inspector.get_table_names():
        # Create persona_settings table with voice support
        op.create_table('persona_settings',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('persona_id', sa.String(), nullable=False),
            sa.Column('voice_id', sa.String(), nullable=True),
            sa.Column('voice_name', sa.String(), nullable=True),
            sa.Column('voice_settings', sa.JSON(), nullable=True),
            sa.Column('default_model', sa.String(), nullable=True),
            sa.Column('temperature', sa.Integer(), nullable=True),
            sa.Column('max_tokens', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('persona_id')
        )
        
        # Create indexes for performance
        op.create_index('ix_persona_settings_persona_id', 'persona_settings', ['persona_id'])
    
    # Set default voice for existing personas (if any)
    # Only if personas table exists and persona_settings was just created or is empty
    try:
        result = conn.execute(text("SELECT COUNT(*) FROM persona_settings")).scalar()
        if result == 0:  # Table is empty, safe to add defaults
            conn.execute(text("""
                INSERT INTO persona_settings (id, persona_id, voice_id, voice_name, voice_settings, created_at, updated_at)
                SELECT 
                    gen_random_uuid()::text as id,
                    p.id as persona_id,
                    'EXAVITQu4vr4xnSDxMaL' as voice_id,
                    'Sarah' as voice_name,
                    '{"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": true}' as voice_settings,
                    now() as created_at,
                    now() as updated_at
                FROM personas p
                WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'personas')
                AND NOT EXISTS (
                    SELECT 1 FROM persona_settings ps WHERE ps.persona_id = p.id
                )
            """))
    except Exception:
        # If personas table doesn't exist yet or other issues, just skip the default setup
        pass


def downgrade() -> None:
    # Check if table exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'persona_settings' in inspector.get_table_names():
        # Drop indexes first (if they exist)
        try:
            op.drop_index('ix_persona_settings_persona_id', table_name='persona_settings')
        except Exception:
            pass
        
        # Drop the table
        op.drop_table('persona_settings')
