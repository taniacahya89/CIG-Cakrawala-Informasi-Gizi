"""Coverage for newly added educational modules, quizzes and recipes."""
from app.extensions import db
from app.models.content import LearningModule, QuizCategory, QuizQuestion, Recipe, QuizBestScore, RecipeFavorite


def seed(app):
    with app.app_context():
        db.session.add(LearningModule(slug='test-modul',title='Modul Uji',content='Isi uji',category='Materi',sort_order=1,is_published=True))
        db.session.add(Recipe(slug='uji',title='Resep Uji',category='Makanan Utama',ingredients='Beras',steps='Masak',tips='',is_published=True))
        cat=QuizCategory(slug='uji-kuis',title='Kuis Uji',description='Tes',is_published=True)
        db.session.add(cat);db.session.flush()
        db.session.add(QuizQuestion(category_id=cat.id,question='Mana jawaban benar?',
                       options={'A':'Benar','B':'Salah','C':'Salah','D':'Salah'},
                       correct='A',explanation='Pembahasan soal',sort_order=1))
        db.session.commit()


def test_public_content(client,app):
    seed(app)
    assert client.get('/modul-edukasi').status_code==200
    assert b'Modul Uji' in client.get('/modul-edukasi').data
    assert b'Isi uji' in client.get('/modul-edukasi/test-modul').data
    assert b'Resep Uji' in client.get('/resep').data
    assert b'Masak' in client.get('/resep/uji').data


def test_quiz_guest_feedback_and_result(client,app):
    seed(app)
    assert client.get('/kuis/uji-kuis').status_code==200
    response=client.post('/kuis/uji-kuis/answer',data={'answer':'A'},follow_redirects=True)
    assert b'Jawaban benar' in response.data
    response=client.post('/kuis/uji-kuis/next',follow_redirects=True)
    assert b'Hasil Kuis' in response.data
    with app.app_context():
        assert QuizBestScore.query.count()==0


def test_unpublished_content_hidden(client,app):
    with app.app_context():
        db.session.add(Recipe(slug='draft',title='Draft',category='Makanan Utama',ingredients='',steps='',tips='',is_published=False))
        db.session.commit()
    assert client.get('/resep/draft').status_code==404


def test_favorite_guest_requires_login(client,app):
    seed(app)
    response=client.post('/resep/uji/favorite')
    assert response.status_code in (302,401)


def test_content_routes_registered_and_no_redirect_loops(client):
    """Public content routes should be reachable and must not redirect to themselves."""
    for route in ('/modul-edukasi', '/kuis', '/resep'):
        response = client.get(route)
        assert response.status_code == 200, (route, response.status_code, response.headers.get('Location'))
