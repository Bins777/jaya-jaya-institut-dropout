# Master Prompt untuk Claude Code — Proyek Jaya Jaya Institut

> Cara pakai: buka terminal di folder proyek ini (folder `submission/`), jalankan `claude`, lalu paste prompt di bawah garis. Kerjakan per-fase; Claude Code akan berhenti dan meminta konfirmasi di langkah yang butuh akun kamu (GitHub, Streamlit Cloud).

---

Saya sedang menyelesaikan submission Dicoding "Menyelesaikan Permasalahan Institusi Pendidikan" (Jaya Jaya Institut, prediksi student dropout). Sebagian besar sudah jadi di folder ini:

- `notebook.ipynb` — sudah dieksekusi penuh (EDA, modeling, evaluation, conclusion)
- `app.py` — prototype Streamlit, sudah dites jalan
- `model/model.joblib`, `model/metadata.json`, `model/feature_defaults.json` — model Logistic Regression (accuracy 94,2%, recall 91,9%, ROC-AUC 0,973)
- `data.csv` — dataset asli (separator `;`)
- `data_dashboard.csv` — data berlabel + kolom `dropout_risk_score`, sumber data dashboard Metabase
- `train_model.py`, `prepare_dashboard_data.py` — script pendukung
- `README.md` — dokumentasi lengkap (masih ada placeholder link Streamlit)
- `requirements.txt`

Identitas saya: Nama **Georgius Bintang**, ID Dicoding **Georgius_bintang**, email **georgiusbb@gmail.com**.

Tolong kerjakan tahap-tahap berikut SATU PER SATU, verifikasi tiap tahap sebelum lanjut:

## Fase 1 — Verifikasi lokal
1. Buat virtualenv, `pip install -r requirements.txt`.
2. Jalankan `streamlit run app.py`, pastikan tidak error dan prediksi bekerja (coba 1 kasus risiko tinggi: tunggakan biaya = Yes, SKS lulus semester 1–2 = 1, nilai 6–7; harus keluar risiko tinggi).
3. Pastikan `notebook.ipynb` masih valid (cukup cek JSON-nya bisa dibuka, tidak perlu re-run kecuali rusak).

## Fase 2 — Dashboard Metabase (Docker)
1. Jalankan Metabase: `docker run -d -p 3000:3000 --name metabase metabase/metabase`, tunggu sampai siap (cek `docker logs -f metabase` sampai "Metabase Initialization COMPLETE").
2. Pandu saya setup admin di http://localhost:3000 dengan email `root@mail.com` password `root123`.
3. Karena Metabase tidak bisa membaca CSV langsung, buat database SQLite/Postgres dari `data_dashboard.csv`:
   - Opsi termudah: jalankan container Postgres (`docker run -d --name pg -e POSTGRES_PASSWORD=root123 -p 5433:5432 postgres`), load `data_dashboard.csv` ke tabel `students` dengan script Python (pandas + sqlalchemy + psycopg2), lalu hubungkan Metabase ke Postgres itu (host: gunakan IP docker `host.docker.internal` atau network bridge).
4. Buatkan aku daftar pertanyaan (question) Metabase untuk dashboard "Jaya Jaya Institut — Student Monitoring", minimal:
   - KPI: total siswa; jumlah & % dropout; rata-rata `dropout_risk_score` siswa Enrolled
   - Bar: dropout rate per `course` (urutkan menurun)
   - Bar: dropout rate per `tuition_up_to_date`, `scholarship_holder`, `debtor`
   - Bar: dropout rate per `age_group` dan per `gender`
   - Bar: rata-rata `units_2nd_sem_approved` per `status`
   - Histogram `dropout_risk_score` untuk status = Enrolled + tabel siswa Enrolled dengan skor > 0.6
   Pandu aku klik-per-klik membuatnya, atau buat otomatis via Metabase API (http://localhost:3000/api) kalau bisa.
5. Setelah dashboard jadi: export DB Metabase: `docker cp metabase:/metabase.db/metabase.db.mv.db ./`
6. Ingatkan aku screenshot dashboard dan simpan sebagai `Georgius_bintang-dashboard.png`.

## Fase 3 — Deploy ke Streamlit Community Cloud
1. Inisialisasi git repo di folder ini (jika belum), buat `.gitignore` seperlunya (jangan ignore `model/` — dibutuhkan app).
2. Buat repo GitHub publik (pakai `gh repo create jaya-jaya-institut-dropout --public`), push semua file yang dibutuhkan app: `app.py`, `requirements.txt`, folder `model/`.
3. Pandu aku deploy di https://share.streamlit.io → New app → pilih repo → main file `app.py`.
4. Setelah dapat URL, ganti placeholder link di `README.md` bagian "Akses prototype".

## Fase 4 — Packaging submission
1. Cek struktur akhir sesuai ketentuan Dicoding:
   ```
   submission
   ├── model/                         (model.joblib, metadata.json, feature_defaults.json)
   ├── notebook.ipynb                 (sudah dieksekusi)
   ├── app.py
   ├── README.md                      (link Streamlit sudah terisi)
   ├── requirements.txt
   ├── data.csv, data_dashboard.csv
   ├── train_model.py, prepare_dashboard_data.py
   ├── metabase.db.mv.db
   ├── Georgius_bintang-dashboard.png
   └── Georgius_bintang-video.mp4     (opsional, kalau sudah kurekam)
   ```
2. Validasi: README tidak boleh ada placeholder tersisa; app.py jalan dari clean venv; metabase.db.mv.db ada.
3. Zip folder jadi `submission.zip`.

Selalu tunjukkan perintah yang akan kamu jalankan sebelum menjalankannya untuk langkah yang menyentuh Docker, git, atau akun online.
