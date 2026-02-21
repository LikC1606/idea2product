from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '202311010001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Apply the migration."""
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )

def downgrade():
    """Revert the migration."""
    op.drop_table('notes')
