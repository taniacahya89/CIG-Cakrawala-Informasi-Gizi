"""Admin blueprint routes — Dashboard and Invitations."""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, login_user
from app.extensions import db
from app.models.user import User, AdminInvitation
from app.utils.decorators import admin_required
from app.utils.tokens import (
    create_admin_invitation,
    verify_admin_invitation,
    accept_admin_invitation,
)
from app.utils.email import send_admin_invitation_email
from .forms import AdminInviteForm, AcceptInviteForm
from . import admin_bp


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard."""
    # User counts
    user_count = User.query.filter_by(role='user').count()
    admin_count = User.query.filter_by(role='admin').count()
    pending_invites = AdminInvitation.query.filter_by(accepted=False).count()
    
    # Content counts for CMS inventory
    from app.models.content import LearningModule, QuizCategory, QuizQuestion, Recipe
    
    module_count = LearningModule.query.count()
    module_published = LearningModule.query.filter_by(is_published=True).count()
    module_draft = LearningModule.query.filter_by(is_published=False).count()
    
    quiz_category_count = QuizCategory.query.count()
    quiz_published = QuizCategory.query.filter_by(is_published=True).count()
    quiz_draft = QuizCategory.query.filter_by(is_published=False).count()
    
    question_count = QuizQuestion.query.count()
    
    recipe_count = Recipe.query.count()
    recipe_published = Recipe.query.filter_by(is_published=True).count()
    recipe_draft = Recipe.query.filter_by(is_published=False).count()

    return render_template('admin/dashboard.html',
                           user_count=user_count,
                           admin_count=admin_count,
                           pending_invites=pending_invites,
                           module_count=module_count,
                           module_published=module_published,
                           module_draft=module_draft,
                           quiz_category_count=quiz_category_count,
                           quiz_published=quiz_published,
                           quiz_draft=quiz_draft,
                           question_count=question_count,
                           recipe_count=recipe_count,
                           recipe_published=recipe_published,
                           recipe_draft=recipe_draft)


@admin_bp.route('/invite', methods=['GET', 'POST'])
@login_required
@admin_required
def invite():
    """Send admin invitation."""
    form = AdminInviteForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        # Check if user already exists as admin
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.is_admin:
            flash('Pengguna ini sudah menjadi administrator.', 'warning')
            return redirect(url_for('admin.invite'))

        # Check for pending invitation
        pending = AdminInvitation.query.filter_by(email=email, accepted=False).first()
        if pending and pending.is_valid:
            flash('Undangan untuk email ini masih aktif.', 'warning')
            return redirect(url_for('admin.invite'))

        token = create_admin_invitation(email, current_user)
        base_url = request.host_url.rstrip('/')
        email_sent = send_admin_invitation_email(email, token, current_user, base_url)

        if email_sent:
            flash(f'Undangan administrator telah dikirim ke {email}.', 'success')
        else:
            flash('Email undangan belum dapat dikirim. Periksa konfigurasi server email lokal.', 'warning')

        return redirect(url_for('admin.invite'))

    # List all invitations
    invitations = AdminInvitation.query.order_by(AdminInvitation.created_at.desc()).all()
    return render_template('admin/invite.html', form=form, invitations=invitations)


@admin_bp.route('/accept-invite/<token>', methods=['GET', 'POST'])
def accept_invite(token):
    """Accept an admin invitation."""
    # Redirect if already logged in as admin
    if current_user.is_authenticated and current_user.is_admin:
        flash('Anda sudah masuk sebagai administrator.', 'info')
        return redirect(url_for('admin.dashboard'))

    invitation = verify_admin_invitation(token)
    if invitation is None:
        flash('Tautan undangan tidak valid atau sudah kedaluwarsa.', 'danger')
        return redirect(url_for('main.index'))

    # Check if user already exists
    existing_user = User.query.filter_by(email=invitation.email).first()

    form = AcceptInviteForm()

    if form.validate_on_submit():
        if existing_user:
            # Upgrade existing user to admin
            existing_user.role = 'admin'
            accept_admin_invitation(token)
            db.session.commit()
            login_user(existing_user)
            flash('Selamat! Akun Anda telah ditingkatkan menjadi administrator.', 'success')
        else:
            # Create new admin user
            user = User(
                full_name=form.full_name.data.strip(),
                email=invitation.email,
                age_range=form.age_range.data,
                city=form.city.data.strip(),
                role='admin',
            )
            user.set_password(form.password.data)
            db.session.add(user)
            accept_admin_invitation(token)
            db.session.commit()
            login_user(user)
            flash('Akun administrator berhasil dibuat!', 'success')

        return redirect(url_for('admin.dashboard'))

    return render_template('admin/accept_invite.html',
                           form=form,
                           token=token,
                           invitation=invitation,
                           existing_user=existing_user)


@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """List all users."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)
