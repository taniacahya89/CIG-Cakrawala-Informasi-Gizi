"""Add CIG educational content, user progress, quiz scores, recipe favorites and scan history.

Revision ID: 20261029_content
Revises: 045d86967952
"""
from alembic import op
import sqlalchemy as sa

revision = '20261029_content'
down_revision = '045d86967952'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('learning_modules',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('slug',sa.String(180),nullable=False,unique=True),
        sa.Column('title',sa.String(300),nullable=False),
        sa.Column('category',sa.String(100),nullable=False),
        sa.Column('content',sa.Text(),nullable=False),
        sa.Column('sort_order',sa.Integer(),nullable=False),
        sa.Column('is_published',sa.Boolean(),nullable=False))
    op.create_table('learning_progress',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('module_id',sa.Integer(),sa.ForeignKey('learning_modules.id',ondelete='CASCADE'),nullable=False),
        sa.Column('status',sa.String(24),nullable=False),
        sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('completed_at',sa.DateTime(timezone=True)),
        sa.UniqueConstraint('user_id','module_id',name='uq_progress_user_module'))
    op.create_table('quiz_categories',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('slug',sa.String(180),nullable=False,unique=True),
        sa.Column('title',sa.String(300),nullable=False),
        sa.Column('description',sa.Text()),
        sa.Column('is_published',sa.Boolean(),nullable=False))
    op.create_table('quiz_questions',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('category_id',sa.Integer(),sa.ForeignKey('quiz_categories.id',ondelete='CASCADE'),nullable=False),
        sa.Column('question',sa.Text(),nullable=False),
        sa.Column('options',sa.JSON(),nullable=False),
        sa.Column('correct',sa.String(1),nullable=False),
        sa.Column('explanation',sa.Text(),nullable=False),
        sa.Column('sort_order',sa.Integer(),nullable=False))
    op.create_table('quiz_best_scores',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('category_id',sa.Integer(),sa.ForeignKey('quiz_categories.id',ondelete='CASCADE'),nullable=False),
        sa.Column('best_correct',sa.Integer(),nullable=False),
        sa.Column('total',sa.Integer(),nullable=False),
        sa.Column('achieved_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('user_id','category_id',name='uq_best_user_category'))
    op.create_table('recipes',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('slug',sa.String(180),nullable=False,unique=True),
        sa.Column('title',sa.String(250),nullable=False),
        sa.Column('category',sa.String(120),nullable=False),
        sa.Column('ingredients',sa.Text(),nullable=False),
        sa.Column('steps',sa.Text(),nullable=False),
        sa.Column('tips',sa.Text(),nullable=False),
        sa.Column('image_path',sa.String(350)),
        sa.Column('prep_minutes',sa.Integer()),
        sa.Column('cook_minutes',sa.Integer()),
        sa.Column('servings',sa.Integer()),
        sa.Column('is_published',sa.Boolean(),nullable=False))
    op.create_table('recipe_favorites',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('recipe_id',sa.Integer(),sa.ForeignKey('recipes.id',ondelete='CASCADE'),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('user_id','recipe_id',name='uq_favorite_user_recipe'))
    op.create_table('recipe_views',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('recipe_id',sa.Integer(),sa.ForeignKey('recipes.id',ondelete='CASCADE'),nullable=False),
        sa.Column('viewed_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('scan_history',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('image_path',sa.String(350),nullable=False),
        sa.Column('overlay_path',sa.String(350)),
        sa.Column('area_percentages',sa.JSON(),nullable=False),
        sa.Column('scanned_at',sa.DateTime(timezone=True),nullable=False))


def downgrade():
    for name in ('scan_history','recipe_views','recipe_favorites','recipes','quiz_best_scores','quiz_questions','quiz_categories','learning_progress','learning_modules'):
        op.drop_table(name)
