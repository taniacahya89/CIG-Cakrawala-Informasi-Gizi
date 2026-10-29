"""Add image_path fields to content models

Revision ID: 089219c44934
Revises: 20261029_content
Create Date: 2026-10-29 17:14:16.846192

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '089219c44934'
down_revision = '20261029_content'
branch_labels = None
depends_on = None


def upgrade():
    # Add image_path column to learning_modules (if not exists)
    with op.batch_alter_table('learning_modules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_path', sa.String(length=350), nullable=True))
        batch_op.drop_constraint(batch_op.f('learning_modules_slug_key'), type_='unique')
        batch_op.create_index(batch_op.f('ix_learning_modules_slug'), ['slug'], unique=True)

    # Add image_path column to quiz_categories (if not exists)
    with op.batch_alter_table('quiz_categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_path', sa.String(length=350), nullable=True))
        batch_op.drop_constraint(batch_op.f('quiz_categories_slug_key'), type_='unique')
        batch_op.create_index(batch_op.f('ix_quiz_categories_slug'), ['slug'], unique=True)

    # Note: recipes.image_path already exists in the database


def downgrade():
    # Remove image_path columns from learning_modules and quiz_categories only
    with op.batch_alter_table('quiz_categories', schema=None) as batch_op:
        batch_op.drop_column('image_path')
        batch_op.drop_index(batch_op.f('ix_quiz_categories_slug'))
        batch_op.create_unique_constraint(batch_op.f('quiz_categories_slug_key'), ['slug'], postgresql_nulls_not_distinct=False)

    with op.batch_alter_table('learning_modules', schema=None) as batch_op:
        batch_op.drop_column('image_path')
        batch_op.drop_index(batch_op.f('ix_learning_modules_slug'))
        batch_op.create_unique_constraint(batch_op.f('learning_modules_slug_key'), ['slug'], postgresql_nulls_not_distinct=False)
    
    # Note: recipes.image_path was already present, not dropped