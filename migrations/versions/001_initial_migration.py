"""Initial database migration

Revision ID: 001
Revises:
Create Date: 2025-04-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('username', sa.String(), unique=True, index=True),
        sa.Column('email', sa.String(), unique=True, index=True),
        sa.Column('password', sa.String()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )

    # Create PDFs table
    op.create_table(
        'pdfs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id')),
        sa.Column('title', sa.String()),
        sa.Column('filename', sa.String()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('file_path', sa.String())
    )

    # Create PDF chunks table
    op.create_table(
        'pdf_chunks',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('pdf_id', sa.String(), sa.ForeignKey('pdfs.id')),
        sa.Column('content', sa.Text()),
        sa.Column('page_number', sa.Integer()),
        sa.Column('embedding_file', sa.String(), nullable=True)
    )

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id')),
        sa.Column('pdf_id', sa.String(), sa.ForeignKey('pdfs.id')),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('conversation_id', sa.String(), sa.ForeignKey('conversations.id')),
        sa.Column('is_user', sa.Boolean(), default=True),
        sa.Column('content', sa.Text()),
        sa.Column('timestamp', sa.DateTime(), default=sa.func.now())
    )

    # Create quizzes table
    op.create_table(
        'quizzes',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('pdf_id', sa.String(), sa.ForeignKey('pdfs.id')),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id')),
        sa.Column('title', sa.String()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('questions', sa.JSON())
    )


def downgrade():
    op.drop_table('quizzes')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('pdf_chunks')
    op.drop_table('pdfs')
    op.drop_table('users')