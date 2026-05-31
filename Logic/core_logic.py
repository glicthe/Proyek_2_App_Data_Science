"""
=============================================================
Logic/core_logic.py
Mesin logika pemrosesan hasil deteksi YOLO untuk sistem ADAS
=============================================================
Tanggung jawab file ini:
  1. Estimasi jarak ke rambu menggunakan metode pin-hole camera
  2. Evaluasi hasil deteksi YOLO menjadi status + notifikasi UI
  3. Menentukan apakah audio alert harus dibunyikan
  4. Mendeteksi pelanggaran batas kecepatan secara real-time

Cara pakai dari UI/app.py:
  import sys, os
  sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Logic'))
  from core_logic import evaluasi_deteksi, estimasi_jarak, EvaluasiHasil
=============================================================
"""

import sys
import os
from dataclasses import dataclass, field
from typing import Optional

# Pastikan folder Logic/ bisa diimpor dari mana saja
sys.path.insert(0, os.path.dirname(__file__))
from config_rambu import KONFIGURASI_RAMBU, WARNA_STATUS, IKON_STATUS


# ==============================================================
# KONSTANTA KALIBRASI KAMERA
# Nilai ini harus disesuaikan dengan spesifikasi kamera dashcam
# yang digunakan tim saat rekaman dataset.
# ==============================================================

# Tinggi rambu lalu lintas standar Indonesia (meter)
# Referensi: Permenhub No. 13 Tahun 2014 — rambu jalan ~60 cm
TINGGI_RAMBU_NYATA_M: float = 0.60

# Focal length kamera dalam satuan piksel.
# Diturunkan dari: f_piksel = (f_mm / sensor_height_mm) * resolusi_vertikal
# Asumsi dashcam 1080p dengan focal length ~3.6 mm, sensor 1/2.9":
#   sensor_h = 2.88 mm → f_piksel = (3.6 / 2.88) * 1080 ≈ 1350
# CATATAN: Nilai ini adalah estimasi empiris.
#          Kalibrasi ulang menggunakan checkerboard untuk akurasi tinggi.
FOCAL_LENGTH_PIKSEL: float = 1350.0

# Jarak minimum (meter) di mana sistem mulai memberikan peringatan dini
JARAK_PERINGATAN_DINI_M: float = 30.0

# Jarak kritis (meter) — peringatan prioritas tinggi
JARAK_KRITIS_M: float = 10.0


# ==============================================================
# DATA CLASS — Struktur kembalian fungsi evaluasi
# Memudahkan UI/app.py membaca hasil tanpa parsing string
# ==============================================================

@dataclass
class EvaluasiHasil:
    """
    Objek hasil evaluasi satu deteksi YOLO.
    Semua field ini langsung bisa dipakai oleh UI/app.py.
    """
    # Nama kelas rambu yang terdeteksi
    nama_kelas      : str

    # Status akhir: 'Aman' | 'Info' | 'Peringatan' | 'Larangan' | 'Pelanggaran'
    status          : str

    # Pesan notifikasi untuk ditampilkan ke pengemudi
    pesan           : str

    # Apakah sistem harus membunyikan audio/TTS?
    play_audio      : bool

    # Estimasi jarak ke rambu dalam meter (None jika bbox tidak tersedia)
    jarak_meter     : Optional[float]

    # Kategori rambu dari config_rambu.py
    kategori        : str

    # Warna CSS untuk panel notifikasi di app.py
    warna_css       : str

    # Ikon teks untuk tampilan panel
    ikon            : str

    # Informasi tambahan batas kecepatan (hanya untuk speed_limit)
    batas_kecepatan : Optional[int] = None

    # Selisih kecepatan jika over-speeding (km/jam di atas batas)
    selisih_kecepatan: Optional[float] = None

    def __str__(self) -> str:
        """Representasi ringkas untuk logging dan terminal."""
        jarak_str = f"{self.jarak_meter:.1f} m" if self.jarak_meter else "N/A"
        audio_str = "🔊 AUDIO" if self.play_audio else "🔇 silent"
        return (
            f"[{self.status.upper():12s}] {self.nama_kelas:<40s} "
            f"| Jarak: {jarak_str:>8s} "
            f"| {audio_str} "
            f"| {self.pesan}"
        )


