# Cakrawala Informasi Gizi (CIG)

> Platform Edukasi Gizi Interaktif Berbasis Web untuk Generasi Muda Indonesia.  
> Dikembangkan di **Universitas Negeri Malang**.

---

## 🥗 Ringkasan Proyek

**Cakrawala Informasi Gizi (CIG)** adalah platform edukasi gizi digital berbahasa Indonesia yang bertujuan membantu masyarakat, khususnya dewasa muda, dalam memahami pola makan bergizi dan seimbang sesuai panduan resmi **Isi Piringku Kementerian Kesehatan RI**.

### Fitur Utama (Tahap Ini):
1. **Beranda & Sistem Desain Resmi**: Replikasi desain antarmuka Figma (warna brand merah `#C62828`, hijau tua `#1B5E20`, latar hangat `#FFF5F5`, typography Poppins, komponen rounded pill).
2. **Autentikasi & Otorisasi Pengguna**:
   - Pendaftaran akun lengkap (nama, email, password, rentang usia, kota domisili).
   - Masuk & Keluar sesi aman dengan Flask-Login dan safe redirect validation.
   - Lupa kata sandi menggunakan token kriptografis berbatas waktu (1 jam).
   - Pengelolaan profil dan perubahan kata sandi dengan verifikasi password lama.
3. **Pondasi Hak Akses Administrator**:
   - Bootstrap administrator awal melalui CLI command.
   - Proteksi rute admin dengan decorator `@admin_required` (403 Forbidden untuk pengguna biasa).
   - Undangan administrator baru via email dengan token kedaluwarsa 24 jam.
   - Panel dashboard admin untuk pemantauan pengguna dan status sistem.
4. **Basis Data & Migrasi**: PostgreSQL 18 + SQLAlchemy ORM + Alembic (Flask-Migrate).
5. **Keamanan**: Proteksi CSRF (Flask-WTF), hashing password dengan scrypt (Werkzeug), rate limiting (Flask-Limiter), cookie HTTPOnly/SameSite, dan sanitasi input.

---

## 🛠️ Stack Teknologi

- **Backend**: Python 3.12+ / 3.15, Flask 3.1
- **Database**: PostgreSQL 18
- **ORM & Migrations**: Flask-SQLAlchemy 3.1, Flask-Migrate (Alembic)
- **Authentication**: Flask-Login 0.6, Werkzeug security
- **Forms & CSRF**: Flask-WTF 1.3, WTForms 3.3
- **Rate Limiting**: Flask-Limiter 4.1
- **Frontend**: Jinja2, Tailwind CSS 3.4, Vanilla JavaScript
- **Testing**: Pytest 9.2, Pytest-Flask

---

## 📁 Struktur Direktori

```text
CIG/
├── app/
│   ├── __init__.py              # Application Factory & Error Handlers
│   ├── config.py                # Konfigurasi Dev, Testing, Production
│   ├── extensions.py            # Inisialisasi Ekstensi (db, login, csrf, mail, limiter)
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py              # Model User, PasswordResetToken, AdminInvitation
│   ├── blueprints/
│   │   ├── main/                # Beranda & Placeholder Fitur Edukasi
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── auth/                # Login, Register, Forgot Password
│   │   │   ├── __init__.py
│   │   │   ├── forms.py
│   │   │   └── routes.py
│   │   ├── user/                # User Dashboard & Profile Management
│   │   │   ├── __init__.py
│   │   │   ├── forms.py
│   │   │   └── routes.py
│   │   └── admin/               # Admin Dashboard, Invite Admin, Users List
│   │       ├── __init__.py
│   │       ├── forms.py
│   │       └── routes.py
│   ├── templates/
│   │   ├── base.html            # Layout utama (HTML5, Tailwind, Font Poppins)
│   │   ├── components/
│   │   │   ├── navbar.html      # Navigasi responsif (Desktop & Mobile)
│   │   │   ├── footer.html      # Footer resmi CIG (3 kolom)
│   │   │   └── flash_messages.html
│   │   ├── main/
│   │   │   ├── index.html       # Beranda CIG (sesuai screenshot Figma)
│   │   │   └── placeholder.html # Placeholder halaman tahap berikutnya
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   ├── forgot_password.html
│   │   │   └── reset_password.html
│   │   ├── user/
│   │   │   ├── dashboard.html
│   │   │   └── profile.html
│   │   ├── admin/
│   │   │   ├── dashboard.html
│   │   │   ├── invite.html
│   │   │   ├── accept_invite.html
│   │   │   └── users.html
│   │   └── errors/
│   │       ├── 404.html
│   │       ├── 403.html
│   │       ├── 500.html
│   │       └── 429.html
│   ├── static/
│   │   ├── css/
│   │   │   ├── input.css        # Tailwind source CSS
│   │   │   └── output.css       # Tailwind compiled & minified CSS
│   │   ├── js/
│   │   │   └── main.js          # Skrip interaksi UI
│   │   └── images/              # Aset visual (hero bowl, banner Isi Piringku)
│   └── utils/
│       ├── decorators.py        # Decorator @admin_required
│       ├── tokens.py            # Generator & validator token SHA-256
│       └── email.py             # Pengirim email notifikasi
├── migrations/                  # Riwayat migrasi database Alembic
├── references/                  # Desain UI, materi modul, kuis, inspirasi
├── tests/
│   ├── conftest.py              # Test client, database fixture, user fixtures
│   ├── test_models.py           # Unit test model & validasi token
│   ├── test_auth.py             # Unit test registrasi, login, reset password
│   └── test_admin.py            # Unit test hak akses admin & alur undangan
├── .env                         # Konfigurasi lokal (rahasia)
├── .env.example                 # Template konfigurasi environment
├── .gitignore
├── manage.py                    # Script CLI manajemen CIG
├── package.json                 # Konfigurasi dependensi Tailwind CSS
├── requirements.txt             # Dependensi Python pip
├── run.py                       # Titik masuk aplikasi Flask
└── tailwind.config.js           # Konfigurasi tema warna & typography Tailwind
```

