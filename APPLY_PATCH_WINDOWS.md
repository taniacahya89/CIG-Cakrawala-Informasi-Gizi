# CIG — Cara memasang perbaikan pada Windows

Paket audit ini dibuat dari `CIG-new-v2.zip` tanggal 29 Oktober 2026. Tidak berisi `.env`, `.git`, `.venv`, `node_modules`, foto unggahan admin, maupun bobot `best.pt`.

## Pilihan paling aman: pasang ZIP patch ke salinan proyek

1. Matikan server Flask di PowerShell dengan `Ctrl+C`.
2. **Backup** folder `A:\tania\CIG-new` dan database `cig_db` melalui pgAdmin (format Custom). Jangan hapus database atau file `.env`.
3. Ekstrak `CIG_PATCH_PERBAIKAN.zip` ke sebuah folder sementara, misalnya `A:\tania\CIG_patch`.
4. Periksa bahwa di dalam folder ekstraksi terdapat folder `app`, `tests`, serta `requirements.txt`. **Salin isi folder ekstraksi** ke salinan folder `A:\tania\CIG-new`, pilih **Replace** hanya setelah backup dibuat. Jangan menimpa `.env` (tidak ada di patch).
5. Buka PowerShell baru:

```powershell
cd A:\tania\CIG-new
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app run:app db current
```

6. **Jika** `db current` menunjukkan revisi `20261029_content` dan backup sudah lengkap, migrasi gambar dari proyek yang sudah ada mungkin belum diterapkan. Jalankan `db upgrade` hanya jika memang diperlukan, setelah memeriksa revision. Jika menunjukkan `089219c44934`, **tidak perlu migrasi** untuk patch ini. Jika hasilnya lain atau error, berhenti dan periksa log; jangan `drop` tabel.
7. Jalankan test lokal:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_auth.py tests/test_admin.py tests/test_models.py tests/test_content.py tests/test_image_upload.py tests/test_invite_existing_user.py
```

8. Jalankan aplikasi:

```powershell
$env:FLASK_DEBUG='0'
.\.venv\Scripts\python.exe run.py
```

9. Uji login admin → CMS → edit salah satu Modul / Kuis / Resep → upload JPG/PNG/WebP (maks. 5 MB) → lihat gambar publik → ganti → hapus. Juga uji menambahkan konten baru beserta gambarnya.

## Penting

- **Patch ini tidak mengubah isi database**, dan tidak mengandung model YOLO.
- Jika menguji gambar dari admin, file hasil upload disimpan lokal pada `app/static/uploads/` dan **diabaikan Git**. Backup folder ini sebelum deployment atau memindahkan project.
- Jika upload 5 MB lebih besar dari batas Flask, aplikasi mengembalikan pesan file terlalu besar.
- Jangan upload `.env` atau folder `.git` ke chat/GitHub. ZIP asli yang dikirim sebelumnya sudah mencakup keduanya; jika kredensialnya pernah dibagikan secara publik, ganti password database/secret key dan audit riwayat Git.
- Jangan menggunakan server debug untuk akses publik.

## Penempatan model AI

Simpan `best.pt` di `A:\tania\CIG-new\models\yolo\best.pt`. Sebelum AI Scanner dapat berfungsi, diperlukan implementasi integrasi inferensi YOLO dan informasi mapping indeks kelas dari model tersebut.