# ==============================================================
# 1. ESTIMASI JARAK — Pin-hole Camera Approximation
# ==============================================================

def estimasi_jarak(
    bbox_height  : float,
    frame_height : float,
    tinggi_rambu : float = TINGGI_RAMBU_NYATA_M,
    focal_length : float = FOCAL_LENGTH_PIKSEL,
) -> Optional[float]:
    """
    Estimasi jarak dari kamera ke rambu menggunakan rumus pin-hole camera.

    Rumus:
        Jarak (m) = (Tinggi_Nyata (m) × Focal_Length (px)) / Tinggi_BBox (px)

    Sumber rumus:
        Derived from the similar-triangles property of the thin lens model.
        Referensi: Bradski & Kaehler, "Learning OpenCV", Chapter 11.

    Args:
        bbox_height  : Tinggi bounding box hasil deteksi YOLO dalam piksel.
        frame_height : Tinggi total frame video dalam piksel (misal: 720, 1080).
        tinggi_rambu : Tinggi nyata objek rambu dalam meter (default: 0.60 m).
        focal_length : Focal length kamera dalam piksel (default: 1350 px).

    Returns:
        Jarak dalam meter (float), atau None jika input tidak valid.

    Catatan keterbatasan:
        - Akurasi bergantung pada kalibrasi focal_length yang tepat.
        - Tidak memperhitungkan distorsi lensa (barrel/pincushion).
        - Asumsi: rambu tegak lurus terhadap sumbu optik kamera.
        - Untuk akurasi produksi, gunakan kalibrasi kamera dengan checkerboard
          (cv2.calibrateCamera) untuk mendapatkan f_x, f_y yang akurat.
    """
    # Validasi: bbox_height harus positif dan tidak nol
    if bbox_height is None or bbox_height <= 0:
        return None

    # Validasi: bbox tidak boleh lebih besar dari frame itu sendiri
    if frame_height is not None and bbox_height > frame_height:
        return None

    # Rumus pin-hole: Z = (H_nyata × f) / h_piksel
    jarak = (tinggi_rambu * focal_length) / bbox_height
    return round(jarak, 2)


# ==============================================================
# 2. HELPER — Kategori → Status UI
# ==============================================================

def _kategori_ke_status(kategori: str) -> str:
    """
    Konversi kategori dari config_rambu ke status tampilan UI.

    Mapping:
        info        → 'Info'
        bahaya      → 'Peringatan'
        larangan    → 'Larangan'
        speed_limit → 'Info' (default; bisa diubah menjadi 'Pelanggaran'
                               oleh evaluasi_deteksi jika over-speeding)
    """
    mapping = {
        "info"       : "Info",
        "bahaya"     : "Peringatan",
        "larangan"   : "Larangan",
        "speed_limit": "Info",   # dioverride jika over-speeding
    }
    return mapping.get(kategori, "Info")


# ==============================================================
# 3. EVALUASI DETEKSI — Fungsi Utama Rule Engine
# ==============================================================

