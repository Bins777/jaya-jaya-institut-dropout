# Proyek Akhir: Menyelesaikan Permasalahan Institusi Pendidikan — Jaya Jaya Institut

- **Nama:** Georgius Bintang
- **Email:** georgiusbb@gmail.com
- **ID Dicoding:** Georgius_bintang

## Business Understanding

Jaya Jaya Institut merupakan institusi pendidikan perguruan tinggi yang berdiri sejak tahun 2000 dan telah mencetak banyak lulusan dengan reputasi sangat baik. Namun, terdapat banyak siswa yang tidak menyelesaikan pendidikannya alias **dropout** — mencapai **32,1%** (1.421 dari 4.424 siswa). Tingkat dropout yang tinggi merugikan institusi baik secara finansial maupun reputasi, sehingga institusi ingin **mendeteksi sedini mungkin** siswa yang berisiko dropout agar dapat diberikan bimbingan khusus.

### Permasalahan Bisnis

1. Tingkat dropout sangat tinggi (±32%, hampir 1 dari 3 siswa) dan belum diketahui faktor-faktor utama penyebabnya.
2. Belum ada mekanisme deteksi dini siswa berisiko dropout, sehingga intervensi selalu terlambat.
3. Belum ada dashboard monitoring yang memudahkan manajemen memahami data dan memantau performa siswa.

### Cakupan Proyek

1. Exploratory Data Analysis (EDA) untuk menemukan faktor-faktor yang memengaruhi dropout.
2. Membangun model machine learning untuk memprediksi risiko dropout siswa.
3. Membuat business dashboard menggunakan **Metabase** untuk monitoring performa siswa.
4. Membangun prototype prediksi berbasis **Streamlit** dan men-deploy-nya ke Streamlit Community Cloud.
5. Menyusun rekomendasi action items untuk menurunkan tingkat dropout.

### Persiapan

