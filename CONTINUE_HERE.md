# CIG — Paket Kode Lanjutan (29 Oktober 2026) — Revisi Perbaikan

**Pengguna Windows:** mulai dari `PANDUAN_WINDOWS_MULAI_DI_SINI.md` (sudah mencakup perbaikan registrasi blueprint, konflik route, dan perintah tes aman).

**Ini kode tambahan yang nyata**, dibuat pada sumber `CIG.zip` yang dikirim pengguna. Ini bukan proyek baru. Jangan menimpa `.env` dan database PostgreSQL lokal Anda.

## Apa yang ditambahkan

- `app/models/content.py`: 9 tabel baru untuk modul/progres, kuis/skor terbaik, resep/favorit/kunjungan, serta *schema* histori scan.
- `app/blueprints/content/`: daftar dan detail modul, progres baca, kuis 1-soal-per-langkah dengan pembahasan langsung, nilai terbaik, resep dan favorit.
- `app/blueprints/admin/content_routes.py`: CMS admin untuk membuat, mengedit, menerbitkan, dan mengarsipkan konten. Semua endpoint dibatasi `admin_required`.
- `app/templates/content/`, `app/templates/admin/content_*.html`: antarmuka baru mengikuti warna CIG.
- `app/static/css/features.css`: gaya tambahan berbasis design system, tanpa perlu Node untuk menyajikan halaman.
- `data/*.json`: hasil ekstraksi dokumen sumber: **9 materi, 30 soal pada 3 kuis, dan 19 resep**. Angka gizi, porsi, waktu, dan foto yang tidak disediakan **tidak diisi secara otomatis**.
- `scripts/seed_content.py`: seed idempotent yang mempertahankan perubahan konten admin; default status konten baru *draft*.
- `migrations/versions/20261029_cig_content.py`: migrasi additive. Tidak menghapus atau menulis ulang tabel pengguna lama.
- `tests/test_content.py`: tes baru untuk fitur publik, pembahasan kuis, dan pembatasan konten draft.
- `app/templates/user/dashboard.html`: ringkasan aktivitas berdasarkan database (bukan angka placeholder).
- `app/templates/user/meal_tracker.html`: kerangka tampilan yang membaca ScanHistory asli, **scanner belum terintegrasi**.

## Cara menerapkan di Windows dengan aman

1. **Backup folder `A:\tania\CIG` dan backup database `cig_db` lebih dahulu.**
2. **Cara paling aman:** Salin folder kode ini menjadi `A:\tania\CIG_next` (bukan menimpa `CIG` asli). Salin `.env` Anda sendiri secara lokal dari folder asli ke `CIG_next/.env`. Jangan kirim `.env` ke pihak lain.
3. Buka PowerShell di `A:\tania\CIG_next`, aktifkan virtual environment Python 3.12 yang sesuai. Jika belum ada, buat: `py -3.12 -m venv .venv`.
4. Instal: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
5. Pastikan PostgreSQL hidup dan DATABASE_URL pada `.env` menunjuk DB yang benar.
6. **Periksa revision database dahulu:** `.\.venv\Scripts\python.exe -m flask db current`. Pastikan migrasi `045d86967952` sudah ada di database dan backup tersedia.
7. Jalankan **migrasi additive**: `.\.venv\Scripts\python.exe -m flask db upgrade`. *Jangan* gunakan `manage.py init-db` atau perintah drop tabel.
8. Masukkan konten sebagai draft: `.\.venv\Scripts\python.exe -m scripts.seed_content`.
9. Tinjau konten di admin `http://127.0.0.1:5000/admin/content`, kemudian terbitkan setiap konten dari editor. **Hanya untuk demo lokal setelah semua konten diperiksa**, Anda boleh seed dengan `--publish` pada database bersih. Perintah `--publish` **tidak** mengubah status entri yang sebelumnya sudah disimpan.
10. Jalankan tes: `.\.venv\Scripts\python.exe -m pytest -q`, lalu jalankan server: `.\.venv\Scripts\python.exe run.py`.

## Yang masih harus dilanjutkan coding agent

**Sangat penting**: paket ini belum menerapkan pemindaian AI yang nyata karena implementasi Flask inferensi dan `best.pt` tidak ada di arsip yang dikirim. Fitur Scan masih placeholder. `ScanHistory` dibuat untuk persiapan, bukan data scan palsu.

Selanjutnya coding agent perlu: (a) integrasi model Flask/YOLO sebenarnya (termasuk penanganan mask dan verifikasi rumus visual); (b) penyimpanan gambar yang aman dan penghapusan scan oleh pemiliknya; (c) penyempurnaan CMS (upload gambar dan metadata resep), validasi sumber dan konten; (d) pengujian visual Figma, database PostgreSQL nyata, keamanan login/email, dan deployment.

## Kualitas/verifikasi

Kode dalam paket telah diperiksa menggunakan `compileall` (pemeriksaan sintaks). **Pengujian end-to-end Flask/PostgreSQL belum dijalankan di sini** karena dependensi runtime proyek dan instance PostgreSQL Windows lokal tidak tersedia. Jangan menganggap seluruh fitur telah lulus test sebelum dites di laptop.

**Keamanan**: Salinan kode tidak berisi file `.env`, password asli, virtual environment, maupun `node_modules`. Perubahan keamanan awal membatasi debug lokal dan menghilangkan pengungkapan reset/invitation token dari pesan browser. Namun perlu security audit menyeluruh sebelum publikasi.
