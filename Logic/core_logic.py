"""
=============================================================
Logic/core_logic.py  [v2 — Context-Aware Warnings]
Mesin logika pemrosesan hasil deteksi YOLO untuk sistem ADAS
=============================================================
PERUBAHAN v2 vs v1:
  evaluasi_deteksi() sekarang membaca dua field baru dari config:

  1. Kategori BAHAYA — field 'kecepatan_aman_kmh':
       kecepatan > kecepatan_aman_kmh
           → status "Peringatan", pesan eskalasi, play_audio = True
       kecepatan ≤ kecepatan_aman_kmh
           → status "Info", pesan informatif, play_audio = False

  2. Kategori LARANGAN — field 'jenis_larangan':
       'parkir_berhenti' + kecepatan == 0
           → status "Pelanggaran", play_audio = True
             (kendaraan diam di tempat terlarang parkir/berhenti)
       'parkir_berhenti' + kecepatan > 0
           → status "Info", play_audio = False
             (kendaraan sedang melintas — tidak relevan)
       'melintas' + kecepatan > 0
           → status "Pelanggaran", play_audio = True
             (kendaraan masuk/melewati jalan terlarang)
       'melintas' + kecepatan == 0
           → status "Info", play_audio = False
             (kendaraan diam — belum melintas, belum melanggar)

  Kategori INFO dan SPEED_LIMIT: logika tidak berubah dari v1.
  Struktur EvaluasiHasil: tidak berubah — kompatibel penuh dengan UI.
=============================================================
"""

import sys
import os
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from config_rambu import KONFIGURASI_RAMBU, WARNA_STATUS, IKON_STATUS


# ==============================================================
# KONSTANTA KALIBRASI KAMERA
# ==============================================================

TINGGI_RAMBU_NYATA_M    : float = 0.60
FOCAL_LENGTH_PIKSEL     : float = 1350.0
JARAK_PERINGATAN_DINI_M : float = 30.0
JARAK_KRITIS_M          : float = 10.0


# ==============================================================
# DATA CLASS — Struktur kembalian fungsi evaluasi
# Tidak ada perubahan dari v1 — kompatibel penuh dengan UI/app.py
# ==============================================================

@dataclass
class EvaluasiHasil:
    nama_kelas        : str
    status            : str
    pesan             : str
    play_audio        : bool
    jarak_meter       : Optional[float]
    kategori          : str
    warna_css         : str
    ikon              : str
    batas_kecepatan   : Optional[int]   = None
    selisih_kecepatan : Optional[float] = None

    def __str__(self) -> str:
        jarak_str = f"{self.jarak_meter:.1f} m" if self.jarak_meter else "N/A"
        audio_str = "🔊 AUDIO" if self.play_audio else "🔇 silent"
        return (
            f"[{self.status.upper():12s}] {self.nama_kelas:<40s} "
            f"| Jarak: {jarak_str:>8s} "
            f"| {audio_str} "
            f"| {self.pesan}"
        )


# ==============================================================
# 1. ESTIMASI JARAK — Pin-hole Camera (tidak berubah dari v1)
# ==============================================================

def estimasi_jarak(
    bbox_height  : float,
    frame_height : float,
    tinggi_rambu : float = TINGGI_RAMBU_NYATA_M,
    focal_length : float = FOCAL_LENGTH_PIKSEL,
) -> Optional[float]:
    if bbox_height is None or bbox_height <= 0:
        return None
    if frame_height is not None and bbox_height > frame_height:
        return None
    return round((tinggi_rambu * focal_length) / bbox_height, 2)


# ==============================================================
# 2. HELPER — Format info jarak untuk pesan
# ==============================================================

def _info_jarak(jarak_meter: Optional[float]) -> str:
    """Kembalikan string ' | Jarak: ~X.X m' atau '' jika None."""
    return f" | Jarak: ~{jarak_meter} m" if jarak_meter else ""


