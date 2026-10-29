"""Idempotent seed from supplied PDF-derived JSON; NEVER publishes without --publish."""
import json
import re
import sys
import unicodedata
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models.content import LearningModule, QuizCategory, QuizQuestion, Recipe

ROOT = Path(__file__).resolve().parents[1]


def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode().lower()
    return re.sub(r'-{2,}', '-', re.sub(r'[^a-z0-9]+','-',text)).strip('-')[:175]


def run(publish=False):
    with create_app().app_context():
        for row in json.loads((ROOT/'data/modules.json').read_text('utf8')):
            slug=slugify(row['title'])
            record=LearningModule.query.filter_by(slug=slug).first()
            if not record:
                record=LearningModule(slug=slug,title=row['title'],content=row['content'],
                                      category=row['category'],sort_order=row['sort_order'],is_published=publish)
                db.session.add(record)
            # Never overwrite content changed by an administrator
        for row in json.loads((ROOT/'data/quizzes.json').read_text('utf8')):
            slug=slugify(row['title'])
            record=QuizCategory.query.filter_by(slug=slug).first()
            if not record:
                record=QuizCategory(slug=slug,title=row['title'],description=row['description'],is_published=publish)
                db.session.add(record)
                db.session.flush()
                for item in row['questions']:
                    db.session.add(QuizQuestion(category_id=record.id,question=item['question'],
                         options=item['options'],correct=item['correct'],
                         explanation=item['explanation'],sort_order=item['sort_order']))
        for row in json.loads((ROOT/'data/recipes.json').read_text('utf8')):
            slug=slugify(row['title'])
            if Recipe.query.filter_by(slug=slug).first() is None:
                db.session.add(Recipe(slug=slug,title=row['title'],category=row['category'],
                    ingredients=row['ingredients'],steps=row['steps'],tips=row['tips'],
                    is_published=publish))
        db.session.commit()
        print('Data sumber dimasukkan. Publish:',publish)
        print('Modul:',LearningModule.query.count(),'Kategori kuis:',QuizCategory.query.count(),
              'Soal:',QuizQuestion.query.count(),'Resep:',Recipe.query.count())
        print('Konten seed yang sebelumnya ada tidak diubah. Konten baru default draft kecuali --publish.')


if __name__=='__main__':
    if '--help' in sys.argv:
        print('python -m scripts.seed_content [--publish]')
    else:
        run(publish='--publish' in sys.argv)
