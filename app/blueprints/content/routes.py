"""Public educational content, real quiz scoring and authenticated activity."""
from datetime import datetime, timezone
from flask import render_template, request, abort, redirect, url_for, session, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.content import (LearningModule, LearningProgress, QuizCategory,
                                QuizQuestion, QuizBestScore, Recipe, RecipeFavorite, RecipeView)
from . import content_bp


def _safe_item(model, slug):
    item = model.query.filter_by(slug=slug, is_published=True).first()
    if item is None:
        abort(404)
    return item


@content_bp.get('/modul-edukasi')
def modules():
    items = LearningModule.query.filter_by(is_published=True).order_by(LearningModule.sort_order, LearningModule.id).all()
    progress = {}
    if current_user.is_authenticated:
        progress = {row.module_id: row.status for row in LearningProgress.query.filter_by(user_id=current_user.id)}
    return render_template('content/modules.html', items=items, progress=progress)


@content_bp.get('/modul-edukasi/<slug>')
def module_detail(slug):
    item = _safe_item(LearningModule, slug)
    progress = None
    if current_user.is_authenticated:
        progress = LearningProgress.query.filter_by(user_id=current_user.id, module_id=item.id).first()
        if not progress:
            progress = LearningProgress(user_id=current_user.id, module_id=item.id, status='in_progress')
            db.session.add(progress)
            db.session.commit()
    return render_template('content/module_detail.html', item=item, progress=progress)


@content_bp.post('/modul-edukasi/<slug>/complete')
@login_required
def module_complete(slug):
    item = _safe_item(LearningModule, slug)
    row = LearningProgress.query.filter_by(user_id=current_user.id, module_id=item.id).first()
    if row is None:
        row = LearningProgress(user_id=current_user.id, module_id=item.id)
        db.session.add(row)
    row.status = 'completed'
    if row.completed_at is None:
        row.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return redirect(url_for('content.module_detail', slug=slug))


@content_bp.get('/kuis')
def quiz_list():
    cats = QuizCategory.query.filter_by(is_published=True).order_by(QuizCategory.id).all()
    scores = {}
    if current_user.is_authenticated:
        scores = {s.category_id:s for s in QuizBestScore.query.filter_by(user_id=current_user.id)}
    return render_template('content/quizzes.html', cats=cats, scores=scores)


def _quiz_session_key(cat):
    return f'cig_quiz_{cat.id}'


def _start_quiz(cat):
    ids = [q.id for q in cat.questions]
    if not ids:
        abort(404)
    state = {'ids':ids,'index':0,'correct':0,'feedback':None,'completed':False}
    session[_quiz_session_key(cat)] = state
    session.modified = True
    return state


def _get_or_start(cat):
    state = session.get(_quiz_session_key(cat))
    if not state or state.get('ids') != [q.id for q in cat.questions]:
        return _start_quiz(cat)
    return state


@content_bp.get('/kuis/<slug>')
def quiz_play(slug):
    cat = _safe_item(QuizCategory, slug)
    state = _get_or_start(cat)
    if state.get('completed'):
        return render_template('content/quiz_result.html', cat=cat, state=state)
    index = state['index']
    if not 0 <= index < len(state['ids']):
        abort(400)
    question = db.session.get(QuizQuestion, state['ids'][index])
    return render_template('content/quiz_play.html', cat=cat, question=question,
                           state=state, number=index+1, total=len(state['ids']))


@content_bp.post('/kuis/<slug>/answer')
def quiz_answer(slug):
    cat = _safe_item(QuizCategory, slug)
    state = _get_or_start(cat)
    if state['completed'] or state['feedback'] is not None:
        return redirect(url_for('content.quiz_play', slug=slug))
    selection = request.form.get('answer', '')
    if selection not in ('A','B','C','D'):
        flash('Pilih salah satu jawaban.', 'warning')
        return redirect(url_for('content.quiz_play', slug=slug))
    q = db.session.get(QuizQuestion, state['ids'][state['index']])
    is_correct = selection == q.correct
    if is_correct:
        state['correct'] += 1
    state['feedback'] = {'selected':selection, 'correct':q.correct,
                         'correct_text':q.options[q.correct], 'is_correct':is_correct,
                         'explanation':q.explanation}
    session[_quiz_session_key(cat)] = state
    session.modified = True
    return redirect(url_for('content.quiz_play', slug=slug))