def evaluasi_deteksi(
    nama_kelas          : str,
    bbox_height         : Optional[float] = None,
    frame_height        : Optional[float] = None,
    kecepatan_kendaraan : float           = 0.0,
) -> EvaluasiHasil:
    """
    Evaluasi satu objek hasil deteksi YOLO dan kembalikan respons lengkap.

    Args:
        nama_kelas          : Nama kelas rambu (harus sesuai KONFIGURASI_RAMBU).
        bbox_height         : Tinggi bounding box deteksi dalam piksel.
                              Kirim None jika tidak tersedia (mode gambar statis).
        frame_height        : Tinggi total frame dalam piksel.
                              Kirim None jika tidak diketahui.
        kecepatan_kendaraan : Kecepatan kendaraan saat ini dalam km/jam
                              (dari slider di UI/app.py).

    Returns:
        EvaluasiHasil: Objek berisi semua data yang dibutuhkan oleh UI/app.py.

    Logika utama:
        1. Lookup data kelas dari KONFIGURASI_RAMBU.
        2. Hitung estimasi jarak jika bbox tersedia.
        3. Jika kategori speed_limit:
           a. Bandingkan kecepatan_kendaraan dengan batas_kecepatan.
           b. Jika melanggar → status 'Pelanggaran', play_audio = True.
           c. Jika patuh    → status 'Info', play_audio = False.
        4. Untuk kategori lain, gunakan status dan play_audio dari config.
        5. Tambahkan konteks jarak ke pesan jika jarak berhasil dihitung.
    """

    # ----------------------------------------------------------
    # LANGKAH 1: Validasi & lookup data kelas
    # ----------------------------------------------------------
    if nama_kelas not in KONFIGURASI_RAMBU:
        # Kelas tidak dikenali — kembalikan hasil default aman
        return EvaluasiHasil(
            nama_kelas       = nama_kelas,
            status           = "Info",
            pesan            = f"Kelas '{nama_kelas}' tidak dikenali dalam database rambu.",
            play_audio       = False,
            jarak_meter      = None,
            kategori         = "unknown",
            warna_css        = WARNA_STATUS.get("Info", "notif-ok"),
            ikon             = IKON_STATUS.get("Info", "ℹ️"),
        )

    # Ambil konfigurasi dari kamus
    cfg = KONFIGURASI_RAMBU[nama_kelas]
    kategori        = cfg["kategori"]
    pesan_dasar     = cfg["pesan"]
    play_audio      = cfg["play_audio"]
    batas_kecepatan = cfg.get("batas_kecepatan")

    # ----------------------------------------------------------
    # LANGKAH 2: Estimasi jarak
    # ----------------------------------------------------------
    jarak_meter = estimasi_jarak(bbox_height, frame_height)

    # Tambahkan info jarak ke pesan jika berhasil dihitung
    pesan = pesan_dasar
    if jarak_meter is not None:
        if jarak_meter <= JARAK_KRITIS_M:
            # Rambu sangat dekat — eskalasi urgensi pesan
            pesan = f"[⚠ DEKAT: {jarak_meter} m] {pesan_dasar}"
        else:
            pesan = f"[Jarak: ~{jarak_meter} m] {pesan_dasar}"

    # ----------------------------------------------------------
    # LANGKAH 3: Logika khusus untuk rambu batas kecepatan
    # ----------------------------------------------------------
    status           = _kategori_ke_status(kategori)
    selisih_kecepatan: Optional[float] = None

    if kategori == "speed_limit" and batas_kecepatan is not None:

        if kecepatan_kendaraan > batas_kecepatan:
            # ── OVER-SPEEDING TERDETEKSI ──────────────────────────────────
            selisih_kecepatan = round(kecepatan_kendaraan - batas_kecepatan, 1)

            status     = "Pelanggaran"
            play_audio = True   # override config — HARUS berbunyi

            jarak_info = f" (jarak: ~{jarak_meter} m)" if jarak_meter else ""
            pesan = (
                f"🚨 BAHAYA! Anda melaju {kecepatan_kendaraan:.0f} km/jam "
                f"di zona batas {batas_kecepatan} km/jam{jarak_info}. "
                f"Kurangi kecepatan segera! ({selisih_kecepatan} km/jam di atas batas)"
            )
        else:
            # ── KECEPATAN PATUH ───────────────────────────────────────────
            status     = "Info"
            play_audio = False  # tidak perlu bunyikan audio

            sisa_batas = batas_kecepatan - kecepatan_kendaraan
            jarak_info = f" | Jarak: ~{jarak_meter} m" if jarak_meter else ""

            if sisa_batas == 0:
                # Tepat di batas — aman tapi tidak ada toleransi
                pesan = (
                    f"✅ Zona batas {batas_kecepatan} km/jam. "
                    f"Kecepatan Anda tepat di batas ({kecepatan_kendaraan:.0f} km/jam). "
                    f"Pertahankan{jarak_info}."
                )
            else:
                pesan = (
                    f"✅ Zona batas {batas_kecepatan} km/jam. "
                    f"Kecepatan Anda: {kecepatan_kendaraan:.0f} km/jam "
                    f"(toleransi {sisa_batas:.0f} km/jam{jarak_info})."
                )

    # ----------------------------------------------------------
    # LANGKAH 4: Bangun dan kembalikan objek hasil
    # ----------------------------------------------------------
    return EvaluasiHasil(
        nama_kelas        = nama_kelas,
        status            = status,
        pesan             = pesan,
        play_audio        = play_audio,
        jarak_meter       = jarak_meter,
        kategori          = kategori,
        warna_css         = WARNA_STATUS.get(status, "notif-ok"),
        ikon              = IKON_STATUS.get(status, "ℹ️"),
        batas_kecepatan   = batas_kecepatan,
        selisih_kecepatan = selisih_kecepatan,
    )


