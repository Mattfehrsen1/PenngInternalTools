"""add_conversation_and_message_tables

Revision ID: 195ec1d9edbd
Revises: 2d581c9e9328
Create Date: 2025-06-11 16:55:53.356482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '195ec1d9edbd'
down_revision: Union[str, None] = '2d581c9e9328'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('persona_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create messages table (using string for role to avoid enum conflicts)
    op.create_table('messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('thread_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['thread_id'], ['conversations.id'], ondelete='CASCADE')
    )
    
    # Create indexes for performance
    # Conversations indexes
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_persona_id', 'conversations', ['persona_id'])
    op.create_index('ix_conversations_user_updated', 'conversations', ['user_id', 'updated_at'])
    op.create_index('ix_conversations_last_message', 'conversations', ['last_message_at'])
    
    # Messages indexes
    op.create_index('ix_messages_thread_id', 'messages', ['thread_id'])
    op.create_index('ix_messages_thread_created', 'messages', ['thread_id', 'created_at'])
    op.create_index('ix_messages_role', 'messages', ['role'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_role', table_name='messages')
    op.drop_index('ix_messages_thread_created', table_name='messages')
    op.drop_index('ix_messages_thread_id', table_name='messages')
    
    op.drop_index('ix_conversations_last_message', table_name='conversations')
    op.drop_index('ix_conversations_user_updated', table_name='conversations')
    op.drop_index('ix_conversations_persona_id', table_name='conversations')
    op.drop_index('ix_conversations_user_id', table_name='conversations')
    
    # Drop tables
    op.drop_table('messages')
    op.drop_table('conversations')