def _prefix_jarak(jarak_meter: Optional[float]) -> str:
    """Kembalikan prefix '[⚠ DEKAT: X m] ' atau '[Jarak: ~X m] ' atau ''."""
    if jarak_meter is None:
        return ""
    if jarak_meter <= JARAK_KRITIS_M:
        return f"[⚠ DEKAT: {jarak_meter} m] "
    return f"[Jarak: ~{jarak_meter} m] "


# ==============================================================
# 3. EVALUASI DETEKSI — Fungsi Utama Rule Engine  [v2]
# ==============================================================

def evaluasi_deteksi(
    nama_kelas          : str,
    bbox_height         : Optional[float] = None,
    frame_height        : Optional[float] = None,
    kecepatan_kendaraan : float           = 0.0,
) -> EvaluasiHasil:
    """
    Evaluasi satu deteksi YOLO dengan logika konteks kecepatan (v2).

    Tiga cabang utama berdasarkan kategori rambu:

    ┌─────────────┬─────────────────────────────────────────────────────┐
    │ info        │ Selalu Info, play_audio selalu False.               │
    ├─────────────┼─────────────────────────────────────────────────────┤
    │ bahaya      │ Bandingkan kecepatan vs kecepatan_aman_kmh.         │
    │             │   > threshold → Peringatan + audio ON              │
    │             │   ≤ threshold → Info + audio OFF                   │
    ├─────────────┼─────────────────────────────────────────────────────┤
    │ larangan    │ Cek jenis_larangan + kecepatan.                     │
    │             │   parkir_berhenti + kecepatan==0 → Pelanggaran ON  │
    │             │   parkir_berhenti + kecepatan>0  → Info OFF        │
    │             │   melintas       + kecepatan>0   → Pelanggaran ON  │
    │             │   melintas       + kecepatan==0  → Info OFF        │
    ├─────────────┼─────────────────────────────────────────────────────┤
    │ speed_limit │ Bandingkan kecepatan vs batas_kecepatan.            │
    │             │   > batas → Pelanggaran + audio ON                 │
    │             │   ≤ batas → Info + audio OFF                       │
    └─────────────┴─────────────────────────────────────────────────────┘

    Args:
        nama_kelas          : Nama kelas dari YOLO (harus ada di KONFIGURASI_RAMBU).
        bbox_height         : Tinggi bbox dalam piksel (None = gambar statis).
        frame_height        : Tinggi frame dalam piksel.
        kecepatan_kendaraan : Kecepatan saat ini dalam km/jam (dari st.slider).

    Returns:
        EvaluasiHasil — kompatibel penuh dengan UI/app.py v1.
    """

    # ── Fallback: kelas tidak dikenali ──────────────────────────────────────
    if nama_kelas not in KONFIGURASI_RAMBU:
        return EvaluasiHasil(
            nama_kelas       = nama_kelas,
            status           = "Info",
            pesan            = f"Kelas '{nama_kelas}' tidak dikenali dalam database rambu.",
            play_audio       = False,
            jarak_meter      = None,
            kategori         = "unknown",
            warna_css        = WARNA_STATUS["Info"],
            ikon             = IKON_STATUS["Info"],
        )

    cfg      = KONFIGURASI_RAMBU[nama_kelas]
    kategori = cfg["kategori"]

    # ── Estimasi jarak ───────────────────────────────────────────────────────
    jarak_meter = estimasi_jarak(bbox_height, frame_height)
    prefix      = _prefix_jarak(jarak_meter)

    # ── Nilai default (akan dioverride tiap cabang) ──────────────────────────
    status     : str  = "Info"
    pesan      : str  = cfg["pesan"]
    play_audio : bool = False
    batas_kec  : Optional[int]   = cfg.get("batas_kecepatan")
    selisih    : Optional[float] = None

    # ════════════════════════════════════════════════════════════════════════
    # CABANG 1: INFO — tidak ada logika dinamis
    # ════════════════════════════════════════════════════════════════════════
    if kategori == "info":
        status     = "Info"
        play_audio = False
        pesan      = f"{prefix}{cfg['pesan']}"

    # ════════════════════════════════════════════════════════════════════════
    # CABANG 2: BAHAYA — konteks kecepatan vs kecepatan_aman_kmh
    # ════════════════════════════════════════════════════════════════════════
    elif kategori == "bahaya":
        kecepatan_aman = cfg.get("kecepatan_aman_kmh", 50)

        if kecepatan_kendaraan > kecepatan_aman:
            # ── Kendaraan terlalu cepat untuk rambu ini ──────────────────────
            selisih    = round(kecepatan_kendaraan - kecepatan_aman, 1)
            status     = "Peringatan"
            play_audio = True
            pesan = (
                f"{prefix}⚠ KURANGI KECEPATAN! {cfg['pesan']} "
                f"Anda melaju {kecepatan_kendaraan:.0f} km/jam "
                f"(batas aman {kecepatan_aman} km/jam, "
                f"lebih {selisih} km/jam)."
            )
        else:
            # ── Kendaraan sudah cukup pelan — cukup info visual ───────────────
            status     = "Info"
            play_audio = False
            pesan = (
                f"{prefix}{cfg['pesan']} "
                f"Kecepatan Anda {kecepatan_kendaraan:.0f} km/jam "
                f"— sudah sesuai."
            )

    # ════════════════════════════════════════════════════════════════════════
    # CABANG 3: LARANGAN — konteks jenis_larangan vs kecepatan
    # ════════════════════════════════════════════════════════════════════════
    elif kategori == "larangan":
        jenis = cfg.get("jenis_larangan", "melintas")

        if jenis == "parkir_berhenti":
            # Larangan diam: alarm hanya saat kendaraan benar-benar berhenti
            if kecepatan_kendaraan == 0:
                status     = "Pelanggaran"
                play_audio = True
                pesan = (
                    f"{prefix}🚨 PELANGGARAN! {cfg['pesan']} "
                    f"Kendaraan Anda sedang berhenti/parkir di zona terlarang."
                )
            else:
                status     = "Info"
                play_audio = False
                pesan = (
                    f"{prefix}{cfg['pesan']} "
                    f"(Anda sedang melintas — tidak relevan.)"
                )

        elif jenis == "melintas":
            # Larangan bergerak: alarm hanya saat kendaraan masih melaju
            if kecepatan_kendaraan > 0:
                status     = "Pelanggaran"
                play_audio = True
                pesan = (
                    f"{prefix}🚨 PELANGGARAN! {cfg['pesan']} "
                    f"Kendaraan Anda melaju {kecepatan_kendaraan:.0f} km/jam "
                    f"di zona ini."
                )
            else:
                status     = "Info"
                play_audio = False
                pesan = (
                    f"{prefix}{cfg['pesan']} "
                    f"(Kendaraan diam — belum melintas.)"
                )

        else:
            # jenis_larangan tidak dikenali — fallback aman
            status     = "Info"
            play_audio = False
            pesan      = f"{prefix}{cfg['pesan']}"

    # ════════════════════════════════════════════════════════════════════════
    # CABANG 4: SPEED_LIMIT — tidak berubah dari v1
    # ════════════════════════════════════════════════════════════════════════
    elif kategori == "speed_limit":
        if batas_kec is not None:
            if kecepatan_kendaraan > batas_kec:
                selisih    = round(kecepatan_kendaraan - batas_kec, 1)
                status     = "Pelanggaran"
                play_audio = True
                pesan = (
                    f"🚨 BAHAYA! Anda melaju {kecepatan_kendaraan:.0f} km/jam "
                    f"di zona batas {batas_kec} km/jam"
                    f"{_info_jarak(jarak_meter)}. "
                    f"Kurangi kecepatan! ({selisih} km/jam di atas batas)"
                )
            else:
                sisa = batas_kec - kecepatan_kendaraan
                status     = "Info"
                play_audio = False
                if sisa == 0:
                    pesan = (
                        f"✅ Zona batas {batas_kec} km/jam. "
                        f"Kecepatan tepat di batas "
                        f"({kecepatan_kendaraan:.0f} km/jam). "
                        f"Pertahankan{_info_jarak(jarak_meter)}."
                    )
                else:
                    pesan = (
                        f"✅ Zona batas {batas_kec} km/jam. "
                        f"Kecepatan Anda: {kecepatan_kendaraan:.0f} km/jam "
                        f"(toleransi {sisa:.0f} km/jam"
                        f"{_info_jarak(jarak_meter)})."
                    )

    # ── Bangun dan kembalikan objek hasil ────────────────────────────────────
    return EvaluasiHasil(
        nama_kelas        = nama_kelas,
        status            = status,
        pesan             = pesan,
        play_audio        = play_audio,
        jarak_meter       = jarak_meter,
        kategori          = kategori,
        warna_css         = WARNA_STATUS.get(status, "notif-ok"),
        ikon              = IKON_STATUS.get(status, "ℹ️"),
        batas_kecepatan   = batas_kec,
        selisih_kecepatan = selisih,
    )