# ==============================================================
# 4. FUNGSI BATCH — Proses banyak deteksi dalam satu frame
# ==============================================================

def evaluasi_batch(
    deteksi_list        : list[dict],
    frame_height        : Optional[float] = None,
    kecepatan_kendaraan : float           = 0.0,
) -> list[EvaluasiHasil]:
    """
    Evaluasi semua objek yang terdeteksi dalam satu frame sekaligus.

    Args:
        deteksi_list: List dictionary hasil dari YOLO, format tiap item:
            {
                "class_name" : str,   # nama kelas
                "bbox"       : list,  # [x1, y1, x2, y2] dalam piksel
                "confidence" : float  # skor keyakinan YOLO (0.0–1.0)
            }
        frame_height        : Tinggi frame dalam piksel.
        kecepatan_kendaraan : Kecepatan kendaraan saat ini (km/jam).

    Returns:
        List EvaluasiHasil, diurutkan dari prioritas tertinggi ke terendah.
        Urutan prioritas: Pelanggaran > Larangan > Peringatan > Info.
    """
    URUTAN_PRIORITAS = {
        "Pelanggaran": 0,
        "Larangan"   : 1,
        "Peringatan" : 2,
        "Info"       : 3,
        "Aman"       : 4,
    }

    hasil_list: list[EvaluasiHasil] = []

    for det in deteksi_list:
        nama_kelas = det.get("class_name", "")
        bbox       = det.get("bbox", [])   # [x1, y1, x2, y2]

        # Hitung tinggi bounding box dari koordinat YOLO
        if len(bbox) == 4:
            bbox_height = abs(bbox[3] - bbox[1])  # y2 - y1
        else:
            bbox_height = None

        hasil = evaluasi_deteksi(
            nama_kelas          = nama_kelas,
            bbox_height         = bbox_height,
            frame_height        = frame_height,
            kecepatan_kendaraan = kecepatan_kendaraan,
        )
        hasil_list.append(hasil)

    # Urutkan: status dengan prioritas tertinggi muncul pertama
    hasil_list.sort(key=lambda h: URUTAN_PRIORITAS.get(h.status, 99))
    return hasil_list


def ambil_prioritas_tertinggi(
    deteksi_list        : list[dict],
    frame_height        : Optional[float] = None,
    kecepatan_kendaraan : float           = 0.0,
) -> Optional[EvaluasiHasil]:
    """
    Shortcut — kembalikan HANYA satu hasil dengan prioritas tertinggi.
    Cocok untuk panel notifikasi tunggal di UI/app.py.

    Returns:
        EvaluasiHasil dengan urgensi tertinggi, atau None jika list kosong.
    """
    hasil = evaluasi_batch(deteksi_list, frame_height, kecepatan_kendaraan)
    return hasil[0] if hasil else None