**Sumber data:** [Dicoding — students' performance dataset](https://github.com/dicodingacademy/dicoding_dataset/blob/main/students_performance/README.md) — 4.424 baris × 37 kolom berisi data demografi, sosial-ekonomi, dan performa akademik siswa, dengan target `Status` (Dropout / Enrolled / Graduate).

**Setup environment (venv):**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Menjalankan notebook:** buka `notebook.ipynb` di Jupyter/Colab lalu *Run All*. Notebook memuat seluruh tahapan: business understanding, data understanding, EDA, data preparation, modeling, evaluation, hingga kesimpulan.

**File pendukung:**

- `train_model.py` — script training model (menghasilkan `model/model.joblib` dan `model/metadata.json`).
- `prepare_dashboard_data.py` — menghasilkan `data_dashboard.csv` (data berlabel + skor risiko model) yang menjadi sumber data dashboard Metabase.
- `load_dashboard_db.py` — memuat `data_dashboard.csv` ke `students.db` (SQLite, tabel `students`) agar bisa dibaca Metabase.
- `metabase_setup.py` — membangun seluruh question & dashboard Metabase secara otomatis lewat Metabase API.
- `validate_submission.py` — memeriksa kelengkapan struktur submission (lihat `METABASE_SETUP.md` untuk panduan dashboard).

## Business Dashboard

Dashboard dibuat menggunakan **Metabase** (via Docker) dengan sumber data `data_dashboard.csv` yang telah diperkaya label kategori yang mudah dibaca serta kolom `dropout_risk_score` dari model.

Dashboard **"Jaya Jaya Institut — Student Monitoring"** menampilkan:

1. **KPI utama** — total siswa, jumlah & persentase dropout, rata-rata skor risiko siswa aktif (Enrolled).
2. **Distribusi status siswa** (Dropout / Enrolled / Graduate).
3. **Dropout rate per program studi** — memperlihatkan konsentrasi dropout di Biofuel Production Tech (67%), Equinculture (55%), Informatics Engineering (54%).
4. **Dropout rate berdasarkan faktor finansial** — status pembayaran (menunggak = 86,6% dropout), beasiswa, dan debtor.
5. **Dropout rate per kelompok usia dan gender**.
6. **Perbandingan performa akademik** (rata-rata SKS lulus semester 1–2) antar status.
7. **Distribusi skor risiko** siswa Enrolled — daftar siswa aktif berisiko tinggi (skor > 0,6) untuk diprioritaskan bimbingan.

**Akses Metabase (lokal):**

- URL: `http://localhost:3000`
- Email: `root@mail.com`
- Password: `root123`

Sumber data dashboard dimuat ke SQLite (`students.db`, tabel `students`) karena
Metabase tidak dapat membaca CSV secara langsung:

```bash
python load_dashboard_db.py        # data_dashboard.csv -> students.db
```

Cara menjalankan Metabase beserta file dashboard yang sudah diekspor:

```bash
docker run -d -p 3000:3000 --name metabase \
  -v $(pwd)/metabase.db.mv.db:/metabase.db/metabase.db.mv.db \
  -v $(pwd)/students.db:/data/students.db \
  metabase/metabase
```

Panduan lengkap membangun ulang dashboard dari nol (termasuk SQL setiap
question) ada di **`METABASE_SETUP.md`**.

Screenshot dashboard tersedia pada berkas `Georgius_bintang-dashboard.png`.

## Menjalankan Sistem Machine Learning

Prototype sistem machine learning dibuat dengan Streamlit. Pengguna mengisi data siswa (akademik, finansial, demografi), lalu sistem menampilkan **probabilitas dropout** beserta kategori risiko (rendah / sedang / tinggi) dan rekomendasi tindak lanjut.

**Menjalankan secara lokal:**

```bash
streamlit run app.py
```

**Akses prototype (Streamlit Community Cloud):**

🔗 **[https://jaya-jaya-institut-dropout-edsmhdagm34fs4fbyj3p9d.streamlit.app](https://jaya-jaya-institut-dropout-edsmhdagm34fs4fbyj3p9d.streamlit.app)**

Repository: [github.com/Bins777/jaya-jaya-institut-dropout](https://github.com/Bins777/jaya-jaya-institut-dropout)

Cara memakai: isi data siswa pada tab **Akademik / Finansial / Demografi**,
lalu tekan **Prediksi Risiko Dropout**. Contoh kasus risiko tinggi — tunggakan
biaya `Yes`, biaya kuliah lancar `No`, SKS lulus semester 1–2 = 1, nilai 6–7 →
probabilitas dropout **99,8 % (🔴 RISIKO TINGGI)**.

Model yang digunakan: **Logistic Regression** (pipeline dengan StandardScaler), dipilih setelah dibandingkan dengan Random Forest melalui 5-fold cross-validation.

| Metrik (test set) | Nilai |
|---|---|
| Accuracy | 94,2% |
| Precision | 93,2% |
| Recall | 91,9% |
| F1-score | 92,6% |
| ROC-AUC | 0,973 |

## Conclusion

1. Tingkat dropout Jaya Jaya Institut mencapai **32,1%** — hampir 1 dari 3 siswa tidak menyelesaikan pendidikannya.
2. Faktor terkuat yang memengaruhi dropout adalah **performa akademik semester awal** (jumlah SKS lulus dan nilai semester 1–2 — siswa dropout rata-rata hanya lulus 1,9 SKS di semester 2 vs 6,2 SKS pada graduate) dan **faktor finansial**: siswa yang menunggak biaya kuliah dropout **86,6%** vs 24,7% yang lancar, debtor dropout 62%, sedangkan penerima beasiswa hanya 12,2%.
3. Faktor demografi juga berpengaruh: siswa laki-laki (45,1% vs 25,1%) dan siswa yang mendaftar pada usia **25+ tahun** (>51%) lebih berisiko, serta dropout terkonsentrasi pada program studi tertentu.
4. Model **Logistic Regression** mampu memprediksi dropout dengan accuracy 94,2%, recall 91,9%, dan ROC-AUC 0,973 — recall tinggi berarti ±92 dari 100 siswa yang benar-benar berisiko berhasil terdeteksi sejak dini.
5. Dengan kombinasi model prediksi (deteksi dini) dan dashboard monitoring, Jaya Jaya Institut dapat beralih dari penanganan **reaktif** menjadi **proaktif** — siswa berisiko teridentifikasi sejak semester 1–2, sebelum benar-benar berhenti.

## Rekomendasi Action Items

1. **Bangun early-warning system berbasis model** — jalankan skor risiko untuk seluruh siswa aktif setiap akhir semester; siswa dengan skor > 0,6 otomatis masuk daftar prioritas bimbingan khusus (academic advising + konseling).
2. **Intervensi finansial proaktif** — hubungi siswa yang mulai menunggak biaya kuliah sebelum tunggakan menumpuk (kelompok ini dropout 86,6%); tawarkan skema cicilan dan perluas program beasiswa, karena penerima beasiswa dropout 3× lebih jarang.
3. **Program remedial semester awal** — wajibkan academic advising dan kelas remedial bagi siswa yang lulus < 3 SKS pada semester 1, karena SKS lulus semester 1–2 adalah prediktor dropout terkuat.
4. **Audit program studi berisiko tinggi** — evaluasi kurikulum, beban studi, dan dukungan pengajaran pada program dengan dropout > 45% (Biofuel Production Tech, Equinculture, Informatics Engineering, Management kelas malam).
5. **Dukungan untuk siswa dewasa dan kelas malam** — sediakan jadwal fleksibel, kelas hybrid, dan layanan konseling khusus bagi siswa usia 25+ yang umumnya bekerja sambil kuliah.
6. **Monitoring rutin melalui dashboard Metabase** — tinjau KPI dropout rate per program studi, status pembayaran, dan distribusi skor risiko setiap bulan pada rapat manajemen akademik.