# ==============================================================
# 4. EVALUASI BATCH + PRIORITAS (tidak berubah dari v1)
# ==============================================================

def evaluasi_batch(
    deteksi_list        : list[dict],
    frame_height        : Optional[float] = None,
    kecepatan_kendaraan : float           = 0.0,
) -> list[EvaluasiHasil]:
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
        bbox       = det.get("bbox", [])
        bbox_height = abs(bbox[3] - bbox[1]) if len(bbox) == 4 else None
        hasil_list.append(evaluasi_deteksi(
            nama_kelas          = nama_kelas,
            bbox_height         = bbox_height,
            frame_height        = frame_height,
            kecepatan_kendaraan = kecepatan_kendaraan,
        ))
    hasil_list.sort(key=lambda h: URUTAN_PRIORITAS.get(h.status, 99))
    return hasil_list


def ambil_prioritas_tertinggi(
    deteksi_list        : list[dict],
    frame_height        : Optional[float] = None,
    kecepatan_kendaraan : float           = 0.0,
) -> Optional[EvaluasiHasil]:
    hasil = evaluasi_batch(deteksi_list, frame_height, kecepatan_kendaraan)
    return hasil[0] if hasil else None


# ==============================================================
# 5. BLOK PENGUJIAN MANDIRI  [v2 — diperbarui sesuai logika baru]
# Jalankan: python Logic/core_logic.py
# ==============================================================