# ==============================================================
# 5. BLOK PENGUJIAN MANDIRI
# Jalankan: python Logic/core_logic.py
# ==============================================================

if __name__ == "__main__":

    # ── Konfigurasi tampilan terminal ──────────────────────────
    SEP  = "=" * 75
    SEP2 = "-" * 75

    print(SEP)
    print("  SMART ADAS — Pengujian Mandiri core_logic.py")
    print("  Kelompok 6 | Proyek Tugas Akhir")
    print(SEP)

    # ==========================================================
    # TEST 1: Estimasi Jarak
    # ==========================================================
    print("\n📐 TEST 1 — estimasi_jarak()")
    print(SEP2)

    kasus_jarak = [
        # (bbox_height_px, frame_height_px, deskripsi)
        (200, 1080, "Rambu dekat (~4 m, bbox besar)"),
        (80 ,  720, "Rambu sedang (~10 m)"),
        (30 ,  720, "Rambu jauh (~27 m)"),
        (10 ,  720, "Rambu sangat jauh (~81 m)"),
        (0  ,  720, "bbox_height nol → harus None"),
        (None, 720, "bbox_height None → harus None"),
        (900, 720,  "bbox lebih besar dari frame → harus None"),
    ]

    for bh, fh, desc in kasus_jarak:
        hasil_jarak = estimasi_jarak(bh, fh)
        jarak_str = f"{hasil_jarak} m" if hasil_jarak is not None else "None (tidak valid)"
        print(f"  bbox={str(bh):>5} px | frame={fh} px → {jarak_str:>12s}  | {desc}")

    # ==========================================================
    # TEST 2: Evaluasi kelas INFO
    # ==========================================================
    print(f"\n🟢 TEST 2 — Kategori INFO (tidak memicu audio)")
    print(SEP2)

    kelas_info = ["Masjid", "Pom Bensin", "Rumah Sakit", "Tempat Parkir"]
    for kelas in kelas_info:
        h = evaluasi_deteksi(kelas, bbox_height=60, frame_height=720, kecepatan_kendaraan=50)
        audio = "✅ BENAR (False)" if not h.play_audio else "❌ SALAH (harusnya False)"
        print(f"  {kelas:<35s} | audio={audio} | status={h.status}")

    # ==========================================================
    # TEST 3: Evaluasi kelas BAHAYA
    # ==========================================================
    print(f"\n🟡 TEST 3 — Kategori BAHAYA (harus memicu audio)")
    print(SEP2)

    kelas_bahaya = ["Polisi Tidur", "Peringatan Perlintasan Kereta Api",
                    "Banyak Anak-Anak", "Hati-Hati"]
    for kelas in kelas_bahaya:
        h = evaluasi_deteksi(kelas, bbox_height=80, frame_height=720, kecepatan_kendaraan=60)
        audio = "✅ BENAR (True)" if h.play_audio else "❌ SALAH (harusnya True)"
        print(f"  {kelas:<42s} | audio={audio} | status={h.status}")

    # ==========================================================
    # TEST 4: Evaluasi kelas LARANGAN
    # ==========================================================
    print(f"\n🔴 TEST 4 — Kategori LARANGAN (harus memicu audio)")
    print(SEP2)

    kelas_larangan = ["Berhenti", "Dilarang Masuk", "Dilarang Mendahului",
                      "Dilarang Parkir"]
    for kelas in kelas_larangan:
        h = evaluasi_deteksi(kelas, bbox_height=100, frame_height=720, kecepatan_kendaraan=40)
        audio = "✅ BENAR (True)" if h.play_audio else "❌ SALAH (harusnya True)"
        print(f"  {kelas:<35s} | audio={audio} | status={h.status}")

    # ==========================================================
    # TEST 5: Over-speeding — berbagai skenario
    # ==========================================================
    print(f"\n🚨 TEST 5 — Logika Over-speeding (speed_limit)")
    print(SEP2)

    skenario_speed = [
        # (nama_kelas,               bbox, kecepatan, ekspektasi_status)
        ("Kecepatan Maks. 30 km",   90,  25,  "Info        ← patuh"),
        ("Kecepatan Maks. 30 km",   90,  30,  "Info        ← tepat di batas"),
        ("Kecepatan Maks. 30 km",   90,  55,  "Pelanggaran ← +25 km/jam"),
        ("Kecepatan Maks. 60 km",   70,  58,  "Info        ← harusnya KeyError (kelas tidak ada)"),
        ("Kecepatan Maks. 80 km",   60,  95,  "Pelanggaran ← +15 km/jam"),
        ("Kecepatan Maks. 100 km",  40, 100,  "Info        ← tepat di batas"),
        ("Kecepatan Maks. 120 km",  30, 145,  "Pelanggaran ← +25 km/jam"),
    ]

    for kelas, bh, kec, keterangan in skenario_speed:
        h = evaluasi_deteksi(kelas, bbox_height=bh, frame_height=720,
                             kecepatan_kendaraan=kec)
        audio_mark = "🔊" if h.play_audio else "🔇"
        print(f"\n  Rambu  : {kelas}")
        print(f"  Kecepatan kendaraan : {kec} km/jam")
        print(f"  Status : {h.status} {audio_mark}  | {keterangan}")
        if h.selisih_kecepatan:
            print(f"  Selisih: +{h.selisih_kecepatan} km/jam di atas batas")
        print(f"  Pesan  : {h.pesan}")

    # ==========================================================
    # TEST 6: Evaluasi Batch (simulasi multi-deteksi 1 frame)
    # ==========================================================
    print(f"\n\n📦 TEST 6 — evaluasi_batch() (3 deteksi dalam 1 frame)")
    print(SEP2)

    deteksi_simulasi = [
        {"class_name": "Kecepatan Maks. 80 km", "bbox": [100, 200, 200, 280], "confidence": 0.91},
        {"class_name": "Polisi Tidur",           "bbox": [300, 150, 420, 230], "confidence": 0.87},
        {"class_name": "Pom Bensin",             "bbox": [500, 100, 600, 180], "confidence": 0.76},
    ]

    batch_hasil = evaluasi_batch(deteksi_simulasi, frame_height=720, kecepatan_kendaraan=110)
    for i, h in enumerate(batch_hasil, 1):
        print(f"\n  [{i}] {h}")

    prioritas = ambil_prioritas_tertinggi(deteksi_simulasi, 720, 110)
    print(f"\n  ► Prioritas tertinggi untuk ditampilkan di UI:")
    print(f"    {prioritas.ikon}  {prioritas.status} — {prioritas.pesan}")

    # ==========================================================
    # TEST 7: Kelas tidak dikenali
    # ==========================================================
    print(f"\n\n❓ TEST 7 — Kelas tidak dikenali")
    print(SEP2)

    h_unknown = evaluasi_deteksi("Rambu Hantu", bbox_height=50, frame_height=720)
    print(f"  Kelas  : {h_unknown.nama_kelas}")
    print(f"  Status : {h_unknown.status}")
    print(f"  Pesan  : {h_unknown.pesan}")
    print(f"  Audio  : {h_unknown.play_audio}")

    # ==========================================================
    # RINGKASAN
    # ==========================================================
    print(f"\n{SEP}")
    print("  Semua pengujian selesai. Periksa hasil di atas.")
    print(f"  Total kelas terkonfigurasi: {len(KONFIGURASI_RAMBU)} kelas rambu")
    print(SEP)
