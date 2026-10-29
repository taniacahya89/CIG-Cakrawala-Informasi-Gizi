# PANDUAN WINDOWS — Menjalankan CIG (Paket Diperbaiki)

Versi: 29 Oktober 2026 — tambahan perbaikan pengaitan Blueprint konten dan navigasi halaman.

## Yang perlu diunduh

Hanya **CIG_LANJUTAN_PERBAIKAN_WINDOWS.zip** dari chat. Kamu **tidak** perlu mengunduh PATCH lama atau memasang ulang Python, Node.js, dan PostgreSQL kalau semuanya sudah tersedia.

## 1. Simpan proyek asli

- Biarkan `A:\tania\CIG` sebagai backup. Jangan langsung ditimpa.
- Buat backup database `cig_db`: di pgAdmin 4, klik kanan `cig_db` → Backup → pilih format `Custom` → tentukan lokasi backup di laptop → Backup.
- Sebelum menjalankan salinan, hentikan server Flask asli (Ctrl+C pada terminalnya).

## 2. Ekstrak ZIP

- Klik kanan ZIP → **Extract All**.
- ZIP berisi sebuah folder bernama `CIG`. Salin folder itu ke drive `A:\tania\` dan beri nama **`CIG_next`**.
- Pastikan file `A:\tania\CIG_next\run.py` ada (bukan `CIG_next\CIG\run.py`).
- Bila drive A: tidak ada, gunakan lokasi lain dan sesuaikan seluruh perintah di bawah.

## 3. Pindahkan konfigurasi lama secara lokal

Buka PowerShell dan ketik:

```powershell
Copy-Item -LiteralPath 'A:\tania\CIG\.env' -Destination 'A:\tania\CIG_next\.env'
```

Pastikan file sumber ada. **Jangan unggah file `.env` ke chat atau GitHub.** Buka `.env` secara lokal dan cek `DATABASE_URL` menunjuk ke `cig_db`. Periksa username/password database hanya di komputermu.

## 4. Siapkan Python 3.12 di proyek salinan

Buka PowerShell:

```powershell
Set-Location 'A:\tania\CIG_next'
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Kalau environment `.venv` sudah ada di `CIG_next`, tidak perlu dibuat ulang. Penggunaan `python.exe` langsung menghindari error kebijakan eksekusi PowerShell.

## 5. Cek sambungan PostgreSQL dan revisi migrasi

Pastikan layanan PostgreSQL berjalan dan `cig_db` sudah ada. Jalankan:

```powershell
.\.venv\Scripts\python.exe -m flask --app run:app db current
.\.venv\Scripts\python.exe -m flask --app run:app db heads
```

Jika `db current` kosong, menunjukkan revisi selain `045d86967952` atau `20261029_content`, atau muncul error koneksi, **hentikan dan kirim pesan error (tanpa password)**. Jangan menjalankan perintah reset/drop database.

Jika migrasi awal `045d86967952` sudah terpasang dan backup selesai, jalankan:

```powershell
.\.venv\Scripts\python.exe -m flask --app run:app db upgrade
.\.venv\Scripts\python.exe -m flask --app run:app db current
```

Revisi akhir yang diharapkan untuk paket ini: `20261029_content`.

## 6. Masukkan konten PDF asli sebagai draft

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_content
```

Output yang diharapkan untuk DB yang baru di-seed: 9 modul, 3 kategori kuis, 30 soal, 19 resep. Default-nya konten adalah **draft**, jadi belum tampil di halaman publik sampai diterbitkan oleh admin di `/admin/content`.

Untuk **demo lokal saja setelah kamu meninjau isi konten** dan hanya jika DB masih kosong untuk konten:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_content --publish
```

`--publish` hanya berdampak pada konten yang *baru* ditambahkan; tidak akan mengubah draft yang sudah ada. Untuk draft yang sudah ada, terbitkan dari dashboard admin.

## 7. Jalankan pengujian tanpa mengubah data produksi

Pengujian unit SQLite (tidak menyentuh `cig_db`):

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_auth.py tests/test_admin.py tests/test_models.py tests/test_content.py
```

**Penting:** file `tests/test_postgres_integration.py` mengakses langsung `cig_db` dan melakukan CRUD pada akun uji. Jalankan hanya jika sudah backup dan memahami efeknya. Jangan jalankan seluruh `pytest` secara membabi buta jika database berisi data nyata.

## 8. Siapkan login administrator untuk memeriksa konten

Jika akun admin lama sudah tidak aktif atau belum ada admin yang bisa login, buat admin lokal baru. Jalankan di PowerShell dengan email milikmu sendiri:

```powershell
.\.venv\Scripts\python.exe manage.py create-admin --name "Administrator CIG" --email "emailmu@example.com" --age-range "18-25" --city "Malang"
```

Ganti `emailmu@example.com` dengan alamat email milikmu. Password akan diminta melalui terminal secara interaktif (tidak tampil). Jangan menuliskan password pada argumen perintah, chat, atau screenshot.

Jika akun admin kamu masih aktif dan bisa login, langkah ini tidak diperlukan.

## 9. Jalankan Flask

```powershell
.\.venv\Scripts\python.exe run.py
```

Lalu buka browser:

- Beranda: http://127.0.0.1:5000/
- Modul: http://127.0.0.1:5000/modul-edukasi
- Kuis: http://127.0.0.1:5000/kuis
- Resep: http://127.0.0.1:5000/resep
- CMS admin (wajib login admin): http://127.0.0.1:5000/admin/content
- Dashboard: http://127.0.0.1:5000/user/dashboard

Saat aplikasi berjalan, biarkan terminalnya tetap terbuka. Hentikan dengan Ctrl+C.

## 10. Yang memang belum berfungsi penuh

- Scan YOLO/`best.pt` belum terhubung; `/scan-makanan` masih placeholder.
- Meal Tracker belum punya data scanner sungguhan.
- Pengiriman email reset/undangan butuh SMTP lokal atau server email terkonfigurasi.
- Styling serta fitur CMS memerlukan pengujian browser dan perbaikan lanjutan.

## Pemecahan masalah singkat

- `py -3.12 not found`: instal Python 3.12 atau periksa Python Launcher.
- `ModuleNotFoundError`: pastikan instalasi `pip install -r requirements.txt` berhasil dari `.venv`.
- `password authentication failed` atau `connection refused`: cek layanan PostgreSQL dan `DATABASE_URL` lokal.
- `Address already in use` port 5000: hentikan server Flask lain (Ctrl+C).
- `relation ... does not exist`: periksa `flask db current`/`db upgrade` sebelum menjalankan seed.
- Halaman kosong: periksa konten masih berstatus draft; masuk ke `/admin/content`.

**Catatan verifikasi:** perbaikan pada paket ini telah dicek secara statis; uji runtime Flask/PostgreSQL harus dilakukan di Windows karena akses ke database lokal dan dependensi Flask tidak tersedia di lingkungan pembuatan paket.