if __name__ == "__main__":

    SEP  = "=" * 75
    SEP2 = "-" * 75

    print(SEP)
    print("  SMART ADAS — Pengujian Mandiri core_logic.py  [v2]")
    print("  Kelompok 6 | Proyek Tugas Akhir")
    print(SEP)

    # ==========================================================
    # TEST 1: Estimasi Jarak (tidak berubah)
    # ==========================================================
    print("\n📐 TEST 1 — estimasi_jarak()")
    print(SEP2)
    for bh, fh, desc in [
        (200, 1080, "Dekat ~4 m"),
        (80,   720, "Sedang ~10 m"),
        (30,   720, "Jauh ~27 m"),
        (0,    720, "bbox nol → None"),
        (None, 720, "bbox None → None"),
    ]:
        r = estimasi_jarak(bh, fh)
        print(f"  bbox={str(bh):>5} px → {str(r)+' m' if r else 'None':>10s}  | {desc}")

    # ==========================================================
    # TEST 2: INFO — selalu silent
    # ==========================================================
    print(f"\n🟢 TEST 2 — INFO (selalu silent, kecepatan apapun)")
    print(SEP2)
    for kelas in ["Masjid", "Pom Bensin", "Tempat Parkir", "Jembatan"]:
        h = evaluasi_deteksi(kelas, bbox_height=60, frame_height=720, kecepatan_kendaraan=80)
        tanda = "✅" if not h.play_audio and h.status == "Info" else "❌"
        print(f"  {tanda} {kelas:<35s} | status={h.status:<12s} | audio={h.play_audio}")

    # ==========================================================
    # TEST 3: BAHAYA — konteks kecepatan_aman_kmh
    # ==========================================================
    print(f"\n🟡 TEST 3 — BAHAYA (Context-Aware berdasarkan kecepatan_aman_kmh)")
    print(SEP2)

    skenario_bahaya = [
        # (kelas,                    kecepatan, ekspektasi)
        ("Banyak Anak-Anak",         20,  "Info    ← ≤30, diam/pelan"),
        ("Banyak Anak-Anak",         30,  "Info    ← tepat di batas aman"),
        ("Banyak Anak-Anak",         60,  "Peringatan ← >30, alarm!"),
        ("Polisi Tidur",             15,  "Info    ← ≤20, aman"),
        ("Polisi Tidur",             45,  "Peringatan ← >20, terlalu cepat!"),
        ("Tikungan Ke Kanan",        40,  "Info    ← tepat di batas"),
        ("Tikungan Ke Kanan",        80,  "Peringatan ← >40, terlalu cepat!"),
        ("Penyebrangan Pejalan Kaki",10,  "Info    ← ≤20, sudah pelan"),
        ("Penyebrangan Pejalan Kaki",50,  "Peringatan ← >20, alarm!"),
        ("Peringatan Perlintasan Kereta Api", 25, "Info  ← ≤30"),
        ("Peringatan Perlintasan Kereta Api", 60, "Peringatan ← >30, alarm!"),
        ("Hati-Hati",                50,  "Info    ← tepat di batas 50"),
        ("Hati-Hati",                90,  "Peringatan ← >50, alarm!"),
    ]

    for kelas, kec, ekspektasi in skenario_bahaya:
        h = evaluasi_deteksi(kelas, bbox_height=80, frame_height=720,
                             kecepatan_kendaraan=kec)
        audio = "🔊" if h.play_audio else "🔇"
        tanda = "✅" if ekspektasi.startswith(h.status.split()[0]) else "❌"
        print(f"  {tanda} {kelas:<42s} {kec:>4} km/h → {h.status:<12s} {audio}  | {ekspektasi}")

    # ==========================================================
    # TEST 4: LARANGAN — konteks jenis_larangan
    # ==========================================================
    print(f"\n🔴 TEST 4 — LARANGAN (Context-Aware berdasarkan jenis_larangan)")
    print(SEP2)

    skenario_larangan = [
        # (kelas,             kecepatan, ekspektasi_status, catatan)
        # ── parkir_berhenti ──────────────────────────────────────────────────
        ("Dilarang Parkir",   0,  "Pelanggaran", "diam = parkir terlarang!"),
        ("Dilarang Parkir",  40,  "Info",         "melaju = tidak relevan"),
        ("Dilarang Berhenti", 0,  "Pelanggaran", "diam = berhenti terlarang!"),
        ("Dilarang Berhenti",60,  "Info",         "melaju = tidak relevan"),
        # ── melintas ─────────────────────────────────────────────────────────
        ("Dilarang Masuk",    0,  "Info",         "diam = belum masuk"),
        ("Dilarang Masuk",   50,  "Pelanggaran", "melaju = masuk jalan terlarang!"),
        ("Dilarang Putar Balik", 0,  "Info",      "diam = belum putar"),
        ("Dilarang Putar Balik",30,  "Pelanggaran","melaju = putar di zona terlarang!"),
        ("Dilarang Mendahului", 0,  "Info",        "diam = tidak mendahului"),
        ("Dilarang Mendahului",70,  "Pelanggaran", "melaju = mendahului terlarang!"),
        ("Berhenti",           0,  "Info",         "sudah berhenti = patuh"),
        ("Berhenti",          50,  "Pelanggaran", "masih melaju = harus berhenti!"),
        ("Larangan Muatan > 10 ton", 0,  "Info",   "diam = belum melintas"),
        ("Larangan Muatan > 10 ton",40,  "Pelanggaran","melaju = muatan terlarang melintas!"),
    ]

    for kelas, kec, exp_status, catatan in skenario_larangan:
        h = evaluasi_deteksi(kelas, bbox_height=100, frame_height=720,
                             kecepatan_kendaraan=kec)
        audio = "🔊" if h.play_audio else "🔇"
        tanda = "✅" if h.status == exp_status else "❌"
        print(f"  {tanda} {kelas:<35s} {kec:>4} km/h → {h.status:<12s} {audio}  | {catatan}")

    # ==========================================================
    # TEST 5: SPEED_LIMIT (tidak berubah dari v1)
    # ==========================================================
    print(f"\n🚨 TEST 5 — SPEED_LIMIT (over-speeding)")
    print(SEP2)
    for kelas, bh, kec, ket in [
        ("Kecepatan Maks. 30 km",  90,  25, "patuh"),
        ("Kecepatan Maks. 30 km",  90,  30, "tepat batas"),
        ("Kecepatan Maks. 30 km",  90,  55, "Pelanggaran +25"),
        ("Kecepatan Maks. 80 km",  60,  95, "Pelanggaran +15"),
        ("Kecepatan Maks. 100 km", 40, 100, "tepat batas"),
        ("Kecepatan Maks.120 km",  30, 145, "Pelanggaran +25"),
    ]:
        h = evaluasi_deteksi(kelas, bbox_height=bh, frame_height=720,
                             kecepatan_kendaraan=kec)
        audio = "🔊" if h.play_audio else "🔇"
        print(f"  {kelas:<30s} {kec:>4} km/h → {h.status:<12s} {audio}  | {ket}")
        if h.selisih_kecepatan:
            print(f"    Pesan: {h.pesan}")

    # ==========================================================
    # TEST 6: Batch — skenario realistis multi-objek dalam 1 frame
    # ==========================================================
    print(f"\n\n📦 TEST 6 — evaluasi_batch() skenario realistis")
    print(SEP2)

    # Skenario: mobil 75 km/jam mendekati zona sekolah + terdeteksi rambu masuk terlarang
    deteksi_simulasi = [
        {"class_name": "Banyak Anak-Anak",   "bbox": [100, 200, 200, 280], "confidence": 0.91},
        {"class_name": "Dilarang Masuk",      "bbox": [300, 150, 420, 230], "confidence": 0.87},
        {"class_name": "Kecepatan Maks. 40 km","bbox": [500, 100, 600, 180], "confidence": 0.76},
    ]
    print("  Input: kecepatan kendaraan = 75 km/jam")
    batch = evaluasi_batch(deteksi_simulasi, frame_height=720, kecepatan_kendaraan=75)
    for i, h in enumerate(batch, 1):
        print(f"\n  [{i}] {h}")

    prior = ambil_prioritas_tertinggi(deteksi_simulasi, 720, 75)
    print(f"\n  ► Prioritas tertinggi di UI:")
    print(f"    {prior.ikon}  [{prior.status}] {prior.pesan}")

    # Skenario 2: mobil berhenti di rambu dilarang parkir
    print(f"\n{SEP2}")
    deteksi_parkir = [
        {"class_name": "Dilarang Parkir", "bbox": [200, 100, 300, 200], "confidence": 0.93},
        {"class_name": "Masjid",          "bbox": [400, 100, 500, 200], "confidence": 0.78},
    ]
    print("  Input: kecepatan kendaraan = 0 km/jam (berhenti)")
    batch2 = evaluasi_batch(deteksi_parkir, frame_height=720, kecepatan_kendaraan=0)
    for i, h in enumerate(batch2, 1):
        print(f"\n  [{i}] {h}")

    # ==========================================================
    # RINGKASAN
    # ==========================================================
    print(f"\n{SEP}")
    print("  Semua pengujian selesai.")
    print(f"  Total kelas terkonfigurasi: {len(KONFIGURASI_RAMBU)}")
    print(SEP)