@content_bp.post('/kuis/<slug>/next')
def quiz_next(slug):
    cat = _safe_item(QuizCategory, slug)
    state = _get_or_start(cat)
    if state['completed'] or state['feedback'] is None:
        return redirect(url_for('content.quiz_play', slug=slug))
    state['feedback'] = None
    state['index'] += 1
    if state['index'] >= len(state['ids']):
        state['completed'] = True
        if current_user.is_authenticated:
            row = QuizBestScore.query.filter_by(user_id=current_user.id, category_id=cat.id).first()
            if row is None:
                row = QuizBestScore(user_id=current_user.id, category_id=cat.id,
                                    best_correct=state['correct'], total=len(state['ids']))
                db.session.add(row)
            elif state['correct'] > row.best_correct:
                row.best_correct = state['correct']
                row.total = len(state['ids'])
                row.achieved_at = datetime.now(timezone.utc)
            db.session.commit()
    session[_quiz_session_key(cat)] = state
    session.modified = True
    return redirect(url_for('content.quiz_play', slug=slug))


@content_bp.post('/kuis/<slug>/restart')
def quiz_restart(slug):
    cat = _safe_item(QuizCategory, slug)
    _start_quiz(cat)
    return redirect(url_for('content.quiz_play', slug=slug))


@content_bp.get('/resep')
def recipes():
    term = request.args.get('q','').strip()[:100]
    category = request.args.get('category','').strip()[:120]
    qry = Recipe.query.filter_by(is_published=True)
    if term:
        qry = qry.filter(Recipe.title.ilike(f'%{term}%'))
    if category:
        qry = qry.filter_by(category=category)
    items = qry.order_by(Recipe.title).all()
    categories = [row[0] for row in db.session.query(Recipe.category).filter_by(is_published=True).distinct().order_by(Recipe.category).all()]
    favorite_ids = set()
    if current_user.is_authenticated:
        favorite_ids = {r.recipe_id for r in RecipeFavorite.query.filter_by(user_id=current_user.id)}
    return render_template('content/recipes.html', items=items, categories=categories,
                           query=term, category=category, favorite_ids=favorite_ids)


@content_bp.get('/resep/<slug>')
def recipe_detail(slug):
    item = _safe_item(Recipe, slug)
    fav = False
    if current_user.is_authenticated:
        db.session.add(RecipeView(user_id=current_user.id, recipe_id=item.id))
        db.session.commit()
        fav = RecipeFavorite.query.filter_by(user_id=current_user.id, recipe_id=item.id).first() is not None
    return render_template('content/recipe_detail.html', item=item, favorite=fav)


@content_bp.post('/resep/<slug>/favorite')
@login_required
def recipe_favorite(slug):
    item = _safe_item(Recipe, slug)
    fav = RecipeFavorite.query.filter_by(user_id=current_user.id, recipe_id=item.id).first()
    if fav:
        db.session.delete(fav)
        flash('Resep dihapus dari favorit.', 'info')
    else:
        db.session.add(RecipeFavorite(user_id=current_user.id, recipe_id=item.id))
        flash('Resep ditambahkan ke favorit.', 'success')
    db.session.commit()
    return redirect(url_for('content.recipe_detail', slug=slug))


@content_bp.get('/user/resep-favorit')
@login_required
def recipe_favorites():
    rows = (db.session.query(Recipe).join(RecipeFavorite, RecipeFavorite.recipe_id == Recipe.id)
            .filter(RecipeFavorite.user_id == current_user.id, Recipe.is_published.is_(True))
            .order_by(Recipe.title).all())
    return render_template('content/recipes.html', items=rows, categories=[], query='',
                           category='', favorite_ids={r.id for r in rows}, only_favorites=True)