---

## 🚀 Panduan Menjalankan Aplikasi Secara Lokal

### 1. Prasyarat Sistem
- Python 3.12+ terinstal
- PostgreSQL 16+ running lokal di port 5432
- Node.js & npm (untuk build Tailwind CSS)

### 2. Konfigurasi Environment (.env)
Pastikan file `.env` sudah sesuai dengan kredensial database lokal Anda:
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-cig-2026-change-in-production
DATABASE_URL=postgresql+psycopg2://postgres:PasswordAnda@localhost:5432/cig_db
```

### 3. Instalasi Dependensi Python
```bash
pip install -r requirements.txt
```

### 4. Kompilasi Tailwind CSS
```bash
npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/output.css --minify
```

### 5. Inisialisasi Database & Migrasi
```bash
# Menjalankan migrasi database
flask db upgrade

# Atau menginisialisasi tabel langsung via CLI
python manage.py init-db
```

### 6. Bootstrap Akun Administrator
Gunakan script CLI `manage.py` untuk membuat akun administrator awal (kata sandi dimasukkan secara aman tanpa terekam di riwayat shell):
```bash
python manage.py create-admin --name "Administrator CIG" --email "admin@example.com" --age-range "26-35" --city "Kota Malang"
# Masukkan kata sandi saat diminta secara interaktif
```

### 7. Menjalankan Server Aplikasi
```bash
python run.py
```
Aplikasi akan berjalan di `http://127.0.0.1:5000/`.

---

## 🧪 Pengujian Otomatis (Automated Testing)

Jalankan test suite menggunakan pytest:
```bash
pytest -v
```

Hasil pengujian mencakup 22+ unit & integration tests:
- Pengujian model pengguna, hashing password, dan masa berlaku token.
- Pengujian alur registrasi, validasi duplikat email, login, logout (POST dengan CSRF), dan safe redirect.
- Pengujian alur reset password (request token, verifikasi token, ubah password).
- Pengujian update profil pengguna dan perubahan kata sandi berotentikasi (termasuk verifikasi password saat ubah email).
- Pengujian proteksi route admin (pengguna biasa menerima 403 Forbidden).
- Pengujian pembuatan undangan administrator dan penerimaan undangan.
- Pengujian seluruh placeholder rute edukasi.
- Pengujian integrasi PostgreSQL langsung pada database aktif (`cig_db`).

---

## 📋 Status Rute & Fitur yang Diimplementasikan

| Rute / Endpoint | Metode | Hak Akses | Deskripsi |
|---|---|---|---|
| `/` | `GET` | Publik | Beranda resmi CIG sesuai screenshot Figma |
| `/scan-makanan` | `GET` | Publik | Placeholder fitur AI scan makanan (fase berikutnya) |
| `/modul-edukasi` | `GET` | Publik | Placeholder 9 artikel edukasi gizi interaktif |
| `/kuis` | `GET` | Publik | Placeholder 3 kategori kuis gizi seimbang |
| `/resep` | `GET` | Publik | Placeholder koleksi resep gizi seimbang |
| `/auth/register` | `GET, POST` | Anonim | Pendaftaran pengguna baru |
| `/auth/login` | `GET, POST` | Anonim | Masuk sesi (Rate limited: 10/menit) |
| `/auth/logout` | `POST` | Terautentikasi | Keluar sesi pengguna (CSRF protected) |
| `/auth/forgot-password` | `GET, POST` | Anonim | Permintaan reset kata sandi (Rate limited: 3/jam) |
| `/auth/reset-password/<token>` | `GET, POST` | Anonim | Form reset password dengan token aman |
| `/user/dashboard` | `GET` | Terautentikasi | Dashboard personal pengguna |
| `/user/profile` | `GET` | Terautentikasi | Halaman kelola data diri & keamanan |
| `/user/profile/update` | `POST` | Terautentikasi | Simpan pembaruan profil (verifikasi password saat ubah email) |
| `/user/profile/change-password` | `POST` | Terautentikasi | Ubah kata sandi dengan verifikasi kata sandi lama |
| `/admin/dashboard` | `GET` | Admin Only | Dashboard manajemen administrator |
| `/admin/invite` | `GET, POST` | Admin Only | Kirim undangan administrator baru |
| `/admin/accept-invite/<token>` | `GET, POST` | Publik / Token | Menerima undangan admin dan membuat akun |
| `/admin/users` | `GET` | Admin Only | Tabel daftar seluruh pengguna terdaftar |

---

## 🔜 Fitur untuk Fase Selanjutnya (Roadmap)
- Integrasi model AI YOLOv8s-seg untuk segmentasi dan estimasi proporsi piring makanan.
- 9 Artikel Edukasi Gizi Lengkap berbasis materi asli dokumen `MATERI CIG_MODUL MATERI.pdf`.
- 3 Kategori Kuis Interaktif (@ 10 pertanyaan per kategori, total 30 pertanyaan) sesuai dokumen asli `MATERI CIG_KUIS.pdf`, dengan penyimpanan nilai tertinggi (*highest score retention*) untuk pengguna terautentikasi (tanpa sertifikat atau badge digital).
- Katalog Resep Makanan Indonesia Bergizi Seimbang sesuai dokumen asli `MATERI CIG_RESEP.pdf`.
- Food Scan History & Meal Tracker per pengguna.
- Sistem CMS Admin Lengkap untuk mengelola 9 artikel edukasi, bank soal kuis, dan resep (tanpa analytics dashboard pengguna dan tanpa export data riset).
