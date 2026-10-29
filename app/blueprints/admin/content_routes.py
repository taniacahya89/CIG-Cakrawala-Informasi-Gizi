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
            db.session.commit()
        except (ValueError,TypeError) as exc:
            db.session.rollback()
            flash(str(exc),'danger')
            return redirect(request.url)
        except Exception:
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


@admin_bp.route('/content/<kind>/<int:record_id>/upload-image', methods=['POST'])
@login_required
@admin_required
def content_upload_image(kind, record_id):
    """Handle image upload for a content item."""
    if kind not in ('module', 'quiz', 'recipe'):
        abort(404)
    
    if kind not in KINDS:
        abort(404)
    
    model = KINDS[kind]
    row = db.session.get(model, record_id)
    if row is None:
        abort(404)
    
    # Check if file was uploaded
    if 'image' not in request.files:
        flash('Tidak ada file yang dipilih.', 'danger')
        return redirect(request.referrer or url_for('admin.content_index'))
    
    file = request.files['image']
    if file.filename == '':
        flash('Tidak ada file yang dipilih.', 'danger')
        return redirect(request.referrer or url_for('admin.content_index'))
    
    # Get existing image path for replacement
    existing_image = getattr(row, 'image_path', None)
    
    # Process and save the image
    from app.utils.image_upload import process_and_save_image
    success, result, original_name = process_and_save_image(file, kind, existing_image)
    
    if success:
        row.image_path = result
        db.session.commit()
        flash('Gambar berhasil diunggah.', 'success')
    else:
        flash(f'Gagal mengunggah gambar: {result}', 'danger')
    
    return redirect(request.referrer or url_for('admin.content_index'))


@admin_bp.route('/content/<kind>/<int:record_id>/remove-image', methods=['POST'])
@login_required
@admin_required
def content_remove_image(kind, record_id):
    """Remove the image from a content item."""
    if kind not in ('module', 'quiz', 'recipe'):
        abort(404)
    
    if kind not in KINDS:
        abort(404)
    
    model = KINDS[kind]
    row = db.session.get(model, record_id)
    if row is None:
        abort(404)
    
    # Get and delete the existing image file
    existing_image = getattr(row, 'image_path', None)
    if existing_image:
        from app.utils.image_upload import delete_image_file
        delete_image_file(existing_image)
        
        # Clear the image path in database
        row.image_path = None
        db.session.commit()
        flash('Gambar berhasil dihapus.', 'success')
    else:
        flash('Tidak ada gambar untuk dihapus.', 'info')
    
    return redirect(request.referrer or url_for('admin.content_index'))
