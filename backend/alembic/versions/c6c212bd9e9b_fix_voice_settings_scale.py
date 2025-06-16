"""fix_voice_settings_scale

Revision ID: c6c212bd9e9b
Revises: fdca45201205
Create Date: 2025-01-10 14:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c6c212bd9e9b'
down_revision: Union[str, None] = 'fdca45201205'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix voice settings scale from percentage (0-100) to decimal (0.0-1.0)"""
    conn = op.get_bind()
    try:
        # Update any existing persona_settings records that have wrong scale
        conn.execute(text("""
            UPDATE persona_settings 
            SET voice_settings = jsonb_set(
                jsonb_set(
                    jsonb_set(
                        voice_settings,
                        '{stability}',
                        to_jsonb((voice_settings->>'stability')::numeric / 100)
                    ),
                    '{similarity_boost}',
                    to_jsonb((voice_settings->>'similarity_boost')::numeric / 100)
                ),
                '{style}',
                to_jsonb((voice_settings->>'style')::numeric / 100)
            )
            WHERE voice_settings IS NOT NULL
            AND (voice_settings->>'stability')::numeric > 1.0
        """))
        
        print("Fixed voice settings scale for existing records")
    except Exception as e:
        print(f"Voice settings migration skipped (no existing records or error): {e}")


def downgrade() -> None:
    """Revert voice settings scale from decimal (0.0-1.0) to percentage (0-100)"""
    conn = op.get_bind()
    try:
        # Revert the changes - multiply by 100 to get back to percentage
        conn.execute(text("""
            UPDATE persona_settings 
            SET voice_settings = jsonb_set(
                jsonb_set(
                    jsonb_set(
                        voice_settings,
                        '{stability}',
                        to_jsonb((voice_settings->>'stability')::numeric * 100)
                    ),
                    '{similarity_boost}',
                    to_jsonb((voice_settings->>'similarity_boost')::numeric * 100)
                ),
                '{style}',
                to_jsonb((voice_settings->>'style')::numeric * 100)
            )
            WHERE voice_settings IS NOT NULL
            AND (voice_settings->>'stability')::numeric <= 1.0
        """))
    except Exception as e:
        print(f"Voice settings downgrade skipped: {e}")
