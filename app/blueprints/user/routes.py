"""User blueprint routes — Dashboard and Profile."""

from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from .forms import ProfileForm, ChangePasswordForm
from . import user_bp


@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    from app.models.content import (LearningProgress, QuizBestScore, RecipeFavorite,
                                    RecipeView, ScanHistory)
    modules_done = LearningProgress.query.filter_by(user_id=current_user.id, status='completed').count()
    from app.models.content import QuizCategory
    score_rows = (db.session.query(QuizBestScore, QuizCategory.title)
                  .join(QuizCategory, QuizBestScore.category_id == QuizCategory.id)
                  .filter(QuizBestScore.user_id == current_user.id).all())
    best_scores = [{'title': title, 'best_correct': score.best_correct, 'total': score.total}
                   for score, title in score_rows]
    favorite_count = RecipeFavorite.query.filter_by(user_id=current_user.id).count()
    view_count = RecipeView.query.filter_by(user_id=current_user.id).count()
    scan_count = ScanHistory.query.filter_by(user_id=current_user.id).count()
    return render_template('user/dashboard.html',modules_done=modules_done,
                           best_scores=best_scores,favorite_count=favorite_count,
                           view_count=view_count,scan_count=scan_count)


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management."""
    form = ProfileForm(obj=current_user)
    password_form = ChangePasswordForm()

    return render_template('user/profile.html', form=form, password_form=password_form)


@user_bp.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    """Update user profile information. Email changes require password verification."""
    form = ProfileForm()

    if form.validate_on_submit():
        new_email = form.email.data.lower().strip()
        # Identity verification for sensitive email change
        if new_email != current_user.email:
            if not form.password_verification.data or not current_user.check_password(form.password_verification.data):
                flash('Verifikasi kata sandi saat ini diperlukan untuk mengubah alamat email.', 'danger')
                return redirect(url_for('user.profile'))

        current_user.full_name = form.full_name.data.strip()
        current_user.email = new_email
        current_user.age_range = form.age_range.data
        current_user.city = form.city.data.strip()

        db.session.commit()
        flash('Profil berhasil diperbarui.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return redirect(url_for('user.profile'))


@user_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password with current password verification."""
    password_form = ChangePasswordForm()

    if password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash('Kata sandi saat ini salah.', 'danger')
            return redirect(url_for('user.profile'))

        current_user.set_password(password_form.new_password.data)
        db.session.commit()
        flash('Kata sandi berhasil diubah.', 'success')
    else:
        for field, errors in password_form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return redirect(url_for('user.profile'))


@user_bp.get('/meal-tracker')
@login_required
def meal_tracker():
    from app.models.content import ScanHistory
    scans = ScanHistory.query.filter_by(user_id=current_user.id).order_by(ScanHistory.scanned_at.desc()).all()
    return render_template('user/meal_tracker.html', scans=scans)
