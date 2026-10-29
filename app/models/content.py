"""CIG core content and activity models (additive, no changes to auth tables)."""
from datetime import datetime, timezone
from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class LearningModule(db.Model):
    __tablename__ = 'learning_modules'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    title = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(100), nullable=False, default='Edukasi Gizi')
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(350))
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_published = db.Column(db.Boolean, nullable=False, default=False)


class LearningProgress(db.Model):
    __tablename__ = 'learning_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(24), nullable=False, default='in_progress')
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    completed_at = db.Column(db.DateTime(timezone=True))
    __table_args__ = (db.UniqueConstraint('user_id','module_id',name='uq_progress_user_module'),)


class QuizCategory(db.Model):
    __tablename__ = 'quiz_categories'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    image_path = db.Column(db.String(350))
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    questions = db.relationship('QuizQuestion', backref='category', lazy='select', cascade='all, delete-orphan', order_by='QuizQuestion.sort_order')


class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('quiz_categories.id', ondelete='CASCADE'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


class QuizBestScore(db.Model):
    __tablename__ = 'quiz_best_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('quiz_categories.id', ondelete='CASCADE'), nullable=False)
    best_correct = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=10)
    achieved_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    __table_args__ = (db.UniqueConstraint('user_id','category_id',name='uq_best_user_category'),)


class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    title = db.Column(db.String(250), nullable=False)
    category = db.Column(db.String(120), nullable=False)
    ingredients = db.Column(db.Text, nullable=False, default='')
    steps = db.Column(db.Text, nullable=False, default='')
    tips = db.Column(db.Text, nullable=False, default='')
    image_path = db.Column(db.String(350))
    prep_minutes = db.Column(db.Integer)
    cook_minutes = db.Column(db.Integer)
    servings = db.Column(db.Integer)
    is_published = db.Column(db.Boolean, nullable=False, default=False)


class RecipeFavorite(db.Model):
    __tablename__ = 'recipe_favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    __table_args__ = (db.UniqueConstraint('user_id','recipe_id',name='uq_favorite_user_recipe'),)


class RecipeView(db.Model):
    __tablename__ = 'recipe_views'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    viewed_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class ScanHistory(db.Model):
    """Reserved for real inference service; never populate with fabricated model output."""
    __tablename__ = 'scan_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    image_path = db.Column(db.String(350), nullable=False)
    overlay_path = db.Column(db.String(350))
    area_percentages = db.Column(db.JSON, nullable=False)
    scanned_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
