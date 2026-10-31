"""Minimal protected content management interface for initial CIG deployment."""
import re
import unicodedata
from flask import render_template, request, abort, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.utils.decorators import admin_required
from app.models.content import LearningModule, QuizCategory, QuizQuestion, Recipe
from . import admin_bp

KINDS = {'module':LearningModule,'quiz':QuizCategory,'question':QuizQuestion,'recipe':Recipe}


def _slug(name):
    ascii_name=unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode('ascii').lower()
    return re.sub(r'-+','-',re.sub('[^a-z0-9]+','-',ascii_name)).strip('-')[:170]


@admin_bp.get('/content')
@login_required
@admin_required
def content_index():
    return render_template('admin/content_index.html',
        modules=LearningModule.query.order_by(LearningModule.sort_order).all(),
        quizzes=QuizCategory.query.order_by(QuizCategory.id).all(),
        questions=QuizQuestion.query.order_by(QuizQuestion.category_id, QuizQuestion.sort_order).all(),
        recipes=Recipe.query.order_by(Recipe.title).all())


@admin_bp.route('/content/<kind>/new',methods=['GET','POST'])
@admin_bp.route('/content/<kind>/<int:record_id>/edit',methods=['GET','POST'])
@login_required
@admin_required
def content_edit(kind,record_id=None):
    if kind not in KINDS:
        abort(404)
    model=KINDS[kind]
    row=db.session.get(model,record_id) if record_id else None
    if record_id and row is None:
        abort(404)
    cats=QuizCategory.query.order_by(QuizCategory.id).all()
    if request.method=='POST':
        title=request.form.get('title','').strip()
        content=request.form.get('content','').strip()
        is_published=request.form.get('is_published')=='1'
        if not title:
            flash('Judul atau pertanyaan wajib diisi.','danger')
            return redirect(request.url)
        if row is None:
            row=model()
            db.session.add(row)
        try:
            if kind=='module':
                row.title=title[:300]
                row.slug=row.slug or _slug(title)
                row.category=request.form.get('category','Edukasi Gizi').strip()[:100] or 'Edukasi Gizi'
                row.content=content
                row.sort_order=int(request.form.get('sort_order',0))
                row.is_published=is_published
            elif kind=='recipe':
                row.title=title[:250]
                row.slug=row.slug or _slug(title)
                row.category=request.form.get('category','').strip()[:120]
                row.ingredients=request.form.get('ingredients','').strip()
                row.steps=request.form.get('steps','').strip()
                row.tips=request.form.get('tips','').strip()
                row.is_published=is_published
                if not row.category:
                    raise ValueError('Kategori resep wajib diisi.')
            elif kind=='quiz':
                row.title=title[:300]
                row.slug=row.slug or _slug(title)
                row.description=content
                row.is_published=is_published
            elif kind=='question':
                row.question=title
                catid=int(request.form.get('category_id','0'))
                if not db.session.get(QuizCategory,catid):
                    raise ValueError('Pilih kategori kuis yang valid.')
                row.category_id=catid
                row.options={letter:request.form.get('option_'+letter,'').strip() for letter in 'ABCD'}
                if not all(row.options.values()):
                    raise ValueError('Empat opsi jawaban wajib diisi.')
                row.correct=request.form.get('correct','')
                if row.correct not in 'ABCD' or len(row.correct)!=1:
                    raise ValueError('Kunci jawaban harus A, B, C, atau D.')
                row.explanation=request.form.get('explanation','').strip()
                if not row.explanation:
                    raise ValueError('Pembahasan wajib diisi.')
                row.sort_order=int(request.form.get('sort_order','0'))
            # Creating a record can include its cover photo in the same request.
            # Save the media first, then commit the database; remove it on failure.
            created_image_path = None
            uploaded = request.files.get('image') if kind in ('module', 'quiz', 'recipe') else None
            if uploaded and uploaded.filename:
                from app.utils.image_upload import process_and_save_image
                success, result, _ = process_and_save_image(uploaded, kind)
                if not success:
                    raise ValueError(result)
                created_image_path = result
                # Record the path only after actual decoding/optimization succeeded.
                row.image_path = created_image_path
            db.session.commit()
        except (ValueError,TypeError) as exc:
            if locals().get('created_image_path'):
                from app.utils.image_upload import delete_image_file
                delete_image_file(created_image_path)
            db.session.rollback()
            flash(str(exc),'danger')
            return redirect(request.url)
        except Exception:
            if locals().get('created_image_path'):
                from app.utils.image_upload import delete_image_file
                delete_image_file(created_image_path)
            db.session.rollback()
            flash('Penyimpanan gagal. Periksa kemungkinan judul atau slug duplikat.','danger')
            return redirect(request.url)
        flash('Konten berhasil disimpan.','success')
        return redirect(url_for('admin.content_index'))
    return render_template('admin/content_edit.html',kind=kind,record=row,categories=cats)


@admin_bp.post('/content/<kind>/<int:record_id>/archive')
@login_required
@admin_required
def content_archive(kind,record_id):
    if kind not in ('module','quiz','recipe'):
        abort(404)
    row=db.session.get(KINDS[kind],record_id)
    if row is None:
        abort(404)
    row.is_published=False
    db.session.commit()
    flash('Konten diarsipkan.','success')
    return redirect(url_for('admin.content_index'))


@admin_bp.post('/content/<kind>/<int:record_id>/upload-image')
@login_required
@admin_required
def content_upload_image(kind, record_id):
    """Replace existing cover safely; do not delete old file before DB commit."""
    if kind not in ('module', 'quiz', 'recipe'):
        abort(404)
    row = db.session.get(KINDS[kind], record_id)
    if row is None:
        abort(404)
    file = request.files.get('image')
    if file is None or not file.filename:
        flash('Pilih gambar terlebih dahulu.', 'danger')
        return redirect(url_for('admin.content_edit', kind=kind, record_id=record_id))

    from app.utils.image_upload import process_and_save_image, delete_image_file
    success, new_path, _ = process_and_save_image(file, kind)
    if not success:
        flash(f'Gagal mengunggah gambar: {new_path}', 'danger')
        return redirect(url_for('admin.content_edit', kind=kind, record_id=record_id))
    old_path = row.image_path
    try:
        row.image_path = new_path
        db.session.commit()
    except Exception:
        db.session.rollback()
        delete_image_file(new_path)
        flash('Gagal menyimpan gambar ke database.', 'danger')
        return redirect(url_for('admin.content_edit', kind=kind, record_id=record_id))
    if old_path and old_path != new_path:
        delete_image_file(old_path)
    flash('Gambar berhasil diunggah.', 'success')
    return redirect(url_for('admin.content_edit', kind=kind, record_id=record_id))


@admin_bp.post('/content/<kind>/<int:record_id>/remove-image')
@login_required
@admin_required
def content_remove_image(kind, record_id):
    """Clear database reference before deleting the old physical file."""
    if kind not in ('module', 'quiz', 'recipe'):
        abort(404)
    row = db.session.get(KINDS[kind], record_id)
    if row is None:
        abort(404)
    old_path = row.image_path
    if not old_path:
        flash('Tidak ada gambar untuk dihapus.', 'info')
        return redirect(url_for('admin.content_edit', kind=kind, record_id=record_id))
    try:
        row.image_path = None
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Gagal menghapus referensi gambar.', 'danger')
        return redirect(url_for('admin.content_edit', kind=kind, record_id=record_id))
    from app.utils.image_upload import delete_image_file
    delete_image_file(old_path)
    flash('Gambar berhasil dihapus.', 'success')
    return redirect(url_for('admin.content_edit', kind=kind, record_id=record_id))
