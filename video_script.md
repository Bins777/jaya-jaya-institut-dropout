# Script Video Submission — Target durasi baca ±1:50

> ±245 kata. Dibaca santai dengan jeda natural ≈ 1 menit 50 detik narasi.
> (Kalau ditambah jeda demo layar, total video tetap aman di bawah 3 menit.)
> Tampilan layar per bagian ada di kolom [LAYAR].

---

**[0:00–0:15] — Intro** · [LAYAR: slide judul / README]

Halo, saya Georgius Bintang. Di proyek ini saya membantu Jaya Jaya Institut menangani masalah dropout siswa. Dari 4.424 siswa, 32 persen — hampir satu dari tiga — tidak menyelesaikan pendidikannya.

**[0:15–0:55] — Solusi Machine Learning** · [LAYAR: notebook → scroll EDA → app Streamlit, demo 1 prediksi]

Dari hasil analisis, faktor terkuat dropout ternyata performa akademik semester awal dan kondisi finansial. Siswa yang menunggak biaya kuliah dropout rate-nya 86 persen, dan siswa dropout rata-rata cuma lulus dua SKS di semester dua.

Untuk deteksi dini, saya melatih model machine learning — Logistic Regression, yang menang dibanding Random Forest — dengan accuracy 94 persen, recall 92 persen, dan ROC-AUC 0,97. Model ini saya kemas jadi prototype Streamlit yang sudah di-deploy ke Streamlit Community Cloud. Tinggal isi data akademik, finansial, dan demografi siswa — sistem langsung menampilkan probabilitas dropout beserta kategori risikonya dan rekomendasi tindak lanjut.

**[0:55–1:30] — Dashboard** · [LAYAR: dashboard Metabase, tunjuk tiap chart]

Selain itu, saya membuat dashboard monitoring di Metabase. Di sini manajemen bisa melihat KPI dropout, dropout rate per program studi — tertinggi di Biofuel Production Technologies, 67 persen — perbandingan faktor finansial seperti tunggakan dan beasiswa, sampai daftar siswa aktif dengan risk score di atas 0,6 yang perlu diprioritaskan untuk bimbingan khusus.

**[1:30–1:50] — Conclusion** · [LAYAR: bagian Conclusion + Action Items di README]

Kesimpulannya: dropout di Jaya Jaya Institut bisa dideteksi sejak semester satu. Dengan early-warning system ini plus intervensi finansial dan program remedial, institusi bisa berubah dari reaktif menjadi proaktif dalam menyelamatkan siswanya. Terima kasih.

---

## Tips rekaman

- Baca dengan kecepatan normal-santai; kalau selesai di bawah 1:45, tahan 1–2 detik ekstra saat demo klik prediksi di Streamlit.
- Simpan hasil rekaman sebagai `Georgius_bintang-video.mp4` di folder submission.
- Resolusi 720p cukup, ukuran file kecil (reviewer minta "ukuran masuk akal").
