# CIG — Audit source code dan perbaikan (29 Oktober 2026)

**Dasar audit:** ZIP `CIG-new-v2.zip` yang diserahkan pengguna, bukan laporan yang dibuat agent. Audit bersifat source-level; koneksi PostgreSQL di laptop Windows dan pengujian aplikasi penuh tidak dapat dijalankan di lingkungan ini karena dependensi Flask tidak tersedia dan koneksi instalasi pip tidak tersedia.

## Ringkasan kondisi

| Area | Hasil dari source code |
| --- | --- |
| Flask modular, blueprint, login, admin | Kode tersedia; belum runtime-tested di Windows versi ini |
| Beranda, UI admin, CMS | Template dan route tersedia |
| Materi | 9 artikel JSON; listing/detail dan progres baca di kode |
| Kuis | 3 kategori, 30 soal JSON; umpan balik langsung dan skor terbaik pengguna login |
| Resep | 19 resep JSON; listing, detail, favorit, view history |
| Upload gambar | Ada pada modul, kategori kuis, resep; beberapa bug diperbaiki di patch |
| Migrasi | Tiga revision tersedia: `045d86967952` → `20261029_content` → `089219c44934` |
| Scanner YOLO | **Belum diimplementasikan**: `/scan-makanan` masih placeholder. `best.pt` tidak ada dalam ZIP |
| Meal Tracker | Route dan daftar `ScanHistory` ada, tetapi tidak ada scan yang menghasilkan record dan belum ada delete untuk pemilik |
| Deployment | Belum siap dinyatakan aman/berfungsi di hosting; penyimpanan upload saat ini di disk lokal |

## Bug dan risiko yang telah diperbaiki di kode paket ini

1. **`requirements.txt` belum mencantumkan Pillow**, padahal `app/utils/image_upload.py` memerlukan `PIL`. Ditambahkan `Pillow>=10.4,<13`.
2. **Template `app/templates/content/module_detail.html` kehilangan `{% endblock %}`** sebelum blok JavaScript, menimbulkan kesalahan parsing Jinja (kemungkinan HTTP 500). Diperbaiki dan seluruh template kembali berhasil diparse.
3. **Gambar lama dihapus sebelum file baru dan transaksi DB berhasil**, serta kode sebelumnya menyatukan lokasi folder dengan nama berisi jalur relatif (cleanup salah). Kini gambar baru disimpan terpisah; gambar lama dihapus **hanya setelah commit DB** berhasil.
4. **`delete_image_file` menerima path dari database tanpa pembatasan direktori**. Kini hanya path gambar UUID WebP dalam subfolder upload yang diizinkan.
5. **Form upload gambar konten baru mengirim ke ID 0**. Kini admin bisa memilih gambar saat membuat konten baru dan menyimpannya dengan data konten dalam satu transaksi kerja.
6. **Validasi media** diperkuat dengan pembatasan 5 MB, verifikasi format aktual via Pillow, batas resolusi, auto-orientation, resize, dan WebP. Diberi batas multipart global 6 MB.
7. **Tidak ada preview sebelum upload** pada editor. Ditambahkan preview browser untuk konten lama maupun baru.
8. **Ketika SMTP gagal, email reset password/undangan admin dicatat utuh ke log**, termasuk token rahasia. Logging isi email dihapus; HTML email juga meng-escape nama yang berasal dari pengguna.
9. **Undangan admin terhadap akun yang sudah terdaftar** dapat meng-upgrade sekaligus melakukan login tanpa meminta password pengguna yang sudah terdaftar. Kini harus login dahulu sebagai pemilik akun yang dimaksud.
10. **Validasi redirect login salah menolak URL relatif yang aman**, seperti `/admin/accept-invite/<token>`. Sekarang menangani path relatif lokal dengan aman dan menolak URL eksternal.
11. **`.gitignore` berisi `*.keyreferences/` yang tergabung pada satu baris**. Dibetulkan.
12. Ditambahkan dua berkas regression test untuk upload gambar dan undangan akun yang sudah ada.

## Validasi yang dilakukan

- Seluruh **42 file Python** berhasil di-parse dengan `ast` (pemeriksaan sintaks; bukan hasil menjalankan Flask).
- Seluruh **30 template Jinja2** berhasil di-parse; sebelum perbaikan, `module_detail.html` gagal parsing.
- Data JSON valid: 9 modul, 3 kategori/30 soal, 19 resep.
- Pemeriksaan terisolasi terhadap helper upload dengan Pillow: 6 skenario lulus (file PNG→WebP, simpan, file rusak, file terlalu besar, percobaan path traversal, delete).
- **Belum dilakukan:** pytest lengkap, koneksi PostgreSQL asli, uji migrasi, Chrome UI end-to-end, file `best.pt` / YOLO; wajib diverifikasi di Windows pengguna.

## Pekerjaan berikutnya yang belum diselesaikan dalam patch ini

1. Integrasi scanner YOLOv8s-seg asli: unggah bobot `best.pt` dan sediakan nama/indeks empat kelas segmentasi. Pastikan hasil hanya menggambarkan **persentase area visual**, bukan gram, kalori, atau kecukupan zat gizi.
2. Simpan scan user ke `scan_history` dan tambahkan fitur melihat/menghapus riwayat per pengguna; tamu tidak menyimpan riwayat permanen.
3. Uji ulang alur lengkap admin CMS, autentikasi, kuis, dan resensi resep di laptop Windows, termasuk image upload baru/replace/remove.
4. Siapkan penyimpanan gambar permanen untuk deployment (folder upload diabaikan Git dan sebagian hosting memakai disk ephemeral).
5. Siapkan mail SMTP dan konfigurasi aman untuk production; amankan kredensial dan nonaktifkan debugger.

## Penanganan ZIP asli

ZIP asli menyertakan `.env`, virtual environment, dependensi Node, dan folder `.git` beserta riwayat. Paket output **tidak menyertakan** file-file tersebut. ZIP output juga tidak mencakup `references/` atau foto upload admin. Simpan semua file asli lokal dan jangan mempublikasikan ZIP asli.
